from __future__ import annotations

import hashlib
import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfWriter

from app.product_core.errors import DocumentValidationError
from app.product_core.models import Person
from app.product_core.services import DocumentService, SourceService
from app.product_core.sqlite import SQLiteDatabase


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self) -> str:
        self.value += 1
        return f"x2-document-{self.value}"


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


def _image_bytes(kind: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (8, 6), color="white").save(output, format=kind)
    return output.getvalue()


def _blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_upload_persists_original_before_text_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, documents = _service(tmp_path)
    payload = b"Synthetic document text"

    def fail_extraction(*args: object, **kwargs: object) -> object:
        raise RuntimeError("downstream extraction failed")

    monkeypatch.setattr(DocumentService, "_extract", staticmethod(fail_extraction))
    result = documents.register(
        "person-1", payload, "text/plain", original_filename="note.txt", process_immediately=False
    )

    assert result.created is True
    assert result.extraction is None
    assert documents.read_original(result.source.id)[1] == payload
    assert result.source.content_hash == hashlib.sha256(payload).hexdigest()
    with database.connect() as connection:
        row = connection.execute(
            "SELECT status, extraction_id FROM document_text_processing WHERE source_id = ?",
            (result.source.id,),
        ).fetchone()
    assert row is not None
    assert row["status"] == "pending"
    assert row["extraction_id"] is None


@pytest.mark.parametrize(
    ("media_type", "payload"),
    [("image/png", _image_bytes("PNG")), ("image/jpeg", _image_bytes("JPEG"))],
)
def test_upload_accepts_signature_checked_images(
    tmp_path: Path, media_type: str, payload: bytes
) -> None:
    _, documents = _service(tmp_path)

    result = documents.register(
        "person-1", payload, media_type, original_filename="scan", process_immediately=False
    )

    assert result.created is True
    assert result.extraction is None
    assert result.source.media_type == media_type
    assert result.source.document_kind == "image"
    assert documents.read_original(result.source.id)[1] == payload


def test_image_mime_must_match_decoded_format(tmp_path: Path) -> None:
    _, documents = _service(tmp_path)

    with pytest.raises(DocumentValidationError, match="image_format_mismatch"):
        documents.register("person-1", _image_bytes("JPEG"), "image/png", process_immediately=False)


def test_text_processing_creates_immutable_d2_snapshot_after_upload(tmp_path: Path) -> None:
    database, documents = _service(tmp_path)
    result = documents.register(
        "person-1",
        b"Report date: 2026-08-24\nHemoglobin: 140",
        "text/plain",
        process_immediately=False,
    )
    assert result.extraction is None

    extraction = documents.process_text(result.source.id)

    assert extraction.status == "complete"
    assert extraction.total_chars > 0
    stored_source, listed_extraction = documents.get(result.source.id)
    assert stored_source.content_hash == hashlib.sha256(
        b"Report date: 2026-08-24\nHemoglobin: 140"
    ).hexdigest()
    assert listed_extraction.extraction_id == extraction.extraction_id
    _, page = documents.get_page(result.source.id, extraction.extraction_id, 1)
    assert "Hemoglobin: 140" in page.normalized_text
    with database.connect() as connection:
        status = connection.execute(
            "SELECT status FROM document_text_processing WHERE source_id = ?",
            (result.source.id,),
        ).fetchone()["status"]
    assert status == "ready"


def test_duplicate_upload_is_person_scoped_and_keeps_metadata(tmp_path: Path) -> None:
    database, documents = _service(tmp_path)
    payload = _blank_pdf()
    first = documents.register(
        "person-1", payload, "application/pdf", original_filename="first.pdf"
    )
    with database.uow() as uow:
        uow.people.insert(
            Person(
                person_id="person-2",
                display_name="Other Synthetic Person",
                created_at=first.source.created_at,
                updated_at=first.source.created_at,
                is_active=True,
            )
        )
    updated_source = documents.update_metadata(first.source.id, title="Edited title")

    same_person = documents.register(
        "person-1", payload, "application/pdf", original_filename="replacement.pdf"
    )
    other_person = documents.register(
        "person-2", payload, "application/pdf", original_filename="other.pdf"
    )

    assert same_person.created is False
    assert same_person.source.id == first.source.id
    assert same_person.source.document_title == updated_source.document_title == "Edited title"
    assert other_person.created is True
    assert other_person.source.id != first.source.id
