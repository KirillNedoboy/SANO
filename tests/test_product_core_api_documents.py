from __future__ import annotations

import hashlib
import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.main as main_module
from app.agent.document_summary_trust import (
    SUMMARY_PROMPT_VERSION,
    DocumentSummaryAnswer,
    DocumentSummaryTrustAdapter,
)
from app.agent.g2_runtime import EnvelopeProjection
from app.agent.providers.contract import ProviderDescriptor, ProviderExecutionResult
from app.family_access.policy import OWNER_SCOPES_V2
from app.product_core.installation_backup import InstallationBackupService
from tests.test_product_core_documents import _text_pdf


def _upload(client: TestClient, body: bytes = b"Aspirin evidence"):
    return client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=body,
        headers={
            "content-type": "text/plain; charset=utf-8",
            "x-opencare-filename": "C:\\private\\evidence.txt",
        },
    )


def _detail(client: TestClient, source_id: str) -> dict[str, object]:
    response = client.get(f"/api/product-core/v1/people/person-1/documents/{source_id}")
    assert response.status_code == 200, response.text
    return response.json()


def test_document_raw_upload_list_page_and_dedup(product_core_client: TestClient) -> None:
    created = _upload(product_core_client)
    assert created.status_code == 201, created.text
    saved_response = created.json()["document"]
    document = _detail(product_core_client, saved_response["source_id"])
    assert document["source_type"] == "document"
    assert document["original_filename"] == "evidence.txt"
    assert "relative_path" not in document
    assert "payload" not in document

    duplicate = _upload(product_core_client)
    assert duplicate.status_code == 409
    assert duplicate.json()["document"]["source_id"] == document["source_id"]

    listed = product_core_client.get("/api/product-core/v1/people/person-1/documents")
    assert listed.status_code == 200
    assert len(listed.json()["documents"]) == 1

    extraction_id = document["extraction"]["extraction_id"]
    page = product_core_client.get(
        "/api/product-core/v1/people/person-1/documents/"
        f"{document['source_id']}/extractions/{extraction_id}/pages/1"
    )
    assert page.status_code == 200

    wrong_person = product_core_client.get(
        f"/api/product-core/v1/people/person-2/documents/{document['source_id']}"
    )
    assert wrong_person.status_code == 404
    assert page.json()["normalized_text"] == "Aspirin evidence"
    downloaded = product_core_client.get(
        f"/api/product-core/v1/people/person-1/documents/{document['source_id']}/download"
    )
    assert downloaded.status_code == 200
    assert downloaded.content == b"Aspirin evidence"
    assert "attachment" in downloaded.headers["content-disposition"]


def test_document_content_type_and_body_limits_are_narrow(product_core_client: TestClient) -> None:
    unsupported = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=b"x",
        headers={"content-type": "application/octet-stream"},
    )
    assert unsupported.status_code == 415

    json_mutation = product_core_client.post(
        "/api/product-core/v1/sources/plain-text",
        content=b"not-json",
        headers={"content-type": "text/plain"},
    )
    assert json_mutation.status_code == 415
    assert json_mutation.json()["error"]["code"] == "json_content_type_required"

    oversized = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=b"",
        headers={"content-type": "text/plain", "content-length": "10485761"},
    )
    assert oversized.status_code == 413

    length_mismatch = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=b"two bytes",
        headers={"content-type": "text/plain", "content-length": "1"},
    )
    assert length_mismatch.status_code == 422

    pdf = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=_text_pdf("PDF evidence"),
        headers={"content-type": "application/pdf"},
    )
    assert pdf.status_code == 201, pdf.text


@pytest.mark.parametrize(
    ("media_type", "image_format", "filename"),
    (
        ("image/png", "PNG", "synthetic.png"),
        ("image/jpeg", "JPEG", "synthetic.jpg"),
    ),
)
def test_document_image_upload_preserves_media_type_and_original_bytes(
    product_core_client: TestClient,
    media_type: str,
    image_format: str,
    filename: str,
) -> None:
    image = Image.new("RGB", (2, 2), color="white")
    output = io.BytesIO()
    image.save(output, format=image_format)
    payload = output.getvalue()

    uploaded = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=payload,
        headers={
            "content-type": media_type,
            "x-opencare-filename": filename,
        },
    )

    assert uploaded.status_code == 201, uploaded.text
    document = uploaded.json()["document"]
    assert document["media_type"] == media_type
    assert document["size_bytes"] == len(payload)

    original = product_core_client.get(
        "/api/product-core/v1/people/person-1/documents/"
        f"{document['source_id']}/original"
    )
    assert original.status_code == 200
    assert original.headers["content-type"].split(";", 1)[0] == media_type
    assert original.content == payload


