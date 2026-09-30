from __future__ import annotations

import re
from datetime import date

_DOCUMENT_DATE_TOKEN = r"(?P<date>\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-\d{2}-\d{2})"
_DOCUMENT_DATE_CONTEXT_PATTERNS = (
    re.compile(
        rf"(?:^|[\s|])(?:document\s+)?date\s*[:=]\s*{_DOCUMENT_DATE_TOKEN}",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        rf"(?:^|[\s|])дата\s*[:=]\s*{_DOCUMENT_DATE_TOKEN}",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        rf"(?:date\s+of\s+(?:the\s+)?(?:document|report|study|exam|visit)|"
        rf"(?:document|report|study|test|exam|visit)\s+date|"
        rf"(?:issued|performed|conducted|dated|result(?:s)?\s+date))"
        rf"[^\n\r0-9]{{0,40}}{_DOCUMENT_DATE_TOKEN}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:дата\s+(?:документа|исследования|отч[её]та|выдачи|проведения|осмотра|анализа)|"
        rf"(?:результат|результаты|исследование|исследования|отч[её]т|заключение|осмотр|анализ)"
        rf"[^\n\r0-9]{{0,25}}(?:от|дата)?)"
        rf"[^\n\r0-9]{{0,20}}{_DOCUMENT_DATE_TOKEN}",
        re.IGNORECASE,
    ),
)


def parse_document_date(value: str) -> date | None:
    try:
        if "-" in value:
            return date.fromisoformat(value)
        day, month, year = (int(part) for part in re.split(r"[./]", value))
        return date(year, month, day)
    except (TypeError, ValueError):
        return None


def extract_document_date(text: str) -> date | None:
    """Return one explicit document-context date, or unknown when ambiguous."""
    candidates: set[date] = set()
    for pattern in _DOCUMENT_DATE_CONTEXT_PATTERNS:
        for match in pattern.finditer(text):
            parsed = parse_document_date(match.group("date"))
            if parsed is not None:
                candidates.add(parsed)
    return next(iter(candidates)) if len(candidates) == 1 else None
