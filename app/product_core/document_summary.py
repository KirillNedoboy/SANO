"""Explicit-consent, document-only AI descriptions over the existing G2 runtime."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC
from typing import Any

from app.agent.document_summary_trust import (
    SUMMARY_ACTION,
    SUMMARY_PROMPT_VERSION,
    DocumentSummaryTrustAdapter,
    _document_input_hash,
    _select_pages,
    encode_summary_question,
)
from app.agent.g2_runtime import G2Runtime
from app.agent.providers.contract import AgentProvider
from app.product_core.errors import DocumentValidationError, SourceNotFoundError
from app.product_core.runtime import ProductCoreRuntime


def _coverage_fields(
    total_chars: int, selected: tuple[tuple[int, str], ...]
) -> dict[str, Any]:
    complete = sum(len(text) for _, text in selected) == total_chars
    return {
        "coverage_complete": complete,
        "coverage_note": None
        if complete
        else "Some extracted text was omitted by the document-processing limit.",
    }


class DocumentSummaryService:
    def __init__(
        self,
        runtime: ProductCoreRuntime,
        provider: AgentProvider,
        g2_runtime: G2Runtime,
        trust_adapter: DocumentSummaryTrustAdapter,
    ) -> None:
        self.runtime = runtime
        self.provider = provider
        self.g2_runtime = g2_runtime
        self.trust_adapter = trust_adapter

    def prepare(self, person_id: str, source_id: str, session_token: str) -> dict[str, Any]:
        source, extraction = self.runtime.documents.get(source_id)
        processing = self.runtime.documents.get_text_processing(source_id)
        if source.person_id != person_id:
            raise SourceNotFoundError("document not found")
        if processing.status != "ready" or extraction is None:
            raise DocumentValidationError("document_text_not_ready")
        pages = self.runtime.documents.list_pages(source_id, extraction.extraction_id)
        selected = _select_pages(pages)
        input_hash = _document_input_hash(selected)
        descriptor = self.provider.descriptor
        fingerprint = hashlib.sha256(
            json.dumps(
                [
                    source.id,
                    extraction.extraction_id,
                    input_hash,
                    descriptor.descriptor_hash,
                    SUMMARY_PROMPT_VERSION,
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
            assert uow.connection is not None
            active = uow.connection.execute(
                """SELECT * FROM document_summary_runs
                   WHERE source_id = ? AND request_fingerprint = ?
                     AND status IN ('consent_required', 'consented', 'executing')
                   ORDER BY attempt_number DESC LIMIT 1""",
                (source_id, fingerprint),
            ).fetchone()
            if active is not None:
                response = self._response(active)
                response["disclosure"] = self._stored_disclosure(active)
                return response
            completed = uow.connection.execute(
                """SELECT * FROM document_summary_runs WHERE source_id = ?
                   AND request_fingerprint = ? AND status IN ('completed', 'partial')
                   ORDER BY attempt_number DESC LIMIT 1""",
                (source_id, fingerprint),
            ).fetchone()
            if completed is not None:
                return self._response(completed)
        question = encode_summary_question(
            person_id=person_id,
            source_id=source_id,
            extraction_id=extraction.extraction_id,
            input_text_hash=input_hash,
        )
        prepared = self.g2_runtime.prepare(
            session_token, question, purpose_id="document_summary", action_id=SUMMARY_ACTION
        )
        run_id = str(uuid.uuid4())
        now = self.runtime.clock().astimezone(UTC).isoformat()
        fields = json.dumps([f"page:{number}" for number, _ in selected], separators=(",", ":"))
        try:
            with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
                assert uow.connection is not None
                attempt = int(
                    uow.connection.execute(
                        "SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM document_summary_runs "
                        "WHERE source_id = ? AND request_fingerprint = ?",
                        (source_id, fingerprint),
                    ).fetchone()[0]
                )
                uow.connection.execute(
                    """INSERT INTO document_summary_runs (
                         run_id, actor_id, person_id, source_id, extraction_id,
                         input_text_hash, request_fingerprint, prompt_version, status,
                         attempt_number, provider_id, provider_kind,
                         provider_descriptor_hash, model_id, external, execution_id,
                         created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'consent_required', ?, ?, ?, ?, ?,
                                  ?, ?, ?, ?)""",
                    (
                        run_id,
                        self._session_actor(session_token),
                        person_id,
                        source_id,
                        extraction.extraction_id,
                        input_hash,
                        fingerprint,
                        SUMMARY_PROMPT_VERSION,
                        attempt,
                        descriptor.provider_id,
                        descriptor.provider_kind,
                        descriptor.descriptor_hash,
                        descriptor.model_id,
                        int(descriptor.external),
                        prepared.execution_id,
                        now,
                        now,
                    ),
                )
                row = uow.connection.execute(
                    "SELECT * FROM document_summary_runs WHERE run_id = ?", (run_id,)
                ).fetchone()
                return {
                    **self._response(row),
                    "disclosure": prepared.preview,
                    "fields": json.loads(fields),
                    "covered_pages": [number for number, _ in selected],
                    "total_pages": extraction.page_count,
                    **_coverage_fields(extraction.total_chars, selected),
                }
        except sqlite3.IntegrityError:
            with self.runtime.database.uow() as uow:
                assert uow.connection is not None
                active = uow.connection.execute(
                    """SELECT * FROM document_summary_runs WHERE source_id = ?
                       AND request_fingerprint = ? AND status IN
                       ('consent_required', 'consented', 'executing') LIMIT 1""",
                    (source_id, fingerprint),
                ).fetchone()
            if active is not None:
                response = self._response(active)
                response["disclosure"] = self._stored_disclosure(active)
                return response
            raise

    @staticmethod
    def _stored_disclosure(row: Any) -> dict[str, Any]:
        return {
            "provider_id": row["provider_id"],
            "model_id": row["model_id"],
            "external": bool(row["external"]),
            "evidence_count": 1,
            "fields": ["summary", "key_points", "discussion_questions", "page_numbers"],
        }

    def consent_and_execute(
        self, person_id: str, source_id: str, run_id: str, session_token: str
    ) -> dict[str, Any]:
        with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
            assert uow.connection is not None
            row = uow.connection.execute(
                "SELECT * FROM document_summary_runs WHERE run_id = ? "
                "AND source_id = ? AND person_id = ?",
                (run_id, source_id, person_id),
            ).fetchone()
            if row is None:
                raise SourceNotFoundError("document summary not found")
            if row["status"] in {"completed", "partial"}:
                return self._response(row)
            if row["status"] != "consent_required":
                raise DocumentValidationError("document_summary_consent_required")
            question = encode_summary_question(
                person_id=person_id,
                source_id=source_id,
                extraction_id=row["extraction_id"],
                input_text_hash=row["input_text_hash"],
            )
            extraction, selected = self._snapshot_for_run(row)
            fields = [f"page:{number}" for number, _ in selected]
        # This is the explicit consent action. No provider call occurs if the
        # session/access/source/provider binding no longer passes G2 checks.
        try:
            consent = self.g2_runtime.grant_disclosure_consent(
                session_token, row["execution_id"], fields=fields, question=question
            )
        except Exception:
            self._mark_failed(run_id, "consent_revalidation_failed")
            raise
        now = self.runtime.clock().astimezone(UTC).isoformat()
        with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
            assert uow.connection is not None
            cursor = uow.connection.execute(
                """UPDATE document_summary_runs SET status = 'executing', consent_id = ?,
                   updated_at = ? WHERE run_id = ? AND status = 'consent_required'""",
                (consent.consent_id, now, run_id),
            )
            if cursor.rowcount != 1:
                raise DocumentValidationError("document_summary_already_started")
        try:
            result = self.g2_runtime.execute(session_token, row["execution_id"], question)
        except Exception:
            self._mark_failed(run_id, "summary_execution_failed")
            raise
        receipt = self.g2_runtime.get_receipt(session_token, row["execution_id"])
        completed_at = self.runtime.clock().astimezone(UTC).isoformat()
        parsed: dict[str, Any] | None = None
        if result.status == "answered" and result.answer is not None:
            parsed = dict(result.answer)
        if receipt is None:
            reason = "execution_receipt_missing"
        elif parsed is None:
            reason = result.reason_code or "summary_generation_failed"
        else:
            reason = None
        coverage = _coverage_fields(extraction.total_chars, selected)
        if parsed is not None:
            parsed = {**parsed, **coverage}
        final_status = (
            "failed"
            if parsed is None
            else "completed"
            if coverage["coverage_complete"]
            else "partial"
        )
        receipt_id = (
            receipt.get("receipt_id")
            if isinstance(receipt, dict)
            else None
            if receipt is None
            else receipt.receipt_id
        )
        with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
            assert uow.connection is not None
            uow.connection.execute(
                """UPDATE document_summary_runs SET status = ?, receipt_id = ?,
                   result_json = ?, reason_code = ?, completed_at = ?, updated_at = ?
                   WHERE run_id = ? AND status = 'executing'""",
                (
                    final_status,
                    receipt_id,
                    None
                    if parsed is None
                    else json.dumps(parsed, ensure_ascii=False, sort_keys=True),
                    reason,
                    completed_at,
                    completed_at,
                    run_id,
                ),
            )
            final = uow.connection.execute(
                "SELECT * FROM document_summary_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            return self._response(final)

    def latest(self, person_id: str, source_id: str) -> dict[str, Any] | None:
        with self.runtime.database.uow() as uow:
            assert uow.connection is not None
            row = uow.connection.execute(
                """SELECT * FROM document_summary_runs WHERE source_id = ? AND person_id = ?
                   ORDER BY attempt_number DESC, created_at DESC LIMIT 1""",
                (source_id, person_id),
            ).fetchone()
        if row is None:
            return None
        response = self._response(row)
        if row["status"] in {"consent_required", "consented", "executing"}:
            response["disclosure"] = self._stored_disclosure(row)
        return response

    def _mark_failed(self, run_id: str, reason_code: str) -> None:
        now = self.runtime.clock().astimezone(UTC).isoformat()
        with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
            assert uow.connection is not None
            uow.connection.execute(
                """UPDATE document_summary_runs SET status = 'failed', reason_code = ?,
                   completed_at = ?, updated_at = ? WHERE run_id = ?
                   AND status IN ('consent_required', 'executing')""",
                (reason_code, now, now, run_id),
            )

    def _snapshot_for_run(
        self, row: Any
    ) -> tuple[Any, tuple[tuple[int, str], ...]]:
        spec = {
            "person_id": row["person_id"],
            "source_id": row["source_id"],
            "extraction_id": row["extraction_id"],
            "input_text_hash": row["input_text_hash"],
        }
        _source, extraction, selected = self.trust_adapter.load_snapshot(spec)
        return extraction, selected

    def _selected_for_run(self, row: Any) -> tuple[tuple[int, str], ...]:
        _extraction, selected = self._snapshot_for_run(row)
        return selected

    def _session_actor(self, session_token: str) -> str:
        session = self.g2_runtime.sessions.resolve(session_token)
        if session is None:
            raise PermissionError("session_or_person_unavailable")
        return session.actor_id

    @staticmethod
    def _response(row: Any) -> dict[str, Any]:
        result = None
        if row["result_json"]:
            try:
                result = json.loads(row["result_json"])
            except (TypeError, ValueError):
                result = None
        return {
            "run_id": row["run_id"],
            "source_id": row["source_id"],
            "status": row["status"],
            "attempt_number": row["attempt_number"],
            "provider_id": row["provider_id"],
            "model_id": row["model_id"],
            "external": bool(row["external"]),
            "result": result,
            "reason_code": row["reason_code"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "consent_id": row["consent_id"],
            "receipt_id": row["receipt_id"],
        }