def test_document_locator_creates_candidate_with_exact_span(
    product_core_client: TestClient,
) -> None:
    uploaded = _upload(product_core_client)
    document = _detail(product_core_client, uploaded.json()["document"]["source_id"])
    selected = "Aspirin"
    locator = {
        "kind": "document_text_span",
        "source_id": document["source_id"],
        "content_hash": document["content_hash"],
        "extraction_id": document["extraction"]["extraction_id"],
        "page_number": 1,
        "start_codepoint": 0,
        "end_codepoint": len(selected),
        "selected_text_sha256": hashlib.sha256(selected.encode()).hexdigest(),
    }
    response = product_core_client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": "person-1",
            "source_id": document["source_id"],
            "display_name": "Aspirin",
            "provenance_locator": locator,
        },
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["provenance_locator"] == locator

    locator["selected_text_sha256"] = "0" * 64
    rejected = product_core_client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": "person-1",
            "source_id": document["source_id"],
            "display_name": "Aspirin",
            "provenance_locator": locator,
        },
        headers={"content-type": "application/json"},
    )
    assert rejected.status_code == 422


def test_v2_source_metadata_is_not_a_document_content_oracle(
    product_core_client: TestClient,
) -> None:
    uploaded = _upload(product_core_client)
    document = _detail(product_core_client, uploaded.json()["document"]["source_id"])
    runtime = main_module.app.state.product_core_runtime
    with runtime.database.uow(begin_mode="IMMEDIATE") as uow:
        assert uow.connection is not None
        uow.connection.execute(
            """
            UPDATE person_access_assignments
            SET scopes_json = ?, scope_generation = 'family-access-v2'
            WHERE person_id = 'person-1' AND is_active = 1
            """,
            (json.dumps(sorted(OWNER_SCOPES_V2), separators=(",", ":")),),
        )

    metadata = product_core_client.get(f"/api/product-core/v1/sources/{document['source_id']}")
    assert metadata.status_code == 200
    denied_page = product_core_client.get(
        "/api/product-core/v1/people/person-1/documents/"
        f"{document['source_id']}/extractions/not-real/pages/1"
    )
    assert denied_page.status_code == 403

    denied_candidate = product_core_client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": "person-1",
            "source_id": document["source_id"],
            "display_name": "Aspirin",
            "provenance_locator": {"kind": "deliberately-invalid"},
        },
        headers={"content-type": "application/json"},
    )
    assert denied_candidate.status_code == 403


