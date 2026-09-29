from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])",
    # Vietnamese mobile numbers, including the common spaced/dotted/dashed
    # forms and the international +84 form.
    "phone_vn": r"(?<!\d)(?:(?:\+84|0)[ .-]?(?:2\d{1,2}|[35789]\d)(?:[ .-]?\d){7,8})(?!\d)",
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    "credit_card": r"(?<!\d)\d{4}(?:[- ]?\d{4}){3}(?!\d)",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
