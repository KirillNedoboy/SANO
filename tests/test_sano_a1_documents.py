from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.product_core.errors import SourceCorruptionError
from app.product_core.models import Person
from app.product_core.services import DocumentService, SourceService
from app.product_core.sqlite import SQLiteDatabase
from tests.product_core_api_support import json_headers


class SequenceIds:
    def __init__(self) -> None:
        self.number = 0

    def __call__(self) -> str:
        self.number += 1
        return f"sano-id-{self.number}"


def _service(tmp_path: Path) -> tuple[SQLiteDatabase, DocumentService]:
    database = SQLiteDatabase(tmp_path / "product.sqlite3")
    database.migrate()
    now = datetime(2026, 9, 1, tzinfo=UTC)
    ids = SequenceIds()
    sources = SourceService(database, tmp_path / "sources", clock=lambda: now, id_factory=ids)
    with database.uow() as uow:
        uow.people.insert(
            Person(
                person_id="person-1",
                display_name="Synthetic Person",
                created_at=now,
                updated_at=now,
                is_active=True,
            )
        )
    return database, DocumentService(database, sources.store, clock=lambda: now, id_factory=ids)


def _blank_pdf() -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def test_blank_pdf_is_archived_even_when_local_ocr_is_unavailable(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)
    payload = _blank_pdf()

    result = documents.register(
        "person-1",
        payload,
        "application/pdf",
        original_filename="blank.pdf",
    )

    assert result.created is True
    assert result.source.document_title == "blank.pdf"
    assert documents.read_original(result.source.id)[1] == payload
    if result.extraction is None:
        assert documents.get_text_processing(result.source.id).status == "unavailable"
    else:
        assert result.extraction.total_chars == 0
        _, page = documents.get_page(result.source.id, result.extraction.extraction_id, 1)
        assert page.normalized_text == ""


def test_document_date_uses_one_explicit_document_context_date(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)

    result = documents.register(
        "person-1",
        "Результат исследования от 12.03.2024\nДата рождения: 01.02.1990".encode(),
        "text/plain",
        original_filename="upload-without-date.txt",
    )

    assert result.source.document_date.isoformat() == "2024-03-12"
    assert result.source.document_date_source == "extracted"


def test_document_date_accepts_an_explicit_date_label(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)

    result = documents.register(
        "person-1",
        b"Synthetic report Hemoglobin: 140 g/L Date: 2026-08-24",
        "text/plain",
        original_filename="report.txt",
    )

    assert result.source.document_date.isoformat() == "2026-08-24"
    assert result.source.document_date_source == "extracted"


def test_document_date_is_unknown_when_context_has_multiple_dates(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)

    result = documents.register(
        "person-1",
        "Результат исследования от 12.03.2024\nДата отчёта: 13.03.2024".encode(),
        "text/plain",
        original_filename="2020-01-01.txt",
    )

    assert result.source.document_date is None
    assert result.source.document_date_source == "unknown"


def test_metadata_update_and_duplicate_preserve_user_date(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)
    first = documents.register("person-1", b"Report", "text/plain", original_filename="r.txt")

    updated = documents.update_metadata(
        first.source.id,
        title="Lab report",
        document_date=datetime(2025, 4, 5, tzinfo=UTC).date(),
    )
    duplicate = documents.register(
        "person-1", b"Report", "text/plain", original_filename="other.txt"
    )

    assert updated.document_title == "Lab report"
    assert updated.document_date.isoformat() == "2025-04-05"
    assert updated.document_date_source == "user"
    assert duplicate.created is False
    assert duplicate.source.document_title == "Lab report"
    assert duplicate.source.document_date_source == "user"


