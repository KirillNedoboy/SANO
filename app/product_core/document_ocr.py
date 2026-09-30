"""Bounded local OCR for the SANO-X2 document understanding path.

This module deliberately has no persistence or Product Core service coupling.  It
accepts immutable document bytes, returns immutable page results, and invokes only
the locally installed Tesseract executable.  PDF pages with usable embedded text
remain on the embedded-text path and are never rendered or sent to OCR.
"""

from __future__ import annotations

import io
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pypdf
import pypdfium2 as pdfium  # type: ignore[import-untyped]
from PIL import (
    Image,
    UnidentifiedImageError,
)

from app.product_core.errors import DocumentValidationError

PageMethod = Literal["embedded", "ocr"]

_SUPPORTED_MEDIA_TYPES = frozenset({"application/pdf", "image/png", "image/jpeg"})
_IMAGE_FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG"}
_TESSERACT_LANGUAGES = "rus+eng"


class DocumentOcrError(DocumentValidationError):
    """Raised when bounded local OCR cannot safely process a document."""


class OcrLimitsError(DocumentOcrError):
    """Raised when the configured OCR limits are invalid."""


@dataclass(frozen=True, slots=True)
class OcrLimits:
    """Resource limits applied before and during local OCR."""

    max_input_bytes: int = 10 * 1024 * 1024
    max_pages: int = 200
    render_dpi: int = 200
    max_render_width: int = 4096
    max_render_height: int = 4096
    max_render_pixels: int = 16_777_216
    max_image_bytes: int = 16 * 1024 * 1024
    max_page_chars: int = 100_000
    max_total_chars: int = 500_000
    tesseract_timeout_seconds: float = 30.0
    max_tesseract_output_bytes: int = 1_000_000

    def __post_init__(self) -> None:
        integer_limits = (
            ("max_input_bytes", self.max_input_bytes),
            ("max_pages", self.max_pages),
            ("render_dpi", self.render_dpi),
            ("max_render_width", self.max_render_width),
            ("max_render_height", self.max_render_height),
            ("max_render_pixels", self.max_render_pixels),
            ("max_image_bytes", self.max_image_bytes),
            ("max_page_chars", self.max_page_chars),
            ("max_total_chars", self.max_total_chars),
            ("max_tesseract_output_bytes", self.max_tesseract_output_bytes),
        )
        if any(not isinstance(value, int) or value <= 0 for _, value in integer_limits):
            raise OcrLimitsError("ocr_limits_invalid")
        if not math.isfinite(self.tesseract_timeout_seconds) or self.tesseract_timeout_seconds <= 0:
            raise OcrLimitsError("ocr_limits_invalid")


@dataclass(frozen=True, slots=True)
class OcrPage:
    """Text and provenance for one input page."""

    page_number: int
    text: str
    method: PageMethod

    @property
    def used_ocr(self) -> bool:
        return self.method == "ocr"


@dataclass(frozen=True, slots=True)
class OcrResult:
    """Deterministic OCR output with the original bytes retained unchanged."""

    original_bytes: bytes
    media_type: str
    pages: tuple[OcrPage, ...]

    @property
    def text(self) -> str:
        """Return page text in input order for callers needing one string."""

        return "\n\n".join(page.text for page in self.pages)


