"""Orchestrate retrieval, refusal, and optional local or hosted generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .hosted import HostedLLMError, chat_hosted, load_hosted_config
from .metrics import MetricFact, exact_metric_facts
from .ollama import DEFAULT_MODEL, OllamaError, chat, setup_instructions, status
from .prompts import SYSTEM_PROMPT, user_prompt
from .retrieval import HybridRetriever, LexicalRetriever, RetrievalMode, ScoredChunk, make_retriever

REFUSAL = "The available evidence does not answer this question."


@dataclass(frozen=True)
class Answer:
    text: str
    passages: list[ScoredChunk]
    refused: bool
    generation_used: bool
    notice: str | None = None
    retrieval_mode: str = "tfidf"


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


def _join_notices(*parts: str | None) -> str | None:
    messages = [part.strip() for part in parts if part and part.strip()]
    return "\n".join(messages) if messages else None


class EvidenceAssistant:
    def __init__(
        self,
        threshold: float = 0.12,
        retriever: LexicalRetriever | HybridRetriever | None = None,
        *,
        retrieval_mode: RetrievalMode | str = "tfidf",
        lexical_weight: float | None = None,
        dense_weight: float | None = None,
        status_fn: Callable = status,
        chat_fn: Callable = chat,
        hosted_chat_fn: Callable | None = None,
        hosted_secrets: dict | None = None,
    ):
        if retriever is not None:
            self.retriever = retriever
        else:
            self.retriever = make_retriever(
                retrieval_mode,
                threshold=threshold,
                lexical_weight=lexical_weight,
                dense_weight=dense_weight,
            )
        self.status_fn = status_fn
        self.chat_fn = chat_fn
        self.hosted_chat_fn = hosted_chat_fn or chat_hosted
        self.hosted_secrets = hosted_secrets

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        retrieval_only: bool = False,
        model: str = DEFAULT_MODEL,
    ) -> Answer:
        result = self.retriever.search(question, top_k=top_k)
        retrieval_mode = getattr(result, "mode", "tfidf")
        retrieval_notice = getattr(result, "notice", None)
        if result.refused:
            detail = f" {result.reason}" if result.reason else ""
            return Answer(
                f"{REFUSAL}{detail}",
                result.passages,
                True,
                False,
                notice=retrieval_notice,
                retrieval_mode=retrieval_mode,
            )

        metric_facts = exact_metric_facts(question, self.retriever.chunks)
        deterministic = _metric_answer(metric_facts) if metric_facts else _retrieval_answer(result.passages)
        if retrieval_only:
            return Answer(
                deterministic,
                result.passages,
                False,
                False,
                notice=retrieval_notice,
                retrieval_mode=retrieval_mode,
            )

        ollama_status = self.status_fn()
        if ollama_status.available and model in ollama_status.models:
            try:
                generated = self.chat_fn(
                    model,
                    SYSTEM_PROMPT,
                    user_prompt(question, _context(result.passages)),
                )
            except OllamaError as exc:
                return Answer(
                    deterministic,
                    result.passages,
                    False,
                    False,
                    notice=_join_notices(retrieval_notice, f"{exc}\nShowing deterministic retrieval only."),
                    retrieval_mode=retrieval_mode,
                )
            return self._compose_generated(
                generated,
                deterministic,
                metric_facts,
                result.passages,
                retrieval_mode,
                retrieval_notice,
            )

        hosted = load_hosted_config(self.hosted_secrets)
        if hosted is not None:
            try:
                generated = self.hosted_chat_fn(
                    SYSTEM_PROMPT,
                    user_prompt(question, _context(result.passages)),
                    config=hosted,
                    secrets=self.hosted_secrets,
                )
            except HostedLLMError as exc:
                return Answer(
                    deterministic,
                    result.passages,
                    False,
                    False,
                    notice=_join_notices(
                        retrieval_notice,
                        f"{exc}\nShowing deterministic retrieval only.",
                    ),
                    retrieval_mode=retrieval_mode,
                )
            return self._compose_generated(
                generated,
                deterministic,
                metric_facts,
                result.passages,
                retrieval_mode,
                _join_notices(
                    retrieval_notice,
                    f"Used hosted model `{hosted.model}` because local Ollama was unavailable.",
                ),
            )

        if not ollama_status.available:
            notice = _join_notices(
                retrieval_notice,
                "Ollama was not detected and no hosted language-model secrets were configured; "
                "showing deterministic retrieval only.\n" + setup_instructions(model),
            )
        else:
            notice = _join_notices(
                retrieval_notice,
                f"Model `{model}` is not installed locally and no hosted language-model secrets "
                f"were configured. Run `ollama pull {model}`, or set HOSTED_LLM_* secrets; "
                "showing retrieval only.",
            )
        return Answer(
            deterministic,
            result.passages,
            False,
            False,
            notice=notice,
            retrieval_mode=retrieval_mode,
        )

    def _compose_generated(
        self,
        generated: str,
        deterministic: str,
        metric_facts: list[MetricFact],
        passages: list[ScoredChunk],
        retrieval_mode: str,
        notice: str | None,
    ) -> Answer:
        citation_block = _citations(passages)
        if metric_facts:
            if _narration_conflicts(generated, metric_facts):
                return Answer(
                    f"{deterministic}\n\nRetrieved citations:\n{citation_block}",
                    passages,
                    False,
                    True,
                    notice=_join_notices(
                        notice,
                        "Generated narration was omitted because it contained a conflicting numeric value.",
                    ),
                    retrieval_mode=retrieval_mode,
                )
            generated = f"{deterministic}\n\nOptional model interpretation (non-authoritative):\n{generated}"
        return Answer(
            f"{generated}\n\nRetrieved citations:\n{citation_block}",
            passages,
            False,
            True,
            notice=notice,
            retrieval_mode=retrieval_mode,
        )