def test_document_backed_review_is_denied_after_v3_scope_loss(
    product_core_client: TestClient,
) -> None:
    document = _upload(product_core_client).json()["document"]
    document = _detail(product_core_client, document["source_id"])
    selected = "Aspirin"
    candidate = product_core_client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": "person-1",
            "source_id": document["source_id"],
            "display_name": selected,
            "provenance_locator": {
                "kind": "document_text_span",
                "source_id": document["source_id"],
                "content_hash": document["content_hash"],
                "extraction_id": document["extraction"]["extraction_id"],
                "page_number": 1,
                "start_codepoint": 0,
                "end_codepoint": len(selected),
                "selected_text_sha256": hashlib.sha256(selected.encode()).hexdigest(),
            },
        },
        headers={"content-type": "application/json"},
    )
    assert candidate.status_code == 201
    runtime = main_module.app.state.product_core_runtime
    with runtime.database.uow(begin_mode="IMMEDIATE") as uow:
        assert uow.connection is not None
        uow.connection.execute(
            """
            UPDATE person_access_assignments
            SET scopes_json = ?, scope_generation = 'family-access-v2'
            WHERE person_id = 'person-1' AND is_active = 1
            """,
            (json.dumps(sorted(OWNER_SCOPES_V2), separators=(",", ":")),),
        )

    candidate_id = candidate.json()["id"]
    for action in ("confirm", "reject", "unsupported"):
        response = product_core_client.post(
            f"/api/product-core/v1/candidates/{candidate_id}/{action}",
            json={},
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 403


def test_summary_requires_explicit_consent_and_reuses_completed_result(
    product_core_client: TestClient, monkeypatch
) -> None:
    class SummaryProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            assert request.purpose_id == "document_summary"
            assert request.action_id == "document.summarize"
            assert "only the supplied page list" in request.system_instructions
            assert "coverage_complete" not in request.system_instructions
            assert "coverage_note" not in request.system_instructions
            assert request.allowed_fields == (
                "summary",
                "key_points",
                "discussion_questions",
                "page_numbers",
            )
            assert len(request.evidence) == 1
            assert set(request.evidence[0]) == {"page_number", "text"}
            return ProviderExecutionResult(
                answer={
                    "summary": "A synthetic laboratory report.",
                    "key_points": ["It contains a sample measurement."],
                    "discussion_questions": ["Would you like to ask your clinician about it?"],
                    "page_numbers": [1],
                },
                provider_id=self.descriptor.provider_id,
                model_id=self.descriptor.model_id,
                tool_calls=(),
                failure=None,
            )

    provider = SummaryProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client, b"Synthetic lab result: 140")
    assert upload.status_code == 201
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text
    root = "/api/product-core/v1/people/person-1/documents/" + source_id + "/summary"

    prepared = product_core_client.post(root + "/prepare", json={})
    assert prepared.status_code == 200, prepared.text
    consent = prepared.json()
    assert consent["status"] == "consent_required"
    assert consent["disclosure"]["external"] is True
    assert consent["covered_pages"] == [1]
    assert provider.calls == 0

    restored = product_core_client.get(root)
    assert restored.status_code == 200
    assert restored.json()["status"] == "consent_required"
    assert restored.json()["disclosure"]["provider_id"] == "synthetic.external"
    assert provider.calls == 0

    completed = product_core_client.post(root + f"/runs/{consent['run_id']}/consent", json={})
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["status"] == "completed"
    assert result["receipt_id"]
    assert result["consent_id"]
    assert result["result"]["page_numbers"] == [1]
    assert result["result"]["coverage_complete"] is True
    assert result["result"]["coverage_note"] is None
    assert provider.calls == 1

    repeated = product_core_client.post(root + "/prepare", json={})
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "completed"
    assert provider.calls == 1


def test_summary_coverage_is_server_owned_for_bounded_input(
    product_core_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.agent.document_summary_trust.MAX_DOCUMENT_AI_TEXT_CHARS", 10)

    class SummaryProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            assert request.allowed_fields == (
                "summary",
                "key_points",
                "discussion_questions",
                "page_numbers",
            )
            return ProviderExecutionResult(
                answer={
                    "summary": "A bounded synthetic report.",
                    "key_points": [],
                    "discussion_questions": [],
                    "page_numbers": [1],
                },
                provider_id=self.descriptor.provider_id,
                model_id=self.descriptor.model_id,
                tool_calls=(),
                failure=None,
            )

    provider = SummaryProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client, b"0123456789abcdef")
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text
    root = f"/api/product-core/v1/people/person-1/documents/{source_id}/summary"

    prepared = product_core_client.post(root + "/prepare", json={})
    assert prepared.status_code == 200, prepared.text
    prepared_payload = prepared.json()
    assert prepared_payload["coverage_complete"] is False
    assert prepared_payload["coverage_note"]
    assert prepared_payload["covered_pages"] == [1]
    completed = product_core_client.post(
        root + f"/runs/{prepared_payload['run_id']}/consent", json={}
    )
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["status"] == "partial"
    assert result["result"]["coverage_complete"] is False
    assert result["result"]["coverage_note"]
    assert result["result"]["page_numbers"] == [1]
    assert provider.calls == 1


def test_summary_contract_excludes_provider_coverage_metadata() -> None:
    properties = DocumentSummaryAnswer.model_json_schema()["properties"]
    assert set(properties) == {
        "summary",
        "key_points",
        "discussion_questions",
        "page_numbers",
    }
    assert SUMMARY_PROMPT_VERSION == "sano-document-summary-v3"

    valid = DocumentSummaryTrustAdapter.answer_validator(
        {
            "summary": "A source-backed description.",
            "key_points": [],
            "discussion_questions": [],
            "page_numbers": [1],
        },
        _document_projection("document.summarize"),
    )
    assert valid.valid is True

    provider_owned = DocumentSummaryTrustAdapter.answer_validator(
        {
            "summary": "A source-backed description.",
            "key_points": [],
            "discussion_questions": [],
            "page_numbers": [1],
            "coverage_complete": True,
            "coverage_note": None,
        },
        _document_projection("document.summarize"),
    )
    assert provider_owned.valid is False
    assert provider_owned.diagnostic.value == "schema_validation_failed"
    assert provider_owned.diagnostic_error_type == "extra_forbidden"