class LocalOcrAdapter:
    """Run bounded, offline OCR with embedded-text and image/PDF safeguards."""

    tesseract_languages = _TESSERACT_LANGUAGES

    def __init__(
        self,
        *,
        limits: OcrLimits | None = None,
        tesseract_executable: str | Path | None = None,
    ) -> None:
        self.limits = limits or OcrLimits()
        self._configured_tesseract = (
            str(tesseract_executable) if tesseract_executable is not None else None
        )

    @property
    def tesseract_path(self) -> str:
        """Resolve the configured executable or the executable available on PATH."""

        return self._resolve_tesseract()

    def extract(
        self,
        payload: bytes,
        *,
        media_type: str = "application/pdf",
    ) -> OcrResult:
        """Extract page text from a PDF or image without changing source bytes."""

        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise DocumentOcrError("document_bytes_invalid")
        original_bytes = bytes(payload)
        if len(original_bytes) > self.limits.max_input_bytes:
            raise DocumentOcrError("input_bytes_limit_exceeded")
        normalized_media_type = media_type.split(";", 1)[0].strip().lower()
        if normalized_media_type not in _SUPPORTED_MEDIA_TYPES:
            raise DocumentOcrError("unsupported_media_type")
        if normalized_media_type == "application/pdf":
            if not original_bytes.startswith(b"%PDF-"):
                raise DocumentOcrError("pdf_signature_invalid")
            pages = self._extract_pdf(original_bytes)
        else:
            pages = (self._extract_image(original_bytes, normalized_media_type),)
        return OcrResult(
            original_bytes=original_bytes,
            media_type=normalized_media_type,
            pages=tuple(pages),
        )

    def _extract_pdf(self, payload: bytes) -> tuple[OcrPage, ...]:
        try:
            reader = pypdf.PdfReader(io.BytesIO(payload), strict=True)
            if reader.is_encrypted:
                raise DocumentOcrError("encrypted_pdf")
            pdf_pages = reader.pages
            page_count = len(pdf_pages)
        except DocumentOcrError:
            raise
        except Exception:
            raise DocumentOcrError("malformed_pdf") from None

        if page_count == 0:
            raise DocumentOcrError("pdf_no_pages")
        if page_count > self.limits.max_pages:
            raise DocumentOcrError("page_limit_exceeded")

        results: list[OcrPage] = []
        total_chars = 0
        pdf_document: object | None = None
        try:
            for index, pdf_page in enumerate(pdf_pages, start=1):
                try:
                    embedded_text = pdf_page.extract_text() or ""
                except Exception:
                    raise DocumentOcrError("malformed_pdf") from None
                normalized_text = self._normalize_text(str(embedded_text))
                if normalized_text.strip():
                    page = OcrPage(index, normalized_text, "embedded")
                else:
                    if pdf_document is None:
                        try:
                            pdf_document = pdfium.PdfDocument(payload)
                        except Exception:
                            raise DocumentOcrError("pdf_render_failed") from None
                    page = self._ocr_pdf_page(pdf_document, index - 1)
                total_chars = self._check_text_limits(page.text, total_chars)
                results.append(page)
        finally:
            if pdf_document is not None:
                close = getattr(pdf_document, "close", None)
                if callable(close):
                    close()
        return tuple(results)

    def _ocr_pdf_page(self, pdf_document: object, page_index: int) -> OcrPage:
        try:
            page = pdf_document[page_index]  # type: ignore[index]
            try:
                image_bytes = self._render_pdf_page(page)
            finally:
                close = getattr(page, "close", None)
                if callable(close):
                    close()
        except DocumentOcrError:
            raise
        except Exception:
            raise DocumentOcrError("pdf_render_failed") from None
        return OcrPage(page_index + 1, self._run_tesseract(image_bytes), "ocr")

    def _render_pdf_page(self, page: object) -> bytes:
        try:
            width_points, height_points = page.get_size()  # type: ignore[attr-defined]
            scale = self.limits.render_dpi / 72.0
            width, height = self._bounded_dimensions(
                width_points * scale,
                height_points * scale,
                width_reason="render_width_limit_exceeded",
                height_reason="render_height_limit_exceeded",
                pixels_reason="render_pixels_limit_exceeded",
            )
            bitmap = page.render(scale=scale, rev_byteorder=True)  # type: ignore[attr-defined]
            try:
                image = bitmap.to_pil()
            finally:
                close = getattr(bitmap, "close", None)
                if callable(close):
                    close()
            if image.size != (width, height):
                self._bounded_dimensions(
                    float(image.width),
                    float(image.height),
                    width_reason="render_width_limit_exceeded",
                    height_reason="render_height_limit_exceeded",
                    pixels_reason="render_pixels_limit_exceeded",
                )
            return self._encode_image(image, "rendered_image_bytes_limit_exceeded")
        except DocumentOcrError:
            raise
        except Exception:
            raise DocumentOcrError("pdf_render_failed") from None

    def _extract_image(self, payload: bytes, media_type: str) -> OcrPage:
        expected_format = _IMAGE_FORMATS[media_type]
        try:
            with Image.open(io.BytesIO(payload)) as source_image:
                if source_image.format != expected_format:
                    raise DocumentOcrError("image_format_mismatch")
                self._bounded_dimensions(
                    float(source_image.width),
                    float(source_image.height),
                    width_reason="image_width_limit_exceeded",
                    height_reason="image_height_limit_exceeded",
                    pixels_reason="image_pixels_limit_exceeded",
                )
                source_image.load()
                image = source_image.convert("RGB")
        except DocumentOcrError:
            raise
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
            raise DocumentOcrError("malformed_image") from None
        try:
            image_bytes = self._encode_image(image, "image_bytes_limit_exceeded")
        finally:
            image.close()
        return OcrPage(1, self._run_tesseract(image_bytes), "ocr")

    def _encode_image(self, image: Image.Image, size_reason: str) -> bytes:
        output = io.BytesIO()
        try:
            image.save(output, format="PNG", optimize=False)
        except Exception:
            raise DocumentOcrError("image_encode_failed") from None
        encoded = output.getvalue()
        if len(encoded) > self.limits.max_image_bytes:
            raise DocumentOcrError(size_reason)
        return encoded

    def _bounded_dimensions(
        self,
        width: float,
        height: float,
        *,
        width_reason: str,
        height_reason: str,
        pixels_reason: str,
    ) -> tuple[int, int]:
        if (
            not math.isfinite(width)
            or not math.isfinite(height)
            or width <= 0
            or height <= 0
        ):
            raise DocumentOcrError("image_dimensions_invalid")
        width_pixels = max(1, math.ceil(width))
        height_pixels = max(1, math.ceil(height))
        if width_pixels > self.limits.max_render_width:
            raise DocumentOcrError(width_reason)
        if height_pixels > self.limits.max_render_height:
            raise DocumentOcrError(height_reason)
        if width_pixels * height_pixels > self.limits.max_render_pixels:
            raise DocumentOcrError(pixels_reason)
        return width_pixels, height_pixels

    def _check_text_limits(self, text: str, total_chars: int) -> int:
        if len(text) > self.limits.max_page_chars:
            raise DocumentOcrError("page_chars_limit_exceeded")
        total = total_chars + len(text)
        if total > self.limits.max_total_chars:
            raise DocumentOcrError("total_chars_limit_exceeded")
        return total

    @staticmethod
    def _normalize_text(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()

    def _resolve_tesseract(self) -> str:
        if self._configured_tesseract is not None:
            return self._configured_tesseract
        executable = shutil.which("tesseract")
        if executable is None:
            raise DocumentOcrError("tesseract_not_found")
        return executable

    def _run_tesseract(self, image_bytes: bytes) -> str:
        command = (
            self._resolve_tesseract(),
            "stdin",
            "stdout",
            "-l",
            _TESSERACT_LANGUAGES,
        )
        try:
            completed = subprocess.run(
                command,
                input=image_bytes,
                capture_output=True,
                timeout=self.limits.tesseract_timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            raise DocumentOcrError("tesseract_not_found") from None
        except PermissionError:
            raise DocumentOcrError("tesseract_unavailable") from None
        except subprocess.TimeoutExpired:
            raise DocumentOcrError("tesseract_timeout") from None
        except OSError:
            raise DocumentOcrError("tesseract_unavailable") from None
        if len(completed.stdout) > self.limits.max_tesseract_output_bytes or len(
            completed.stderr
        ) > self.limits.max_tesseract_output_bytes:
            raise DocumentOcrError("tesseract_output_limit_exceeded")
        if completed.returncode != 0:
            stderr_text = completed.stderr.decode("utf-8", errors="replace").lower()
            if (
                "traineddata" in stderr_text
                or "failed loading language" in stderr_text
                or "could not initialize tesseract" in stderr_text
            ):
                raise DocumentOcrError("tesseract_languages_missing")
            raise DocumentOcrError("tesseract_failed")
        try:
            text = completed.stdout.decode("utf-8")
        except UnicodeDecodeError:
            raise DocumentOcrError("tesseract_output_invalid") from None
        return self._normalize_text(text)


# Explicit aliases keep the integration surface easy to discover without adding
# another implementation or persistence path.
DocumentOcrResult = OcrResult
OcrPageResult = OcrPage
