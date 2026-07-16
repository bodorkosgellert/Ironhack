"""Lexical, dense, and hybrid retrieval over the allowlisted public corpus."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .corpus import Chunk, build_corpus
from .fusion import fuse_weighted_scores, reciprocal_rank_fusion
from .metrics import exact_metric_chunks
from .textnorm import search_text

RetrievalMode = Literal["tfidf", "dense", "hybrid"]
FusionMethod = Literal["weighted", "rrf"]

OTHER_GEOGRAPHIES = {
    "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana",
    "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico",
    "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee",
    "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming",
}

DEFAULT_LEXICAL_WEIGHT = 0.55
DEFAULT_DENSE_WEIGHT = 0.45


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float

    @property
    def citation(self) -> str:
        return self.chunk.citation


@dataclass(frozen=True)
class Retrieval:
    passages: list[ScoredChunk]
    refused: bool
    reason: str | None = None
    mode: str = "tfidf"
    notice: str | None = None


def _search_text(text: str) -> str:
    """Backward-compatible alias used by tests and older call sites."""
    return search_text(text)


def _unsupported_geography(question: str) -> str | None:
    lowered = question.lower()
    return next(
        (
            name
            for name in sorted(OTHER_GEOGRAPHIES, key=len, reverse=True)
            if re.search(rf"\b{re.escape(name)}\b", lowered)
        ),
        None,
    )


def _safety_chunks(question: str, chunks: list[Chunk]) -> list[Chunk]:
    """Prefer interpretation boundaries for causal phrasing."""
    q = question.lower()
    if not re.search(r"\b(caus\w*|causes|prove)\b", q):
        return []
    preferred = {
        (
            "projects/asthma-air-pollution/README.md",
            "Asthma prevalence and air pollution > Research question",
        ),
        (
            "projects/asthma-air-pollution/v2/VALIDATION.md",
            "Statistical validation and uncertainty > Interpretation boundaries",
        ),
    }
    return [chunk for chunk in chunks if (chunk.source, chunk.locator) in preferred]


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def resolve_retrieval_mode(mode: str | None = None) -> RetrievalMode:
    raw = (mode or os.environ.get("RETRIEVAL_MODE") or "tfidf").strip().lower()
    if raw not in {"tfidf", "dense", "hybrid"}:
        raise ValueError("retrieval mode must be one of: tfidf, dense, hybrid")
    return raw  # type: ignore[return-value]


class LexicalRetriever:
    """In-memory deterministic retriever over a fixed public corpus."""

    def __init__(self, chunks: list[Chunk] | None = None, threshold: float = 0.12):
        self.chunks = chunks if chunks is not None else build_corpus()
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            preprocessor=search_text,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.matrix = self.vectorizer.fit_transform(
            f"{chunk.source} {chunk.locator} {chunk.locator} {chunk.locator} {chunk.text}"
            for chunk in self.chunks
        )

    def lexical_scores(self, question: str) -> dict[int, float]:
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        return {index: float(scores[index]) for index in range(len(self.chunks)) if scores[index] > 0}

    def search(self, question: str, top_k: int = 5) -> Retrieval:
        return HybridRetriever(
            chunks=self.chunks,
            threshold=self.threshold,
            mode="tfidf",
            lexical=self,
        ).search(question, top_k=top_k)


class HybridRetriever:
    """TF-IDF by default, with optional dense or hybrid ranking when embeddings load."""

    def __init__(
        self,
        chunks: list[Chunk] | None = None,
        threshold: float = 0.12,
        *,
        mode: RetrievalMode | str = "tfidf",
        lexical_weight: float | None = None,
        dense_weight: float | None = None,
        fusion: FusionMethod | str = "weighted",
        dense_model: str | None = None,
        cache_dir: Path | None = None,
        lexical: LexicalRetriever | None = None,
        allow_dense_fallback: bool = True,
    ):
        self.chunks = chunks if chunks is not None else (lexical.chunks if lexical else build_corpus())
        self.threshold = threshold
        self.mode = resolve_retrieval_mode(mode)
        self.lexical_weight = (
            DEFAULT_LEXICAL_WEIGHT if lexical_weight is None else lexical_weight
        )
        self.dense_weight = DEFAULT_DENSE_WEIGHT if dense_weight is None else dense_weight
        if lexical_weight is None:
            self.lexical_weight = _env_float("RETRIEVAL_LEXICAL_WEIGHT", self.lexical_weight)
        if dense_weight is None:
            self.dense_weight = _env_float("RETRIEVAL_DENSE_WEIGHT", self.dense_weight)
        self.fusion = fusion if fusion in {"weighted", "rrf"} else "weighted"
        self.lexical = lexical or LexicalRetriever(chunks=self.chunks, threshold=threshold)
        self.chunks = self.lexical.chunks
        self.allow_dense_fallback = allow_dense_fallback
        self._dense = None
        self._dense_notice: str | None = None
        self._dense_model = dense_model
        self._cache_dir = cache_dir
        if self.mode in {"dense", "hybrid"}:
            self._try_load_dense()

    def _try_load_dense(self) -> None:
        from .dense import DEFAULT_DENSE_MODEL, DenseIndex, sentence_transformers_available

        model_name = self._dense_model or os.environ.get("DENSE_EMBEDDING_MODEL") or DEFAULT_DENSE_MODEL
        if not sentence_transformers_available():
            self._dense_notice = (
                "Dense embeddings unavailable (sentence-transformers not installed); "
                "using term frequency-inverse document frequency retrieval."
            )
            if self.mode == "dense" and not self.allow_dense_fallback:
                raise ImportError(self._dense_notice)
            return
        try:
            self._dense = DenseIndex(
                self.chunks,
                model_name=model_name,
                cache_dir=self._cache_dir,
            )
        except Exception as exc:  # model download or encode failure
            self._dense_notice = (
                f"Dense embeddings failed to load ({exc}); "
                "using term frequency-inverse document frequency retrieval."
            )
            if self.mode == "dense" and not self.allow_dense_fallback:
                raise

    @property
    def dense_loaded(self) -> bool:
        return self._dense is not None

    @property
    def effective_mode(self) -> str:
        if self.mode == "tfidf":
            return "tfidf"
        if self._dense is None:
            return "tfidf"
        return self.mode

    def search(self, question: str, top_k: int = 5) -> Retrieval:
        geography = _unsupported_geography(question)
        if geography:
            return Retrieval(
                [],
                True,
                f"The corpus contains Alabama results, not a specific {geography.title()} estimate.",
                mode=self.effective_mode,
                notice=self._dense_notice,
            )

        lexical_scores = self.lexical.lexical_scores(question)
        dense_scores: dict[int, float] = {}
        if self._dense is not None and self.mode in {"dense", "hybrid"}:
            raw = self._dense.scores(question)
            dense_scores = {
                index: float(raw[index])
                for index in range(len(self.chunks))
                if raw[index] > 0
            }

        if self.effective_mode == "dense":
            combined = dense_scores
        elif self.effective_mode == "hybrid":
            if self.fusion == "rrf":
                lexical_rank = sorted(lexical_scores, key=lexical_scores.get, reverse=True)
                dense_rank = sorted(dense_scores, key=dense_scores.get, reverse=True)
                combined = reciprocal_rank_fusion([lexical_rank, dense_rank])
            else:
                combined = fuse_weighted_scores(
                    lexical_scores,
                    dense_scores,
                    lexical_weight=self.lexical_weight,
                    dense_weight=self.dense_weight,
                )
        else:
            combined = lexical_scores

        ranked_indices = sorted(combined, key=combined.get, reverse=True)
        ranked = [
            ScoredChunk(self.chunks[index], float(combined[index]))
            for index in ranked_indices
            if combined[index] > 0
        ]

        # Exact metric routing is deterministic and takes precedence over prose
        # similarity; no value is calculated or parsed from natural language.
        exact = exact_metric_chunks(question, self.chunks) + _safety_chunks(question, self.chunks)
        exact_ids = {(chunk.source, chunk.locator) for chunk in exact}
        merged = [ScoredChunk(chunk, 1.0) for chunk in exact]
        merged.extend(item for item in ranked if (item.chunk.source, item.chunk.locator) not in exact_ids)
        passages = merged[: max(1, top_k)]

        # Reciprocal Rank Fusion scores are small absolute values, so refusal still
        # inspects the best underlying cosine similarity from either channel.
        if self.effective_mode == "hybrid" and self.fusion == "rrf":
            best_retrieval_score = max(
                max(lexical_scores.values(), default=0.0),
                max(dense_scores.values(), default=0.0),
            )
        else:
            best_retrieval_score = ranked[0].score if ranked else 0.0

        if exact:
            pass  # exact routing is authoritative even when prose similarity is weak
        elif not passages or best_retrieval_score < self.threshold:
            score = best_retrieval_score
            return Retrieval(
                passages,
                True,
                f"No passage met the evidence threshold ({score:.3f} < {self.threshold:.3f}).",
                mode=self.effective_mode,
                notice=self._dense_notice,
            )
        return Retrieval(
            passages,
            False,
            mode=self.effective_mode,
            notice=self._dense_notice,
        )


def make_retriever(
    mode: RetrievalMode | str = "tfidf",
    *,
    threshold: float = 0.12,
    chunks: list[Chunk] | None = None,
    lexical_weight: float | None = None,
    dense_weight: float | None = None,
    fusion: FusionMethod | str = "weighted",
) -> HybridRetriever:
    """Factory used by the command-line interface and Streamlit app."""
    return HybridRetriever(
        chunks=chunks,
        threshold=threshold,
        mode=mode,
        lexical_weight=lexical_weight,
        dense_weight=dense_weight,
        fusion=fusion,
    )
