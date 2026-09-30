from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.product_core.document_ocr import (
    DocumentOcrError,
    LocalOcrAdapter,
    OcrLimits,
)


def _blank_pdf(*, pages: int = 1) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=216, height=288)
    writer.write(output)
    return output.getvalue()


def _text_pdf(text: str) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    page = writer.add_blank_page(width=216, height=288)
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
    writer.write(output)
    return output.getvalue()


def _image_bytes(*, width: int = 12, height: int = 8, image_format: str = "PNG") -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color="white").save(output, format=image_format)
    return output.getvalue()


def test_embedded_pdf_text_is_returned_without_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LocalOcrAdapter(tesseract_executable="missing-tesseract")
    monkeypatch.setattr(
        adapter,
        "_run_tesseract",
        lambda image_bytes: pytest.fail("embedded text must not invoke OCR"),
    )

    payload = _text_pdf("Embedded text")
    result = adapter.extract(payload, media_type="application/pdf")

    assert result.original_bytes == payload
    assert result.pages[0].text == "Embedded text"
    assert result.pages[0].method == "embedded"
    assert result.pages[0].used_ocr is False


def test_scanned_pdf_page_is_rendered_then_ocred(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LocalOcrAdapter(tesseract_executable="tesseract")
    calls: list[bytes] = []

    def fake_ocr(image_bytes: bytes) -> str:
        calls.append(image_bytes)
        return "Синтетический отчёт"

    monkeypatch.setattr(adapter, "_run_tesseract", fake_ocr)

    result = adapter.extract(_blank_pdf(), media_type="application/pdf")

    assert result.pages[0].text == "Синтетический отчёт"
    assert result.pages[0].method == "ocr"
    assert result.pages[0].used_ocr is True
    assert len(calls) == 1
    assert calls[0].startswith(b"\x89PNG")


def test_pdf_signature_is_checked_before_rendering() -> None:
    adapter = LocalOcrAdapter(tesseract_executable="tesseract")

    with pytest.raises(DocumentOcrError, match="pdf_signature_invalid"):
        adapter.extract(b"not a pdf", media_type="application/pdf")


def test_image_input_is_validated_and_ocr_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LocalOcrAdapter(
        tesseract_executable="tesseract",
        limits=OcrLimits(max_render_width=20, max_render_height=20, max_render_pixels=400),
    )
    calls: list[bytes] = []
    monkeypatch.setattr(
        adapter, "_run_tesseract", lambda image_bytes: calls.append(image_bytes) or "OCR"
    )

    payload = _image_bytes()
    result = adapter.extract(payload, media_type="image/png")

    assert result.original_bytes == payload
    assert result.pages[0].text == "OCR"
    assert result.pages[0].method == "ocr"
    assert calls and calls[0].startswith(b"\x89PNG")


def test_oversized_image_is_rejected_before_tesseract(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LocalOcrAdapter(
        tesseract_executable="tesseract",
        limits=OcrLimits(max_render_width=20, max_render_height=20, max_render_pixels=100),
    )
    monkeypatch.setattr(
        adapter,
        "_run_tesseract",
        lambda _image_bytes: pytest.fail("oversized image must not invoke OCR"),
    )

    with pytest.raises(DocumentOcrError, match="image_pixels_limit_exceeded"):
        adapter.extract(_image_bytes(width=11, height=10), media_type="image/png")


def test_tesseract_resolution_uses_path_or_configured_executable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executable = tmp_path / "tesseract"
    executable.write_bytes(b"stub")
    configured = LocalOcrAdapter(tesseract_executable=executable)
    assert configured.tesseract_path == str(executable)

    monkeypatch.setattr(
        "app.product_core.document_ocr.shutil.which", lambda name: "/path/tesseract"
    )
    discovered = LocalOcrAdapter()
    assert discovered.tesseract_path == "/path/tesseract"


def test_tesseract_command_is_local_russian_english_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = LocalOcrAdapter(tesseract_executable="tesseract")
    observed: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> object:
        observed["args"] = args
        observed.update(kwargs)
        return type("Completed", (), {"returncode": 0, "stdout": b"OCR\n", "stderr": b""})()

    monkeypatch.setattr("app.product_core.document_ocr.subprocess.run", fake_run)

    assert adapter._run_tesseract(b"image") == "OCR"
    command = observed["args"][0]  # type: ignore[index]
    assert command == ("tesseract", "stdin", "stdout", "-l", "rus+eng")
    assert observed["timeout"] == adapter.limits.tesseract_timeout_seconds
    assert observed["input"] == b"image"


def test_tesseract_output_limit_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = LocalOcrAdapter(
        tesseract_executable="tesseract",
        limits=OcrLimits(max_tesseract_output_bytes=3),
    )
    monkeypatch.setattr(
        "app.product_core.document_ocr.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"returncode": 0, "stdout": b"toolong", "stderr": b""}
        )(),
    )

    with pytest.raises(DocumentOcrError, match="tesseract_output_limit_exceeded"):
        adapter._run_tesseract(b"image")


def test_missing_tesseract_language_data_has_a_specific_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = LocalOcrAdapter(tesseract_executable="tesseract")
    monkeypatch.setattr(
        "app.product_core.document_ocr.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed",
            (),
            {
                "returncode": 1,
                "stdout": b"",
                "stderr": b"Error opening data file rus.traineddata",
            },
        )(),
    )

    with pytest.raises(DocumentOcrError, match="tesseract_languages_missing"):
        adapter._run_tesseract(b"image")
