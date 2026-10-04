import re
from enum import StrEnum

from app.agent.models import AgentAnswer, AgentContext
from app.agent.policy import has_unsafe_russian_output


class ValidationDiagnostic(StrEnum):
    """Bounded internal diagnostics for structural validation failures."""

    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
    PAGE_NUMBERS_MISSING = "page_numbers_missing"
    PAGE_NUMBERS_DUPLICATE = "page_numbers_duplicate"
    PAGE_OUT_OF_SCOPE = "page_out_of_scope"
    COVERAGE_INCONSISTENT = "coverage_inconsistent"
    CONTROL_CHARACTER = "control_character"


class ValidationResult:
    def __init__(
        self,
        valid: bool,
        reason_code: str | None = None,
        diagnostic: ValidationDiagnostic | None = None,
        diagnostic_field: str | None = None,
        diagnostic_error_type: str | None = None,
    ) -> None:
        self.valid = valid
        self.reason_code = reason_code
        self.diagnostic = diagnostic
        self.internal_diagnostic = diagnostic
        self.diagnostic_field = diagnostic_field
        self.diagnostic_error_type = diagnostic_error_type


UNSAFE_PRESCRIPTIVE_PATTERNS = (
    r"\byou should (take|start|stop|increase|decrease|change|switch)\b",
    r"\b(increase|decrease|adjust) (your |the )?(dose|dosage)\b",
    r"\bstart taking\b|\bstop taking\b|\bdiscontinue\b",
    r"\byou have (a |an )?(diagnosis|condition)\b",
    r"\bi recommend\b|\bthe best treatment\b",
)
PATH_PATTERN = re.compile(r"(?:[A-Za-z]:\\|/(?:home|tmp|var|Users|private)/)")
SECRET_PATTERN = re.compile(r"(?:api[_ -]?key|authorization|bearer\s+[A-Za-z0-9])", re.IGNORECASE)


def validate_answer(answer: AgentAnswer, context: AgentContext) -> ValidationResult:
    known_source_ids = {source.source_id for source in context.sources}
    if any(citation.source_id not in known_source_ids for citation in answer.citations):
        return ValidationResult(False, "unknown_citation")
    content = "\n".join(
        [answer.answer, *answer.unknowns, *answer.doctor_questions, *answer.boundary_notices]
    )
    if PATH_PATTERN.search(content):
        return ValidationResult(False, "private_path")
    if SECRET_PATTERN.search(content):
        return ValidationResult(False, "secret_pattern")
    if any(
        re.search(pattern, content, flags=re.IGNORECASE)
        for pattern in UNSAFE_PRESCRIPTIVE_PATTERNS
    ) or has_unsafe_russian_output(content):
        return ValidationResult(False, "unsafe_prescriptive_claim")
    return ValidationResult(True)