def test_document_question_uses_only_selected_document_and_requires_consent(
    product_core_client: TestClient, monkeypatch, tmp_path
) -> None:
    class QuestionProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            assert request.purpose_id == "document_question"
            assert request.action_id == "document.answer_question"
            assert request.question == "What does this report say?"
            assert len(request.evidence) == 1
            assert set(request.evidence[0]) == {"page_number", "text"}
            return ProviderExecutionResult(
                answer={
                    "answer": "It reports one sample result.",
                    "page_numbers": [1],
                    "unknowns": [],
                },
                provider_id=self.descriptor.provider_id,
                model_id=self.descriptor.model_id,
                tool_calls=(),
                failure=None,
            )

    provider = QuestionProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client, b"Synthetic lab result: 140")
    assert upload.status_code == 201
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text
    root = f"/api/product-core/v1/people/person-1/documents/{source_id}/questions"
    payload = {"question": "What does this report say?"}
    prepared = product_core_client.post(root + "/prepare", json=payload)
    assert prepared.status_code == 200, prepared.text
    data = prepared.json()
    assert data["status"] == "prepared"
    assert data["preview"]["fields"]
    assert provider.calls == 0
    consent = product_core_client.post(
        root + f"/{data['execution_id']}/consent",
        json={**payload, "fields": data["preview"]["fields"]},
    )
    assert consent.status_code == 200, consent.text
    answered = product_core_client.post(root + f"/{data['execution_id']}/execute", json=payload)
    assert answered.status_code == 200, answered.text
    result = answered.json()
    assert result["answer"]["answer"] == "It reports one sample result."
    assert result["answer"]["citations"] == [{"source_id": source_id, "claim": "Page 1"}]
    assert result["receipt_id"]
    assert provider.calls == 1
    runtime = main_module.app.state.product_core_runtime
    backup = InstallationBackupService(
        runtime.database.path, runtime.sources.store.source_dir
    ).backup(tmp_path / "synthetic-backup")
    assert backup.valid is True


