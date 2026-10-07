from __future__ import annotations

import io
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

import app.main as main_module
from app.agent.provider import HttpResponse
from app.agent.providers.openrouter import OpenRouterProvider, OpenRouterProviderConfig
from app.config import Settings, clear_settings_cache
from app.family_access.policy import V2_POLICY_VERSION, build_scopes
from app.family_access.runtime import FamilyAccessRuntime, create_family_access_runtime
from app.product_core.runtime import ProductCoreRuntime, create_product_core_runtime
from tests.product_core_api_support import FixedClock, SequenceIds


def _text_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    stream = DecodedStreamObject()
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 20 250 Td ({escaped}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def registered_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, list[bytes]]]:
    monkeypatch.setenv("OPENCARE_PRODUCT_DB_PATH", str(tmp_path / "product" / "db.sqlite3"))
    monkeypatch.setenv("OPENCARE_SOURCE_DIR", str(tmp_path / "product" / "sources"))
    monkeypatch.setenv("OPENCARE_SESSION_DB_PATH", str(tmp_path / "runtime" / "sessions.sqlite3"))
    monkeypatch.setenv("OPENCARE_ENV", "development")
    monkeypatch.setenv("OPENCARE_DEMO_MODE", "true")
    monkeypatch.setenv("OPENCARE_PUBLIC_REGISTRATION", "true")
    monkeypatch.setenv("OPENCARE_AGENT_MODE", "openrouter")
    monkeypatch.setenv("OPENCARE_AGENT_ALLOW_EXTERNAL_LLM", "true")
    monkeypatch.setenv("OPENCARE_OPENROUTER_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("OPENCARE_OPENROUTER_MODEL", "synthetic/test-model")
    clear_settings_cache()
    clock = FixedClock(datetime(2026, 10, 7, 12, tzinfo=UTC))
    product_ids = SequenceIds()
    family_ids = SequenceIds()

    def runtime_factory(settings: Settings) -> ProductCoreRuntime:
        return create_product_core_runtime(settings, clock=clock, id_factory=product_ids)

    def family_runtime_factory(
        settings: Settings, runtime: ProductCoreRuntime
    ) -> FamilyAccessRuntime:
        return create_family_access_runtime(
            settings,
            runtime.database,
            clock=clock,
            id_factory=lambda: f"family-{family_ids()}",
        )

    calls: list[bytes] = []

    def fake_post(
        _endpoint: str,
        body: bytes,
        _headers: dict[str, str],
        _timeout: float,
        _max_response_bytes: int,
    ) -> HttpResponse:
        calls.append(body)
        request = json.loads(body.decode("utf-8"))
        user_payload = json.loads(request["messages"][1]["content"])
        action_id = user_payload["action_id"]
        if action_id == "document.answer_question":
            answer = {"answer": "Synthetic document answer.", "page_numbers": [1], "unknowns": []}
        else:
            citations = [
                {"source_id": source_id, "claim": "Synthetic confirmed record"}
                for evidence in user_payload.get("evidence", [])
                for source_id in evidence.get("source_ids", [])
            ]
            answer = {
                "answer": "Synthetic confirmed record answer.",
                "citations": citations,
                "unknowns": [],
                "doctor_questions": [],
                "boundary_notices": [],
            }
        return HttpResponse(
            status_code=200,
            body=json.dumps(
                {
                    "model": "synthetic/test-model",
                    "choices": [{"message": {"content": json.dumps(answer)}}],
                }
            ).encode("utf-8"),
        )

    provider = OpenRouterProvider(
        OpenRouterProviderConfig(api_key="synthetic-test-key", model="synthetic/test-model"),
        post=fake_post,
    )
    monkeypatch.setattr(main_module, "_build_agent_provider", lambda _settings: provider)
    main_module.app.state.product_core_runtime_factory = runtime_factory
    main_module.app.state.family_access_runtime_factory = family_runtime_factory
    try:
        with TestClient(main_module.app) as client:
            bootstrap = client.post(
                "/api/family-access/v1/bootstrap",
                headers={"origin": "http://testserver"},
                json={
                    "username": "synthetic-operator",
                    "display_name": "Synthetic operator",
                    "password": "synthetic operator password",
                    "person_ids": [],
                    "confirm_full_owner_access": False,
                },
            )
            assert bootstrap.status_code == 201, bootstrap.text
            client.cookies.clear()
            registered = client.post(
                "/api/family-access/v1/register",
                headers={"origin": "http://testserver"},
                json={
                    "username": "synthetic-owner",
                    "display_name": "Synthetic owner",
                    "password": "synthetic owner password",
                },
            )
            assert registered.status_code == 201, registered.text
            csrf = client.cookies.get("opencare_csrf")
            assert csrf is not None
            client.headers.update({"origin": "http://testserver", "x-opencare-csrf": csrf})
            yield client, calls
    finally:
        if hasattr(main_module.app.state, "product_core_runtime_factory"):
            del main_module.app.state.product_core_runtime_factory
        if hasattr(main_module.app.state, "family_access_runtime_factory"):
            del main_module.app.state.family_access_runtime_factory
        clear_settings_cache()


def test_empty_record_chat_refuses_without_creating_execution(
    product_core_client: TestClient,
) -> None:
    selected = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert selected.status_code == 204, selected.text

    prepared = product_core_client.post(
        "/api/chat/prepare", json={"question": "What is recorded?"}
    )

    assert prepared.status_code == 200
    assert prepared.json()["status"] == "refused"
    assert prepared.json()["reason_code"] == "record_context_empty"


def test_registered_owner_empty_record_chat_is_informational_and_does_not_call_provider(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, calls = registered_client
    me = client.get("/api/family-access/v1/me").json()
    person_id = me["active_person_id"]
    session_token = client.cookies.get("opencare_session")
    assert session_token is not None
    family_runtime = main_module.app.state.family_access_runtime
    session = family_runtime.sessions.resolve(session_token)
    assert session is not None
    prepared = client.post("/api/chat/prepare", json={"question": "What is recorded?"})
    assert prepared.status_code == 200, prepared.text
    payload = prepared.json()
    assert payload["status"] == "refused"
    assert payload["reason_code"] == "record_context_empty"
    assert payload["actions"] == [{"code": "select_document", "label": "Select a document"}]
    assert "confirmed" in payload["answer"]
    assert calls == []
    with family_runtime.sessions._connect() as connection:
        pending_count = connection.execute(
            "SELECT COUNT(*) FROM pending_executions WHERE session_id = ?",
            (session.session_id,),
        ).fetchone()[0]
    with main_module.app.state.product_core_runtime.database.connect() as connection:
        receipt_count = connection.execute(
            "SELECT COUNT(*) FROM agent_execution_receipts WHERE person_id = ?",
            (person_id,),
        ).fetchone()[0]
    assert pending_count == 0
    assert receipt_count == 0


def test_registered_owner_can_ask_one_selected_document_with_explicit_consent(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, calls = registered_client
    person_id = client.get("/api/family-access/v1/me").json()["active_person_id"]
    assert person_id
    upload = client.post(
        f"/api/product-core/v1/people/{person_id}/documents",
        content=_text_pdf("Synthetic lab result: 140."),
        headers={"content-type": "application/pdf", "x-opencare-filename": "synthetic.pdf"},
    )
    assert upload.status_code == 201, upload.text
    document = upload.json()["document"]
    source_id = document["source_id"]
    assert document["text_processing"]["status"] in {"pending", "ready"}
    main_module.app.state.product_core_runtime.documents.process_text(source_id)
    document = client.get(
        f"/api/product-core/v1/people/{person_id}/documents/{source_id}"
    ).json()
    assert document["text_processing"]["status"] == "ready"
    assert calls == []

    page = client.get(f"/chat?source_id={source_id}")
    assert page.status_code == 200
    assert f'data-chat-document-source="{source_id}"' in page.text

    root = f"/api/product-core/v1/people/{person_id}/documents/{source_id}/questions"
    question = {"question": "What does this report say?"}
    prepared = client.post(f"{root}/prepare", json=question)
    assert prepared.status_code == 200, prepared.text
    prepared_payload = prepared.json()
    assert prepared_payload["status"] == "prepared"
    assert calls == []

    consent = client.post(
        f"{root}/{prepared_payload['execution_id']}/consent",
        json={"question": question["question"], "fields": prepared_payload["preview"]["fields"]},
    )
    assert consent.status_code == 200, consent.text
    answered = client.post(
        f"{root}/{prepared_payload['execution_id']}/execute", json=question
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["answer"]["citations"] == [{"source_id": source_id, "claim": "Page 1"}]
    assert answered.json()["receipt_id"].startswith("sha256:")
    assert len(calls) == 1


def test_registered_owner_record_chat_and_cancelled_document_chat_do_not_bypass_consent(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, calls = registered_client
    person_id = client.get("/api/family-access/v1/me").json()["active_person_id"]
    source = client.post(
        "/api/product-core/v1/sources/manual-medication",
        json={"person_id": person_id, "medication": {"display_name": "Synthetic medicine"}},
    )
    assert source.status_code == 201, source.text
    candidate = client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": person_id,
            "source_id": source.json()["source"]["source_id"],
            "display_name": "Synthetic medicine",
        },
    )
    assert candidate.status_code == 201, candidate.text
    candidate_id = candidate.json()["id"]
    confirmed = client.post(f"/api/product-core/v1/candidates/{candidate_id}/confirm", json={})
    assert confirmed.status_code == 200, confirmed.text

    prepared = client.post("/api/chat/prepare", json={"question": "What is recorded?"})
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["status"] == "prepared"
    assert calls == []
    consent = client.post(
        f"/api/chat/executions/{prepared.json()['execution_id']}/consent",
        json={"fields": prepared.json()["preview"]["fields"]},
    )
    assert consent.status_code == 200, consent.text
    executed = client.post(
        f"/api/chat/executions/{prepared.json()['execution_id']}/execute",
        json={"question": "What is recorded?"},
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "answered"
    assert executed.json()["answer"]["citations"]
    receipt = client.get(
        f"/api/chat/executions/{prepared.json()['execution_id']}/receipt"
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["receipt_id"] == executed.json()["receipt_id"]
    assert len(calls) == 1

    upload = client.post(
        f"/api/product-core/v1/people/{person_id}/documents",
        content=_text_pdf("Synthetic pending document."),
        headers={"content-type": "application/pdf", "x-opencare-filename": "pending.pdf"},
    )
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]
    assert upload.json()["document"]["text_processing"]["status"] in {"pending", "ready"}
    assert len(calls) == 1

    main_module.app.state.product_core_runtime.documents.process_text(source_id)
    ready = client.get(
        f"/api/product-core/v1/people/{person_id}/documents/{source_id}"
    )
    assert ready.status_code == 200, ready.text
    assert ready.json()["text_processing"]["status"] == "ready"
    question_root = f"/api/product-core/v1/people/{person_id}/documents/{source_id}/questions"
    pending = client.post(f"{question_root}/prepare", json={"question": "Can I review this?"})
    assert pending.status_code == 200, pending.text
    assert pending.json()["status"] == "prepared"
    # The UI Cancel action stops here; consent and execute are deliberately absent.
    assert len(calls) == 1

    empty_upload = client.post(
        f"/api/product-core/v1/people/{person_id}/documents",
        content=_text_pdf(""),
        headers={"content-type": "application/pdf", "x-opencare-filename": "empty.pdf"},
    )
    assert empty_upload.status_code == 201, empty_upload.text
    empty_source_id = empty_upload.json()["document"]["source_id"]
    main_module.app.state.product_core_runtime.documents.process_text(empty_source_id)
    empty_document = client.get(
        f"/api/product-core/v1/people/{person_id}/documents/{empty_source_id}"
    )
    assert empty_document.status_code == 200, empty_document.text
    assert empty_document.json()["text_processing"]["status"] in {"ready", "failed", "unavailable"}
    if empty_document.json()["text_processing"]["status"] == "ready":
        assert empty_document.json()["extraction"]["total_chars"] == 0


def test_registered_owner_cannot_read_foreign_person_or_document_metadata(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, _calls = registered_client
    person_id = client.get("/api/family-access/v1/me").json()["active_person_id"]
    upload = client.post(
        f"/api/product-core/v1/people/{person_id}/documents",
        content=_text_pdf("Synthetic private page."),
        headers={"content-type": "application/pdf", "x-opencare-filename": "private.pdf"},
    )
    assert upload.status_code == 201, upload.text
    source_id = upload.json()["document"]["source_id"]

    foreign_list = client.get("/api/product-core/v1/people/foreign-person/documents")
    assert foreign_list.status_code in {403, 404}
    assert source_id not in foreign_list.text
    foreign_document = client.get(
        f"/api/product-core/v1/people/foreign-person/documents/{source_id}"
    )
    assert foreign_document.status_code in {403, 404}
    assert source_id not in foreign_document.text


def test_revoked_assignment_refuses_record_chat_before_context_projection(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, calls = registered_client
    me = client.get("/api/family-access/v1/me").json()
    person_id = me["active_person_id"]
    actor_id = me["actor"]["actor_id"]
    runtime = main_module.app.state.family_access_runtime
    with runtime.service.database.uow(begin_mode="IMMEDIATE") as uow:
        assert uow.connection is not None
        admin_row = uow.connection.execute(
            """
            SELECT actor_id FROM installation_admin_assignments
            WHERE is_active = 1 AND actor_id <> ? ORDER BY actor_id LIMIT 1
            """,
            (actor_id,),
        ).fetchone()
        assert admin_row is not None
        runtime.service._insert_assignment(
            uow.connection,
            acting_actor_id=actor_id,
            recipient_actor_id=str(admin_row["actor_id"]),
            person_id=person_id,
            role="owner",
            scopes=build_scopes("owner"),
            event_type="grant",
            reason_code="test_second_owner_for_revocation",
            now=runtime.service._timestamp(),
        )
        uow.connection.execute(
            """
            UPDATE own_person_links
            SET is_active = 0, revoked_at = ?, revoked_by_actor_id = ?
            WHERE actor_id = ? AND person_id = ? AND is_active = 1
            """,
            ("2026-10-07T12:00:00+00:00", actor_id, actor_id, person_id),
        )
        uow.connection.execute(
            """
            UPDATE person_access_assignments
            SET is_active = 0, revoked_at = ?, revoked_by_actor_id = ?
            WHERE actor_id = ? AND person_id = ? AND is_active = 1
            """,
            ("2026-10-07T12:00:00+00:00", actor_id, actor_id, person_id),
        )
    prepared = client.post("/api/chat/prepare", json={"question": "What is recorded?"})
    assert prepared.status_code == 403, prepared.text
    assert prepared.json()["reason_code"] in {"forbidden_access", "person_access_denied"}
    assert calls == []


def test_confirmed_records_remain_usable_when_caregiver_lacks_document_read(
    registered_client: tuple[TestClient, list[bytes]],
) -> None:
    client, calls = registered_client
    person_id = client.get("/api/family-access/v1/me").json()["active_person_id"]
    source = client.post(
        "/api/product-core/v1/sources/manual-medication",
        json={"person_id": person_id, "medication": {"display_name": "Synthetic medicine"}},
    )
    assert source.status_code == 201, source.text
    candidate = client.post(
        "/api/product-core/v1/candidates/medications",
        json={
            "person_id": person_id,
            "source_id": source.json()["source"]["source_id"],
            "display_name": "Synthetic medicine",
        },
    )
    assert candidate.status_code == 201, candidate.text
    confirmed = client.post(
        f"/api/product-core/v1/candidates/{candidate.json()['id']}/confirm", json={}
    )
    assert confirmed.status_code == 200, confirmed.text

    family_runtime = main_module.app.state.family_access_runtime
    with family_runtime.service.database.uow() as uow:
        assert uow.connection is not None
        admin_row = uow.connection.execute(
            """
            SELECT actor_id FROM installation_admin_assignments
            WHERE is_active = 1 ORDER BY actor_id LIMIT 1
            """
        ).fetchone()
    assert admin_row is not None
    caregiver = family_runtime.service.create_local_actor(
        str(admin_row["actor_id"]),
        username="synthetic-caregiver",
        display_name="Synthetic caregiver",
        password="synthetic caregiver password",
    )
    with family_runtime.service.database.uow(begin_mode="IMMEDIATE") as uow:
        assert uow.connection is not None
        family_runtime.service._insert_assignment(
            uow.connection,
            acting_actor_id=str(admin_row["actor_id"]),
            recipient_actor_id=caregiver.actor_id,
            person_id=person_id,
            role="caregiver",
            scopes=build_scopes("caregiver", generation=V2_POLICY_VERSION),
            event_type="grant",
            reason_code="test_v2_caregiver_without_documents",
            now=family_runtime.service._timestamp(),
        )

    logout = client.post("/api/family-access/v1/logout")
    assert logout.status_code == 204, logout.text
    login = client.post(
        "/api/family-access/v1/login",
        headers={"origin": "http://testserver"},
        json={"username": "synthetic-caregiver", "password": "synthetic caregiver password"},
    )
    assert login.status_code == 200, login.text
    csrf = client.cookies.get("opencare_csrf")
    assert csrf is not None
    client.headers.update({"origin": "http://testserver", "x-opencare-csrf": csrf})
    selected = client.put("/api/family-access/v1/active-person", json={"person_id": person_id})
    assert selected.status_code == 204, selected.text
    documents = client.get(f"/api/product-core/v1/people/{person_id}/documents")
    assert documents.status_code in {403, 404}
    assert "Synthetic medicine" not in documents.text
    prepared = client.post("/api/chat/prepare", json={"question": "What is recorded?"})
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["status"] == "prepared"
    assert calls == []