def test_document_api_updates_metadata_and_serves_verified_original(
    product_core_client: TestClient,
) -> None:
    payload = b"Sano source text"
    created = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content=payload,
        headers={
            "content-type": "text/plain",
            "x-opencare-filename": "folder\\report.txt",
        },
    )
    assert created.status_code == 201, created.text
    document = created.json()["document"]
    source_id = document["source_id"]

    updated = product_core_client.patch(
        f"/api/product-core/v1/people/person-1/documents/{source_id}",
        json={"title": "Annual report", "document_date": "2024-05-06"},
        headers=json_headers(),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Annual report"
    assert updated.json()["document_date_source"] == "user"

    cleared = product_core_client.patch(
        f"/api/product-core/v1/people/person-1/documents/{source_id}",
        json={"document_date": None},
        headers=json_headers(),
    )
    assert cleared.status_code == 200
    assert cleared.json()["document_date"] is None
    assert cleared.json()["document_date_source"] == "unknown"

    viewed = product_core_client.get(
        f"/api/product-core/v1/people/person-1/documents/{source_id}/original"
    )
    downloaded = product_core_client.get(
        f"/api/product-core/v1/people/person-1/documents/{source_id}/download"
    )
    assert viewed.status_code == 200
    assert viewed.content == payload
    assert "inline" in viewed.headers["content-disposition"]
    assert downloaded.status_code == 200
    assert downloaded.content == payload
    assert "attachment" in downloaded.headers["content-disposition"]
    assert "/" not in downloaded.headers["content-disposition"]

    foreign = product_core_client.get(
        f"/api/product-core/v1/people/person-2/documents/{source_id}/original"
    )
    assert foreign.status_code == 404


def test_archive_is_person_scoped_and_creates_no_health_facts(tmp_path: Path) -> None:
    database, documents = _service(tmp_path)
    now = datetime(2026, 9, 1, tzinfo=UTC)
    with database.uow() as uow:
        uow.people.insert(
            Person(
                person_id="person-2",
                display_name="Second synthetic person",
                created_at=now,
                updated_at=now,
                is_active=True,
            )
        )
    first = documents.register("person-1", b"Glucose 5 mmol/L", "text/plain")
    second = documents.register("person-2", b"Glucose 5 mmol/L", "text/plain")
    assert first.source.id != second.source.id
    assert first.source.content_hash == second.source.content_hash
    with database.uow() as uow:
        for table in ("candidate_facts", "canonical_records", "document_fact_extraction_runs"):
            assert uow.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_metadata_survives_restart_and_date_clear_is_unknown(tmp_path: Path) -> None:
    database, documents = _service(tmp_path)
    created = documents.register("person-1", b"Report date: 03.04.2024", "text/plain")
    documents.update_metadata(created.source.id, title="Changed title", document_date=None)
    restarted_db = SQLiteDatabase(database.path)
    restarted_db.migrate()
    restarted = DocumentService(restarted_db, documents.store)
    loaded, _ = restarted.get(created.source.id)
    assert loaded.document_title == "Changed title"
    assert loaded.document_date is None
    assert loaded.document_date_source == "unknown"


def test_original_and_metadata_api_preserve_unicode_and_reject_foreign_person(
    product_core_client: TestClient,
) -> None:
    from urllib.parse import quote

    filename = "Анализы 2024.txt"
    created = product_core_client.post(
        "/api/product-core/v1/people/person-1/documents",
        content="Синтетический документ".encode(),
        headers={"content-type": "text/plain", "x-opencare-filename": quote(filename)},
    )
    assert created.status_code == 201
    item = created.json()["document"]
    assert item["title"] == filename
    original = product_core_client.get(
        f"/api/product-core/v1/people/person-1/documents/{item['source_id']}/download"
    )
    assert original.status_code == 200
    assert "filename*=UTF-8" in original.headers["content-disposition"]
    foreign = f"/api/product-core/v1/people/person-2/documents/{item['source_id']}"
    assert product_core_client.get(foreign + "/download").status_code == 404
    assert (
        product_core_client.patch(
            foreign, json={"title": "Forbidden"}, headers=json_headers()
        ).status_code
        == 404
    )


def test_original_refuses_corrupted_bytes(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)
    created = documents.register("person-1", b"Synthetic original", "text/plain")
    (tmp_path / "sources" / created.source.relative_path).write_bytes(b"changed")
    with pytest.raises(SourceCorruptionError):
        documents.read_original(created.source.id)


def test_archive_orders_document_dates_and_keeps_unknown_last(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)
    older = documents.register("person-1", b"Report date: 02.03.2024", "text/plain")
    unknown = documents.register("person-1", b"No document date", "text/plain")
    newer = documents.register("person-1", b"Report date: 06.07.2026", "text/plain")
    assert [source.id for source, _ in documents.list_for_person("person-1")] == [
        newer.source.id,
        older.source.id,
        unknown.source.id,
    ]
    assert unknown.source.document_date is None
