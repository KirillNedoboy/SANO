import re

from app.agent.models import PolicyDecision

URGENT_PATTERNS = (
    r"chest pain",
    r"cannot breathe|can.t breathe|difficulty breathing",
    r"overdose",
    r"suicid|self[- ]harm",
    r"immediate danger|emergency",
)
BLOCKED_PATTERNS = (
    r"what diagnosis do i have|diagnose me|do i have .*diagnos",
    r"which medication should i choose|should i take .*medication|recommend .*medication",
    r"increase (my |the )?(dose|dosage)|decrease (my |the )?(dose|dosage)",
    r"should i stop taking|should i start taking|change (my |the )?medication",
    r"what treatment should i start|recommend .*treatment",
    r"genetic variant|genotype|pgx|pharmacogen|dna result",
)

RUSSIAN_REQUEST_PATTERNS = (
    r"\b(?:какой|какая|какое|какие)\s+(?:у\s+меня|мне)\s+диагноз\w*\b",
    r"\b(?:постав\w*|определ\w*|диагностир\w*)\s+(?:мне\s+)?диагноз\w*\b",
    r"\b(?:какое|какую|какой)\s+\w*\s*лечени\w*\b.*\b(?:мне\s+)?(?:начать|выбрать|назначить|применять|принимать)\w*\b",
    r"\b(?:какой|какую|какое|какие)\s+(?:мне\s+)?(?:препарат\w*|лекарств\w*|медикамент\w*)\b"
    r".*\b(?:мне\s+)?(?:выбрать|принимать|начать|назначить)\w*\b",
    r"\b(?:мне|я)\s+(?:начать|начинать|прекратить|прекращать|отменить|отменять|"
    r"заменить|заменять|сменить|сменять)\w*\b.*\b(?:прием\w*|принимать|"
    r"лекарств\w*|препарат\w*|таблетк\w*|медикамент\w*)\b",
    r"\b(?:начать|прекратить|отменить|заменить|сменить)\w*\b.*\b(?:прием\w*|"
    r"принимать|лекарств\w*|препарат\w*|таблетк\w*|медикамент\w*)\b",
    r"\b(?:увелич\w*|уменьш\w*|измен\w*|скорректир\w*|корректир\w*)\b.*\b"
    r"(?:доз\w*|дозиров\w*)\b",
    r"\b(?:доз\w*|дозиров\w*)\b.*\b(?:увелич\w*|уменьш\w*|измен\w*|"
    r"скорректир\w*|корректир\w*)\b",
    r"\bчем\s+(?:это\s+)?леч\w*\b",
    r"\b(?:какую|какой|какое|какие)\s+(?:мне\s+)?доз\w*\b.*\b"
    r"(?:принимать|начать|измен\w*|увелич\w*|уменьш\w*)\w*\b",
    r"\b(?:что|какой|какую)\s+(?:мне\s+)?(?:начать|продолжить|перестать)\s+"
    r"(?:принимать|пить)\w*\b",
    r"\b(?:можно|можно\s+ли|стоит\s+ли|следует\s+ли)\s+(?:мне\s+)?"
    r"(?:отменить|прекратить|заменить|сменить|перестать|поменять)\w*\b.*\b"
    r"(?:лекарств\w*|препарат\w*|медикамент\w*|таблетк\w*)\b",
)

MIXED_REQUEST_PATTERNS = (
    r"\b(?:should|could|can|do\s+i\s+need\s+to|what|which)\b.*\b"
    r"(?:диагноз\w*|лечени\w*|препарат\w*|лекарств\w*|доз\w*|дозиров\w*|"
    r"прием\w*|принимать)\b",
    r"\b(?:какой|какая|какое|какие)\s+(?:у\s+меня|мне)\s+"
    r"(?:diagnosis|treatment|medication|medicine|drug|dose|dosage)\b",
    r"\b(?:какой|какая|какое|какие)\b.*\b(?:diagnosis|treatment|medication|"
    r"medicine|drug|dose|dosage)\b.*\b(?:у\s+меня|мне)\b",
    r"\b(?:should|could|can)\b.*\b(?:увелич\w*|уменьш\w*|измен\w*|"
    r"замен\w*|отмен\w*)\b.*\b(?:dose|dosage|medication|medicine|drug|treatment)\b",
)

