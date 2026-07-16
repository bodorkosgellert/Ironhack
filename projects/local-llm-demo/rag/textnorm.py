"""Shared query and document text normalization for retrieval."""

from __future__ import annotations

import re


def search_text(text: str) -> str:
    text = text.lower().replace("_", " ")
    text = re.sub(r"pm\s*2[.\s]?5", "pm25 particulate matter", text)
    text = text.replace("r²", "r2 coefficient determination")
    text = re.sub(r"\b(causes|causality|causally)\b", "causal", text)
    text = re.sub(r"\bindividuals\b", "individual", text)
    return re.sub(r"\s+", " ", text)
