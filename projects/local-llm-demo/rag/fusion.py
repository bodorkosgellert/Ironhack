"""Score fusion helpers for hybrid lexical and dense retrieval."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def normalize_scores(scores: Mapping[int, float]) -> dict[int, float]:
    """Min-max normalize scores into [0, 1]. Empty or constant maps become zeros."""
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if high <= low:
        return {index: 0.0 for index in scores}
    span = high - low
    return {index: (value - low) / span for index, value in scores.items()}


def clip_unit_interval(scores: Mapping[int, float]) -> dict[int, float]:
    """Clip scores into [0, 1] without relative rescaling across the candidate set."""
    return {index: max(0.0, min(1.0, float(value))) for index, value in scores.items()}


def fuse_weighted_scores(
    lexical_scores: Mapping[int, float],
    dense_scores: Mapping[int, float],
    *,
    lexical_weight: float = 0.55,
    dense_weight: float = 0.45,
    relative_normalize: bool = False,
) -> dict[int, float]:
    """Combine lexical and dense scores with a weighted sum.

    By default scores are clipped to [0, 1] independently. Relative min-max
    normalization is optional because it can inflate weak matches and weaken
    low-score refusal.
    """
    if lexical_weight < 0 or dense_weight < 0:
        raise ValueError("Fusion weights must be non-negative.")
    total = lexical_weight + dense_weight
    if total <= 0:
        raise ValueError("At least one fusion weight must be positive.")
    lexical_w = lexical_weight / total
    dense_w = dense_weight / total
    if relative_normalize:
        lexical_norm = normalize_scores(lexical_scores)
        dense_norm = normalize_scores(dense_scores)
    else:
        lexical_norm = clip_unit_interval(lexical_scores)
        dense_norm = clip_unit_interval(dense_scores)
    indices = set(lexical_norm) | set(dense_norm)
    return {
        index: lexical_w * lexical_norm.get(index, 0.0) + dense_w * dense_norm.get(index, 0.0)
        for index in indices
    }


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[int]],
    *,
    rank_constant: int = 60,
) -> dict[int, float]:
    """Reciprocal Rank Fusion over one or more index rankings (best first)."""
    if rank_constant <= 0:
        raise ValueError("rank_constant must be positive.")
    fused: dict[int, float] = {}
    for ranking in ranked_lists:
        for rank, index in enumerate(ranking, start=1):
            fused[index] = fused.get(index, 0.0) + 1.0 / (rank_constant + rank)
    return fused