RUSSIAN_DIAGNOSTIC_OUTPUT_PATTERNS = (
    r"\b(?:у\s+вас|у\s+тебя|вам\s+поставлен\w*|вам\s+установлен\w*)\b.*\b"
    r"(?:диагноз\w*|заболеван\w*|состояни\w*)\b",
    r"\b(?:ваш|ваша|ваше)\s+(?:диагноз\w*|заболеван\w*|состояни\w*)\b",
    r"\b(?:у\s+вас|у\s+тебя)\s+(?:есть\s+)?(?:диабет\w*|гипертон\w*|"
    r"астм\w*|анеми\w*|инфекци\w*|онкологи\w*|рак\w*|синдром\w*)\b",
    r"\b(?:вы|ты)\s+(?:болен|больна|больны|болеете|страдаете)\b",
    r"\b(?:результат\w*|анализ\w*|показател\w*|данн\w*|это)\b.*\b"
    r"(?:указыва\w*|свидетельств\w*|говор\w*|подтвержда\w*|означа\w*)\b.*\b"
    r"(?:диабет\w*|гипертон\w*|астм\w*|анеми\w*|инфекци\w*|онкологи\w*|"
    r"рак\w*|синдром\w*|гипотиреоз\w*|гипертиреоз\w*|пневмони\w*|"
    r"артрит\w*|остеопороз\w*|заболеван\w*|диагноз\w*)\b",
    r"\b(?:вам|тебе)\s+(?:назначен\w*|прописан\w*|подобран\w*|"
    r"рекомендован\w*)\b.*\b(?:препарат\w*|лекарств\w*|доз\w*|лечени\w*|"
    r"терапи\w*)\b",
)

RUSSIAN_PRESCRIPTIVE_OUTPUT_PATTERNS = (
    r"\b(?:вам|тебе)\s+(?:следует|нужно|надо|необходимо|рекомендуется)\b.*\b"
    r"(?:принимать|начать|прекратить|увелич\w*|уменьш\w*|измен\w*|замен\w*|"
    r"отмен\w*|препарат\w*|лекарств\w*|доз\w*|лечени\w*|терапи\w*)\b",
    r"\b(?:принимайте|начните|прекратите|увеличьте|уменьшите|измените|замените|"
    r"отмените|подберите|выберите)\b.*\b(?:препарат\w*|лекарств\w*|доз\w*|"
    r"лечени\w*|терапи\w*|таблетк\w*)\b",
    r"\b(?:рекомендую|советую)\s+(?:вам|тебе)\b",
    r"\b(?:вам|тебе)\s+(?:начать|прекратить|изменить|увеличить|уменьшить|"
    r"заменить|отменить)\w*\b.*\b(?:препарат\w*|лекарств\w*|доз\w*|"
    r"лечени\w*|терапи\w*|таблетк\w*)\b",
    r"\b(?:следует|необходимо|рекомендуется|рекомендовано)\b.*\b(?:принимать|"
    r"начать|прекратить|увелич\w*|уменьш\w*|измен\w*|замен\w*|отмен\w*|"
    r"доз\w*|лечени\w*|терапи\w*)\b",
)

SOURCE_ATTRIBUTION_PATTERN = (
    r"\b(?:в|из|согласно)\s+(?:документ\w*|выписк\w*|анализ\w*|"
    r"отчет\w*|источник\w*|протокол\w*)\b"
    r"|\b(?:документ\w*|выписк\w*|анализ\w*|отчет\w*|источник\w*)\s+"
    r"(?:указан\w*|содержит|сообща\w*|отмеча\w*|написан\w*)\b"
)


def _normalize_safety_text(value: str) -> str:
    normalized = value.casefold().replace("ё", "е")
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def has_unsafe_russian_output(text: str) -> bool:
    for sentence in re.split(r"[.!?;\n]+", text):
        normalized = _normalize_safety_text(sentence)
        if not normalized:
            continue
        if any(
            re.search(pattern, normalized) for pattern in RUSSIAN_PRESCRIPTIVE_OUTPUT_PATTERNS
        ):
            return True
        if not re.search(SOURCE_ATTRIBUTION_PATTERN, normalized) and any(
            re.search(pattern, normalized) for pattern in RUSSIAN_DIAGNOSTIC_OUTPUT_PATTERNS
        ):
            return True
    return False


def classify_question(question: str) -> PolicyDecision:
    normalized = " ".join(question.lower().split())
    if any(re.search(pattern, normalized) for pattern in URGENT_PATTERNS):
        return PolicyDecision(
            decision="urgent",
            reason_code="urgent_language",
            response_text=(
                "If you may be in immediate danger, contact local emergency services or a "
                "licensed medical professional now. OpenCare cannot assess emergencies."
            ),
        )
    safety_normalized = _normalize_safety_text(question)
    russian_blocked = any(
        re.search(pattern, safety_normalized) for pattern in RUSSIAN_REQUEST_PATTERNS
    )
    mixed_blocked = any(
        re.search(pattern, safety_normalized) for pattern in MIXED_REQUEST_PATTERNS
    )
    if russian_blocked or mixed_blocked or any(
        re.search(pattern, normalized) for pattern in BLOCKED_PATTERNS
    ):
        return PolicyDecision(
            decision="blocked",
            reason_code="clinical_or_genetics_request",
            response_text=(
                "OpenCare can summarize recorded, source-backed vault information but cannot "
                "diagnose, recommend treatment, select medication, or advise medication changes."
            ),
        )
    return PolicyDecision(decision="allowed", reason_code="recorded_context", response_text="")
