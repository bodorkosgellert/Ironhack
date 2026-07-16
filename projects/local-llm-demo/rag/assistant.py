"""Orchestrate retrieval, refusal, and optional local generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .metrics import MetricFact, exact_metric_facts
from .ollama import DEFAULT_MODEL, OllamaError, chat, setup_instructions, status
from .prompts import SYSTEM_PROMPT, user_prompt
from .retrieval import LexicalRetriever, ScoredChunk

REFUSAL = "The available evidence does not answer this question."


@dataclass(frozen=True)
class Answer:
    text: str
    passages: list[ScoredChunk]
    refused: bool
    generation_used: bool
    notice: str | None = None


def _context(passages: list[ScoredChunk]) -> str:
    return "\n\n".join(
        f"[{item.citation}]\n{item.chunk.text}" for item in passages
    )


def _retrieval_answer(passages: list[ScoredChunk]) -> str:
    lines = ["Retrieved evidence (values are quoted, not recomputed):"]
    lines.extend(f"- {item.chunk.text} [{item.citation}]" for item in passages)
    return "\n".join(lines)


def _citations(passages: list[ScoredChunk]) -> str:
    return "\n".join(f"- [{item.citation}]" for item in passages)


def _metric_answer(facts: list[MetricFact]) -> str:
    lines = ["Verified stored metric (authoritative):"]
    lines.extend(
        f"- `{fact.locator}` = **{fact.rendered_value}** [{fact.citation}]"
        for fact in facts
    )
    return "\n".join(lines)


def _narration_conflicts(generated: str, facts: list[MetricFact]) -> bool:
    """Reject narration containing numeric claims other than exact routed values."""
    scrubbed = re.sub(r"\[[^\]]+\]", "", generated)
    scrubbed = re.sub(r"\bpm\s*2\s*[. ]\s*5\b", "PM", scrubbed, flags=re.I)
    expected = [float(fact.value) for fact in facts if isinstance(fact.value, (int, float))]
    pattern = r"(?<![\w.])[-+]?\s*(?:\d+\s*(?:\.\s*\d*)?|\.\s*\d+)(?:[eE]\s*[-+]?\s*\d+)?"
    for match in re.finditer(pattern, scrubbed):
        compact = re.sub(r"\s+", "", match.group())
        try:
            candidate = float(compact)
        except ValueError:
            return True
        if not any(abs(candidate - value) <= 1e-12 for value in expected):
            return True
    return False


class EvidenceAssistant:
    def __init__(
        self,
        threshold: float = 0.12,
        retriever: LexicalRetriever | None = None,
        *,
        status_fn: Callable = status,
        chat_fn: Callable = chat,
    ):
        self.retriever = retriever or LexicalRetriever(threshold=threshold)
        self.status_fn = status_fn
        self.chat_fn = chat_fn

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        retrieval_only: bool = False,
        model: str = DEFAULT_MODEL,
    ) -> Answer:
        result = self.retriever.search(question, top_k=top_k)
        if result.refused:
            detail = f" {result.reason}" if result.reason else ""
            return Answer(f"{REFUSAL}{detail}", result.passages, True, False)

        metric_facts = exact_metric_facts(question, self.retriever.chunks)
        deterministic = _metric_answer(metric_facts) if metric_facts else _retrieval_answer(result.passages)
        if retrieval_only:
            return Answer(deterministic, result.passages, False, False)

        ollama_status = self.status_fn()
        if not ollama_status.available:
            return Answer(
                deterministic,
                result.passages,
                False,
                False,
                "Ollama was not detected; showing deterministic retrieval only.\n" + setup_instructions(model),
            )
        if model not in ollama_status.models:
            return Answer(
                deterministic,
                result.passages,
                False,
                False,
                f"Model `{model}` is not installed. Run `ollama pull {model}`; showing retrieval only.",
            )

        try:
            generated = self.chat_fn(model, SYSTEM_PROMPT, user_prompt(question, _context(result.passages)))
        except OllamaError as exc:
            return Answer(
                deterministic,
                result.passages,
                False,
                False,
                f"{exc}\nShowing deterministic retrieval only.",
            )

        citation_block = _citations(result.passages)
        if metric_facts:
            if _narration_conflicts(generated, metric_facts):
                return Answer(
                    f"{deterministic}\n\nRetrieved citations:\n{citation_block}",
                    result.passages,
                    False,
                    True,
                    "Generated narration was omitted because it contained a conflicting numeric value.",
                )
            generated = f"{deterministic}\n\nOptional model interpretation (non-authoritative):\n{generated}"
        return Answer(
            f"{generated}\n\nRetrieved citations:\n{citation_block}",
            result.passages,
            False,
            True,
        )
