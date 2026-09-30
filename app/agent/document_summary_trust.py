"""G2 trust binding for one selected, page-numbered document snapshot."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agent.g2_runtime import EnvelopeProjection
from app.agent.providers.contract import AgentProvider, ProviderExecutionRequest
from app.agent.trust_adapter import OpenCareAuthorizationAdapter
from app.agent_trust.builders import (
    BuildRefused,
    EnvelopeRequest,
    TrustAuthority,
    TrustedEnvelopeBuilder,
)
from app.agent_trust.canonical import canonical_bytes, sha256_hex
from app.agent_trust.identifiers import ACTION_REQUIREMENTS
from app.agent_trust.models import (
    AuthorizationDecision,
    EvidenceItem,
    ProviderDescriptorContract,
    SafetyDecision,
    TrustEnvelope,
)
from app.family_access.service import FamilyAccessService
from app.product_core.models import DocumentExtractionPage, Source
from app.product_core.runtime import ProductCoreRuntime

SUMMARY_PURPOSE = "document_summary"
SUMMARY_ACTION = "document.summarize"
SUMMARY_CONSENT_BASIS = "document-summary-per-source-v1"
SUMMARY_REQUEST_PREFIX = "sano-document-summary-v1:"
MAX_DOCUMENT_AI_TEXT_CHARS = 60_000
SUMMARY_PROMPT_VERSION = "sano-document-summary-v1"


class DocumentSummaryAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    summary: str = Field(min_length=1, max_length=1600)
    key_points: list[str] = Field(max_length=8)
    discussion_questions: list[str] = Field(max_length=8)
    page_numbers: list[int] = Field(min_length=1, max_length=200)
    coverage_complete: bool
    coverage_note: str | None = Field(default=None, max_length=300)


class DocumentQuestionAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    answer: str = Field(min_length=1, max_length=3000)
    page_numbers: list[int] = Field(min_length=1, max_length=200)
    unknowns: list[str] = Field(max_length=8)


def _document_input_hash(pages: Sequence[tuple[int, str]]) -> str:
    return sha256_hex(
        canonical_bytes(
            {"pages": [{"page_number": number, "text": text} for number, text in pages]}
        )
    )


def _select_pages(pages: Sequence[DocumentExtractionPage]) -> tuple[tuple[int, str], ...]:
    selected: list[tuple[int, str]] = []
    remaining = MAX_DOCUMENT_AI_TEXT_CHARS
    for page in sorted(pages, key=lambda item: item.page_number):
        if remaining <= 0:
            break
        text = page.normalized_text[:remaining]
        if text:
            selected.append((page.page_number, text))
            remaining -= len(text)
    return tuple(selected)


def encode_summary_question(
    *, person_id: str, source_id: str, extraction_id: str, input_text_hash: str
) -> str:
    value = {
        "person_id": person_id,
        "source_id": source_id,
        "extraction_id": extraction_id,
        "input_text_hash": input_text_hash,
    }
    return SUMMARY_REQUEST_PREFIX + json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def encode_document_question(
    *,
    person_id: str,
    source_id: str,
    extraction_id: str,
    input_text_hash: str,
    user_question: str,
) -> str:
    value = {
        "person_id": person_id,
        "source_id": source_id,
        "extraction_id": extraction_id,
        "input_text_hash": input_text_hash,
        "user_question": user_question,
    }
    return SUMMARY_REQUEST_PREFIX + json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _decode_summary_question(question: str) -> dict[str, str]:
    if not question.startswith(SUMMARY_REQUEST_PREFIX):
        raise BuildRefused(["document_binding_invalid"])
    try:
        spec = json.loads(question[len(SUMMARY_REQUEST_PREFIX) :])
    except (TypeError, ValueError, json.JSONDecodeError):
        raise BuildRefused(["document_binding_invalid"]) from None
    expected = {"person_id", "source_id", "extraction_id", "input_text_hash"}
    question_mode = isinstance(spec, dict) and "user_question" in spec
    if (
        not isinstance(spec, dict)
        or set(spec) != (expected | {"user_question"} if question_mode else expected)
        or any(not isinstance(spec[key], str) or not spec[key].strip() for key in expected)
        or len(spec["input_text_hash"]) != 64
        or any(char not in "0123456789abcdef" for char in spec["input_text_hash"])
    ):
        raise BuildRefused(["document_binding_invalid"])
    if question_mode and (
        not isinstance(spec["user_question"], str)
        or not spec["user_question"].strip()
        or len(spec["user_question"]) > 2000
    ):
        raise BuildRefused(["document_question_invalid"])
    return cast(dict[str, str], spec)


class _SummaryAuthority(TrustAuthority):
    def __init__(self, adapter: DocumentSummaryTrustAdapter, spec: dict[str, str]) -> None:
        self.adapter = adapter
        self.spec = spec

    def authorize(
        self,
        *,
        actor_id: str,
        credential_id: str,
        person_id: str,
        required_scopes: frozenset[str],
        authorized_at: datetime,
    ) -> AuthorizationDecision:
        return self.adapter.authorization.authorize(
            actor_id=actor_id,
            credential_id=credential_id,
            person_id=person_id,
            required_scopes=required_scopes,
            authorized_at=authorized_at,
        )

    def select_evidence(
        self,
        *,
        evidence_ids: Sequence[str],
        person_id: str,
        required_scopes: frozenset[str],
        observed_at: datetime,
    ) -> list[EvidenceItem]:
        if not {"person.read", "document.read"}.issubset(required_scopes):
            raise BuildRefused(["evidence_scope_invalid"])
        expected = self.adapter.evidence_id(self.spec)
        if list(evidence_ids) != [expected] or person_id != self.spec["person_id"]:
            raise BuildRefused(["provenance_missing"])
        _source, _snapshot, selected = self.adapter.load_snapshot(self.spec)
        actual_hash = _document_input_hash(selected)
        if actual_hash != self.spec["input_text_hash"]:
            raise BuildRefused(["context_changed"])
        return [
            EvidenceItem(
                evidence_id=expected,
                evidence_type="document_text_snapshot",
                person_id=person_id,
                resource_scope="document.read",
                content_sha256=actual_hash,
                source_ids=[self.spec["source_id"]],
                provenance_status="source_backed",
                selected_fields=[f"page:{number}" for number, _ in selected],
                observed_at=observed_at.astimezone(UTC),
            )
        ]

    def safety_decision(self, request: EnvelopeRequest, evaluated_at: datetime) -> SafetyDecision:
        del request
        return SafetyDecision(
            decision="allow",
            reason_codes=[],
            policy_version="document-summary-safety-v1",
            evaluated_at=evaluated_at,
            limitations=sorted(
                [
                    "Only one selected document's locally extracted text is available.",
                    "The description is informational and does not create health records.",
                ]
            ),
            required_notices=[
                "This description does not diagnose or recommend treatment, dosage, "
                "or medication changes."
            ],
        )

    def validate_disclosure(self, request: EnvelopeRequest) -> None:
        if request.disclosure_mode == "external_provider" and not request.provider_descriptor:
            raise BuildRefused(["provider_disclosure_denied"])


class DocumentSummaryTrustAdapter:
    def __init__(
        self,
        runtime: ProductCoreRuntime,
        family_service: FamilyAccessService,
        provider: AgentProvider,
        *,
        clock: Any = None,
    ) -> None:
        self.runtime = runtime
        self.family_service = family_service
        self.authorization = OpenCareAuthorizationAdapter(family_service)
        self.provider = provider
        self.clock = clock or runtime.clock

    def set_provider(self, provider: AgentProvider) -> None:
        self.provider = provider

    @staticmethod
    def evidence_id(spec: dict[str, str]) -> str:
        return f"document-summary:{spec['source_id']}:{spec['extraction_id']}"

    def load_snapshot(
        self, spec: dict[str, str]
    ) -> tuple[Source, Any, tuple[tuple[int, str], ...]]:
        with self.runtime.database.uow() as uow:
            source = uow.sources.get(spec["source_id"])
            extraction = uow.document_extractions.get(spec["extraction_id"])
            processing = uow.document_text_processing.get_for_source(spec["source_id"])
            if (
                source is None
                or extraction is None
                or processing is None
                or source.person_id != spec["person_id"]
                or source.source_type != "document"
                or processing.status != "ready"
                or processing.extraction_id != extraction.extraction_id
                or extraction.source_id != source.id
                or extraction.person_id != source.person_id
            ):
                raise BuildRefused(["document_binding_invalid"])
            pages = tuple(uow.document_extractions.list_pages(extraction.extraction_id))
        if (
            len(pages) != extraction.page_count
            or [page.page_number for page in pages] != list(range(1, len(pages) + 1))
            or any(
                page.source_id != source.id
                or page.person_id != source.person_id
                or page.extraction_id != extraction.extraction_id
                or hashlib.sha256(page.normalized_text.encode("utf-8")).hexdigest()
                != page.page_hash
                for page in pages
            )
        ):
            raise BuildRefused(["document_binding_invalid"])
        selected = _select_pages(pages)
        if not selected or _document_input_hash(selected) != spec["input_text_hash"]:
            raise BuildRefused(["context_changed"])
        return source, extraction, selected

    def build_envelope(self, **kwargs: Any) -> TrustEnvelope:
        spec = _decode_summary_question(str(kwargs["question"]))
        if str(kwargs["person_id"]) != spec["person_id"]:
            raise BuildRefused(["person_mismatch"])
        self.load_snapshot(spec)
        descriptor = self.provider.descriptor
        descriptor_contract = ProviderDescriptorContract(
            provider_id=descriptor.provider_id,
            model_id=descriptor.model_id,
            provider_kind=descriptor.provider_kind,
            endpoint_class=descriptor.endpoint_class,
            external=descriptor.external,
            descriptor_hash=descriptor.descriptor_hash,
        )
        question_mode = "user_question" in spec
        purpose_id = "document_question" if question_mode else SUMMARY_PURPOSE
        action_id = "document.answer_question" if question_mode else SUMMARY_ACTION
        if kwargs["purpose_id"] != purpose_id or kwargs["action_id"] != action_id:
            raise BuildRefused(["document_binding_invalid"])
        request = EnvelopeRequest(
            actor_id=str(kwargs["actor_id"]),
            credential_id=str(kwargs["credential_id"]),
            person_id=str(kwargs["person_id"]),
            purpose_id=cast(Literal["document_summary", "document_question"], purpose_id),
            action_id=cast(Literal["document.summarize", "document.answer_question"], action_id),
            requested_action=(
                "Answer one question using only this selected document."
                if question_mode
                else "Create an informational description of this one document."
            ),
            requested_tools=["source.read"],
            evidence_ids=[self.evidence_id(spec)],
            disclosure_mode="external_provider" if descriptor.external else "local_only",
            provider_id=descriptor.provider_id,
            provider_descriptor=descriptor_contract,
            consent_basis_id=SUMMARY_CONSENT_BASIS,
            ttl_seconds=300,
        )
        return TrustedEnvelopeBuilder(_SummaryAuthority(self, spec), clock=self.clock).build(
            request
        )

    def resolve_evidence(self, envelope: TrustEnvelope) -> tuple[dict[str, Any], ...]:
        if len(envelope.evidence) != 1:
            raise BuildRefused(["context_changed"])
        evidence = envelope.evidence[0]
        if len(evidence.source_ids) != 1 or not evidence.evidence_id.startswith(
            "document-summary:"
        ):
            raise BuildRefused(["context_changed"])
        source_id = evidence.source_ids[0]
        if not evidence.evidence_id.startswith(f"document-summary:{source_id}:"):
            raise BuildRefused(["context_changed"])
        extraction_id = evidence.evidence_id[len(f"document-summary:{source_id}:") :]
        spec = {
            "person_id": envelope.person_id,
            "source_id": source_id,
            "extraction_id": extraction_id,
            "input_text_hash": evidence.content_sha256,
        }
        _source, _snapshot, pages = self.load_snapshot(spec)
        return tuple({"page_number": number, "text": text} for number, text in pages)

    def provider_request_builder(
        self,
        projection: EnvelopeProjection,
        question: str,
        evidence: tuple[dict[str, Any], ...],
    ) -> ProviderExecutionRequest:
        spec = _decode_summary_question(question)
        question_mode = "user_question" in spec
        rows: list[dict[str, Any]] = []
        for item in evidence:
            if set(item) != {"page_number", "text"}:
                raise BuildRefused(["provider_projection_invalid"])
            if type(item["page_number"]) is not int or not isinstance(item["text"], str):
                raise BuildRefused(["provider_projection_invalid"])
            rows.append({"page_number": item["page_number"], "text": item["text"]})
        return ProviderExecutionRequest(
            question=(
                spec["user_question"]
                if question_mode
                else "Describe this document briefly for the person who uploaded it."
            ),
            purpose_id=projection.purpose_id,
            action_id=projection.action_id,
            requested_action=(
                "Answer using only the supplied document text and cite pages."
                if question_mode
                else "Summarize only the supplied document text and cite pages."
            ),
            evidence=tuple(rows),
            allowed_tools=tuple(projection.allowed_tools),
            allowed_fields=(
                ("answer", "page_numbers", "unknowns")
                if question_mode
                else (
                    "summary",
                    "key_points",
                    "discussion_questions",
                    "page_numbers",
                    "coverage_complete",
                    "coverage_note",
                )
            ),
            output_contract=(
                DocumentQuestionAnswer.model_json_schema()
                if question_mode
                else DocumentSummaryAnswer.model_json_schema()
            ),
            system_instructions=(
                (
                    "Answer the user's question using only the supplied document text. "
                    "Cite supplied page numbers. State when the document does not "
                    "answer the question. "
                    "Do not diagnose, recommend treatment, dosage, or medication changes."
                )
                if question_mode
                else (
                    "Write a brief plain-language description of the supplied document. "
                    "Use only its text. Do not diagnose, interpret results, recommend treatment, "
                    "or suggest medication changes. Keep uncertainty explicit. Every "
                    "page number must refer to supplied evidence. If the supplied pages "
                    "do not cover the whole "
                    "document, set coverage_complete false and say which pages are covered."
                )
            ),
            disclosure_constraints=tuple(projection.disclosure_constraints),
            prohibited_operations=tuple(projection.prohibited_operations),
        )

    @staticmethod
    def answer_validator(answer: dict[str, Any], projection: EnvelopeProjection) -> Any:
        question_mode = projection.action_id == "document.answer_question"
        try:
            if question_mode:
                parsed_question = DocumentQuestionAnswer.model_validate(answer)
                content_values = [parsed_question.answer, *parsed_question.unknowns]
                coverage_valid = True
            else:
                parsed_summary = DocumentSummaryAnswer.model_validate(answer)
                content_values = [
                    parsed_summary.summary,
                    *parsed_summary.key_points,
                    *parsed_summary.discussion_questions,
                ]
                coverage_valid = (
                    parsed_summary.coverage_complete and parsed_summary.coverage_note is None
                ) or (not parsed_summary.coverage_complete and bool(parsed_summary.coverage_note))
        except ValidationError:
            from app.agent.validation import ValidationResult

            return ValidationResult(False, "summary_invalid")
        parsed = parsed_question if question_mode else parsed_summary
        allowed_pages = {
            int(field.removeprefix("page:"))
            for evidence in projection.evidence
            for field in evidence["selected_fields"]
            if isinstance(field, str)
            and field.startswith("page:")
            and field.removeprefix("page:").isdigit()
        }
        if (
            len(set(parsed.page_numbers)) != len(parsed.page_numbers)
            or any(page not in allowed_pages for page in parsed.page_numbers)
            or not parsed.page_numbers
            or not coverage_valid
            or any(
                any(ord(char) < 32 and char not in "\n\t" for char in value)
                for value in content_values
            )
        ):
            from app.agent.validation import ValidationResult

            return ValidationResult(False, "summary_invalid")
        content = "\n".join(content_values)
        unsafe = (
            r"\byou should (take|start|stop|increase|decrease|change|switch)\b",
            r"\b(increase|decrease|adjust) (your |the )?(dose|dosage)",
            r"\bstart taking\b|\bstop taking\b|\bdiscontinue\b",
            r"\byou have (a |an )?(diagnosis|condition)",
            r"\bi recommend\b|\bthe best treatment\b",
        )
        if (
            re.search(r"(?:[A-Za-z]:\\|/(?:home|tmp|var|Users|private)/)", content)
            or re.search(r"(?:api[_ -]?key|authorization|bearer\s+[A-Za-z0-9])", content, re.I)
            or any(re.search(pattern, content, re.I) for pattern in unsafe)
        ):
            from app.agent.validation import ValidationResult

            return ValidationResult(False, "summary_safety_validation_failed")
        del projection
        from app.agent.validation import ValidationResult

        return ValidationResult(True, None)

    def project(self, projection: EnvelopeProjection, _question: str) -> dict[str, Any]:
        descriptor = self.provider.descriptor
        return {
            "provider_id": descriptor.provider_id,
            "model_id": descriptor.model_id,
            "provider_kind": descriptor.provider_kind,
            "external": descriptor.external,
            "retention": "provider_policy" if descriptor.external else "request_only",
            "evidence_count": len(projection.evidence),
            "disclosure_constraints": list(projection.disclosure_constraints),
            "fields": list(projection.allowed_fields),
        }

    def revalidate(self, pending: Any, session: Any) -> bool:
        if session.active_person_id != pending.person_id or session.actor_id != pending.actor_id:
            return False
        with self.runtime.database.uow() as uow:
            assert uow.connection is not None
            row = uow.connection.execute(
                "SELECT * FROM document_summary_runs WHERE execution_id = ?",
                (pending.execution_id,),
            ).fetchone()
            question_binding = None
            if row is None:
                question_binding = uow.connection.execute(
                    "SELECT * FROM document_question_bindings WHERE execution_id = ?",
                    (pending.execution_id,),
                ).fetchone()
        descriptor = self.provider.descriptor
        binding = row if row is not None else question_binding
        if binding is None or (
            binding["actor_id"] != session.actor_id
            or binding["person_id"] != pending.person_id
            or (
                row is not None
                and row["status"] not in {"consent_required", "consented", "executing"}
            )
            or binding["provider_id"] != descriptor.provider_id
            or binding["provider_descriptor_hash"] != descriptor.descriptor_hash
            or binding["model_id"] != descriptor.model_id
        ):
            return False
        spec = {
            "person_id": binding["person_id"],
            "source_id": binding["source_id"],
            "extraction_id": binding["extraction_id"],
            "input_text_hash": binding["input_text_hash"],
        }
        try:
            self.load_snapshot(spec)
        except BuildRefused:
            return False
        required_scopes = ACTION_REQUIREMENTS[pending.action_id][0]
        decision = self.authorization.authorize(
            actor_id=session.actor_id,
            credential_id=session.credential_id,
            person_id=pending.person_id,
            required_scopes=required_scopes,
            authorized_at=self.clock(),
        )
        return decision.decision == "allow" and decision.snapshot is not None

    def authorize_receipt(self, actor_id: str, credential_id: str, person_id: str) -> bool:
        decision = self.authorization.authorize(
            actor_id=actor_id,
            credential_id=credential_id,
            person_id=person_id,
            required_scopes=ACTION_REQUIREMENTS[SUMMARY_ACTION][0],
            authorized_at=self.clock(),
        )
        return decision.decision == "allow" and decision.snapshot is not None