def test_document_question_refuses_russian_prescriptive_request_before_provider_call(
    product_core_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class CountingProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            raise AssertionError(f"provider must not be called: {request}")

    provider = CountingProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client)
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text

    response = product_core_client.post(
        f"/api/product-core/v1/people/person-1/documents/{source_id}/questions/prepare",
        json={"question": "Какое лечение мне начать?"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "refused"
    assert response.json()["reason_code"] == "clinical_or_genetics_request"
    assert provider.calls == 0


def test_document_question_refuses_english_dose_change_before_provider_call(
    product_core_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class CountingProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            raise AssertionError(f"provider must not be called: {request}")

    provider = CountingProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client)
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text

    response = product_core_client.post(
        f"/api/product-core/v1/people/person-1/documents/{source_id}/questions/prepare",
        json={"question": "What dose of this medication should I increase?"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "refused"
    assert response.json()["reason_code"] == "clinical_or_genetics_request"
    assert provider.calls == 0


def test_document_question_rejects_unsafe_russian_provider_output_without_exposing_it(
    product_core_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnsafeQuestionProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            return ProviderExecutionResult(
                answer={
                    "answer": "Вам следует увеличить дозу препарата.",
                    "page_numbers": [1],
                    "unknowns": [],
                },
                provider_id=self.descriptor.provider_id,
                model_id=self.descriptor.model_id,
                tool_calls=(),
                failure=None,
            )

    provider = UnsafeQuestionProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client)
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text
    root = f"/api/product-core/v1/people/person-1/documents/{source_id}/questions"
    payload = {"question": "Что указано в документе?"}

    prepared = product_core_client.post(root + "/prepare", json=payload)
    assert prepared.status_code == 200, prepared.text
    consent = product_core_client.post(
        root + f"/{prepared.json()['execution_id']}/consent",
        json={"question": payload["question"], "fields": prepared.json()["preview"]["fields"]},
    )
    assert consent.status_code == 200, consent.text
    answered = product_core_client.post(
        root + f"/{prepared.json()['execution_id']}/execute", json=payload
    )

    assert answered.status_code == 200, answered.text
    assert answered.json()["status"] == "refused"
    assert answered.json()["reason_code"] == "summary_safety_validation_failed"
    assert answered.json()["answer"]["answer"] == ""
    assert "Вам следует увеличить дозу препарата." not in answered.text
    receipt = product_core_client.get(
        root + f"/{prepared.json()['execution_id']}/receipt"
    )
    assert receipt.status_code == 200, receipt.text
    assert "Вам следует увеличить дозу препарата." not in receipt.text
    assert provider.calls == 1


def test_document_summary_rejects_unsafe_russian_output_without_persisting_result(
    product_core_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class UnsafeSummaryProvider:
        calls = 0
        descriptor = ProviderDescriptor(
            provider_id="synthetic.external",
            provider_kind="external_http",
            provider_mode="external_provider",
            endpoint_class="non_loopback",
            external=True,
            model_id="synthetic-model",
        )

        def execute(self, request):
            self.calls += 1
            return ProviderExecutionResult(
                answer={
                    "summary": "Вам следует увеличить дозу препарата.",
                    "key_points": [],
                    "discussion_questions": [],
                    "page_numbers": [1],
                },
                provider_id=self.descriptor.provider_id,
                model_id=self.descriptor.model_id,
                tool_calls=(),
                failure=None,
            )

    provider = UnsafeSummaryProvider()
    monkeypatch.setattr(main_module.app.state, "agent_provider", provider)
    upload = _upload(product_core_client)
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    active = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert active.status_code == 204, active.text
    root = f"/api/product-core/v1/people/person-1/documents/{source_id}/summary"

    prepared = product_core_client.post(root + "/prepare", json={})
    assert prepared.status_code == 200, prepared.text
    with caplog.at_level("WARNING", logger="opencare.agent.document_summary"):
        completed = product_core_client.post(
            root + f"/runs/{prepared.json()['run_id']}/consent", json={}
        )

    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "failed"
    assert completed.json()["result"] is None
    assert completed.json()["reason_code"] == "summary_safety_validation_failed"
    assert "Вам следует увеличить дозу препарата." not in completed.text
    latest = product_core_client.get(root)
    assert latest.status_code == 200, latest.text
    assert latest.json()["status"] == "failed"
    assert latest.json()["result"] is None
    assert "Вам следует увеличить дозу препарата." not in latest.text
    assert provider.calls == 1
    runtime = main_module.app.state.product_core_runtime
    with runtime.database.uow() as uow:
        assert uow.connection is not None
        execution_id = str(
            uow.connection.execute(
                "SELECT execution_id FROM document_summary_runs WHERE run_id = ?",
                (prepared.json()["run_id"],),
            ).fetchone()["execution_id"]
        )
    assert execution_id in caplog.text
    assert "summary_safety_validation_failed" in caplog.text
    assert "Вам следует увеличить дозу препарата." not in caplog.text
    assert "evidence.txt" not in caplog.text
    assert "api_key" not in caplog.text


def _document_projection(
    action_id: str, *, selected_fields: tuple[str, ...] = ("page:1",)
) -> EnvelopeProjection:
    return EnvelopeProjection(
        envelope_id="envelope-1",
        person_id="person-1",
        purpose_id=(
            "document_question"
            if action_id == "document.answer_question"
            else "document_summary"
        ),
        action_id=action_id,
        requested_action="document-only synthetic request",
        evidence=(
            {
                "evidence_id": "document-summary:source-1:extraction-1",
                "content_sha256": "a" * 64,
                "selected_fields": selected_fields,
                "source_ids": ("source-1",),
            },
        ),
        allowed_tools=(),
        allowed_fields=(),
        disclosure_constraints=(),
        prohibited_operations=(),
    )


def _summary_answer(**overrides: object) -> dict[str, object]:
    answer: dict[str, object] = {
        "summary": "A source-backed description.",
        "key_points": [],
        "discussion_questions": [],
        "page_numbers": [1],
    }
    answer.update(overrides)
    return answer


@pytest.mark.parametrize(
    ("answer", "selected_fields", "diagnostic"),
    [
        (
            {"summary": "missing required fields"},
            ("page:1",),
            "schema_validation_failed",
        ),
        (
            _summary_answer(),
            (),
            "page_numbers_missing",
        ),
        (
            _summary_answer(page_numbers=[1, 1]),
            ("page:1",),
            "page_numbers_duplicate",
        ),
        (
            _summary_answer(page_numbers=[2]),
            ("page:1",),
            "page_out_of_scope",
        ),
        (
            _summary_answer(coverage_complete=True, coverage_note="pages 1-2"),
            ("page:1",),
            "schema_validation_failed",
        ),
        (
            _summary_answer(summary="safe\x01text"),
            ("page:1",),
            "control_character",
        ),
    ],
)
def test_document_validator_exposes_safe_internal_diagnostic_for_structural_failures(
    answer: dict[str, object],
    selected_fields: tuple[str, ...],
    diagnostic: str,
) -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        answer,
        _document_projection("document.summarize", selected_fields=selected_fields),
    )

    assert result.valid is False
    assert result.reason_code == "summary_invalid"
    assert result.diagnostic.value == diagnostic
    assert result.internal_diagnostic.value == diagnostic


def test_document_validator_schema_diagnostic_keeps_only_safe_metadata() -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        {"summary": "missing required fields"},
        _document_projection("document.summarize"),
    )

    assert result.diagnostic.value == "schema_validation_failed"
    assert result.diagnostic_field == "key_points"
    assert result.diagnostic_error_type == "missing"


def test_document_validator_classifies_empty_page_numbers_before_schema_validation() -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        _summary_answer(page_numbers=[]),
        _document_projection("document.summarize"),
    )

    assert result.valid is False
    assert result.reason_code == "summary_invalid"
    assert result.diagnostic.value == "page_numbers_missing"


def test_document_validator_keeps_page_allowlist_for_question_answers() -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        {
            "answer": "The source reports one result.",
            "page_numbers": [2],
            "unknowns": [],
        },
        _document_projection("document.answer_question"),
    )

    assert result.valid is False
    assert result.reason_code == "summary_invalid"
    assert result.diagnostic.value == "page_out_of_scope"


@pytest.mark.parametrize(
    ("action_id", "answer"),
    [
        (
            "document.answer_question",
            {
                "answer": "У вас диабет, вам следует увеличить дозу препарата.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "У вас диагноз: гипертония.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "У вас диабет.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Вы больны диабетом.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Результаты указывают на гипертонию.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Вам нужно начать принимать препарат.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Прекратите принимать препарат.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Замените препарат на другой.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Увеличьте дозу препарата.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "Я рекомендую увеличить дозировку препарата.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В выписке указано принимать X 10 мг, а у вас диабет.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В документе указан диагноз: диабет, и у вас диабет.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В документе указан диагноз: диабет и у вас диабет.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.summarize",
            {
                "summary": "Вам следует увеличить дозу препарата.",
                "key_points": [],
                "discussion_questions": [],
                "page_numbers": [1],
            },
        ),
        (
            "document.summarize",
            {
                "summary": (
                    "В документе указан диагноз: диабет. "
                    "Вам следует увеличить дозу препарата."
                ),
                "key_points": [],
                "discussion_questions": [],
                "page_numbers": [1],
            },
        ),
    ],
)
def test_document_validator_rejects_russian_unsafe_answers_and_summaries(
    action_id: str, answer: dict[str, object]
) -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        answer, _document_projection(action_id)
    )

    assert result.valid is False
    assert result.reason_code == "summary_safety_validation_failed"


@pytest.mark.parametrize(
    ("action_id", "answer"),
    [
        (
            "document.answer_question",
            {
                "answer": "В документе указан диагноз: сахарный диабет 2 типа.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В документе указано: у вас диабет.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В документе написано, что вы больны диабетом.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.summarize",
            {
                "summary": "В выписке указан диагноз: сахарный диабет 2 типа.",
                "key_points": [],
                "discussion_questions": [],
                "page_numbers": [1],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В документе указано, что пациент принимал препарат в дозировке 10 мг.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.answer_question",
            {
                "answer": "В выписке указано принимать X 10 мг.",
                "page_numbers": [1],
                "unknowns": [],
            },
        ),
        (
            "document.summarize",
            {
                "summary": "В выписке указан препарат в дозировке 10 мг.",
                "key_points": [],
                "discussion_questions": [],
                "page_numbers": [1],
            },
        ),
    ],
)
def test_document_validator_allows_explicitly_source_attributed_russian_reporting(
    action_id: str, answer: dict[str, object]
) -> None:
    result = DocumentSummaryTrustAdapter.answer_validator(
        answer, _document_projection(action_id)
    )

    assert result.valid is True
