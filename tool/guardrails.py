"""Input, PDF and output guardrails."""

import re

from config import INPUT_BANNED, OUTPUT_BLOCKLIST, PDF_BANNED


class GuardrailError(ValueError):
    """Raised when a guardrail blocks the request."""


# Matches whole words (plus common suffixes) so "hackathon" is NOT blocked.
_INPUT_PATTERN = re.compile(
    r"\b(?:" + "|".join(map(re.escape, INPUT_BANNED)) + r")(?:s|ed|ing|er|ers)?\b",
    re.IGNORECASE,
)


def pdf_guardrail(docs):
    """Reject PDFs that contain sensitive strings."""
    for doc in docs:
        text = doc.page_content.lower()
        for word in PDF_BANNED:
            if word in text:
                raise GuardrailError(f"Sensitive PDF content found: '{word}'")
    return docs


def check_banned_content(user_input: str) -> str:
    """Reject inappropriate user prompts."""
    if _INPUT_PATTERN.search(user_input or ""):
        raise GuardrailError(
            "I cannot process requests containing inappropriate content. "
            "Please rephrase your request."
        )
    return user_input


def output_guardrail(answer: str) -> str:
    """Block model answers that leak sensitive terms."""
    lower = answer.lower()
    for word in OUTPUT_BLOCKLIST:
        if word in lower:
            return "Response Blocked: Sensitive data detected."
    return answer