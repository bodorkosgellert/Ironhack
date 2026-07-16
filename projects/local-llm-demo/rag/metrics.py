"""Deterministic routing for questions about stored numeric results."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .corpus import ASTHMA_ROOT, Chunk


@dataclass(frozen=True)
class MetricTarget:
    source_suffix: str
    locator: str


@dataclass(frozen=True)
class MetricFact:
    """An exact JSON value resolved independently of language generation."""

    source: str
    locator: str
    value: Any

    @property
    def citation(self) -> str:
        return f"{self.source} — {self.locator}"

    @property
    def rendered_value(self) -> str:
        return json.dumps(self.value, ensure_ascii=False, sort_keys=True)


def _normalise(question: str) -> str:
    return re.sub(r"[^a-z0-9²]+", " ", question.lower()).strip()


def targets_for_question(question: str) -> list[MetricTarget]:
    """Return exact JSON leaves for well-defined metric intents."""
    q = _normalise(question)
    mentions_pm25 = "pm2 5" in q or "pm25" in q or "particulate" in q
    targets: list[MetricTarget] = []

    if mentions_pm25 and "pearson" in q and ("asthma" in q or "correlation" in q):
        targets.append(MetricTarget("v2/outputs/metrics.json", "$.pearson_r_pm25_asthma"))
    if mentions_pm25 and ("cross validated" in q or "cross validation" in q or "cv" in q) and ("r2" in q or "r²" in q):
        targets.extend(
            [
                MetricTarget("v2/outputs/multivariate_metrics.json", "$.models[0].r2_cv_mean"),
                MetricTarget("v2/outputs/multivariate_metrics.json", "$.models[0].r2_cv_std"),
            ]
        )
    if mentions_pm25 and ("partial" in q or "adjusted" in q) and "correlation" in q:
        targets.append(
            MetricTarget(
                "v2/outputs/multivariate_metrics.json",
                "$.partial_correlations_vs_asthma.partial_r_pm25_ug_m3_annual_mean_vs_asthma",
            )
        )
    if mentions_pm25 and ("coefficient of variation" in q or "exposure contrast" in q or "spread" in q):
        targets.append(
            MetricTarget("v2/outputs/feature_analysis.json", "$.variance_analysis.pm25_ug_m3_annual_mean.cv")
        )
    if mentions_pm25 and "permutation" in q and ("p value" in q or "significant" in q):
        targets.append(
            MetricTarget(
                "v2/outputs/robustness_report.json",
                "$.pm25_asthma_association.permutation_test.p_value_two_sided",
            )
        )
    if mentions_pm25 and "bootstrap" in q:
        targets.extend(
            [
                MetricTarget(
                    "v2/outputs/robustness_report.json",
                    "$.pm25_asthma_association.bootstrap_95ci.ci_low",
                ),
                MetricTarget(
                    "v2/outputs/robustness_report.json",
                    "$.pm25_asthma_association.bootstrap_95ci.ci_high",
                ),
            ]
        )
    if "obesity" in q and "correlation" in q:
        targets.append(
            MetricTarget(
                "v2/outputs/multivariate_metrics.json",
                "$.pearson_correlation_matrix.asthma_pct.obesity_pct",
            )
        )
    return targets


def exact_metric_chunks(question: str, chunks: list[Chunk]) -> list[Chunk]:
    targets = targets_for_question(question)
    return [
        chunk
        for target in targets
        for chunk in chunks
        if chunk.source.endswith(target.source_suffix) and chunk.locator == target.locator
    ]


def _value_at_path(data: Any, locator: str) -> Any:
    """Resolve the restricted JSONPath syntax emitted by ``corpus.py``."""
    value = data
    tokens = re.findall(r"(?:^|\.)?([A-Za-z0-9_]+)|\[(\d+)\]", locator.removeprefix("$"))
    for key, index in tokens:
        value = value[int(index)] if index else value[key]
    return value


def exact_metric_facts(question: str, chunks: list[Chunk]) -> list[MetricFact]:
    """Load recognised metrics from their allowlisted JSON files by key path."""
    facts: list[MetricFact] = []
    for chunk in exact_metric_chunks(question, chunks):
        relative = chunk.source.removeprefix("projects/asthma-air-pollution/")
        data = json.loads((ASTHMA_ROOT / relative).read_text(encoding="utf-8"))
        facts.append(MetricFact(chunk.source, chunk.locator, _value_at_path(data, chunk.locator)))
    return facts


def is_numeric_question(question: str) -> bool:
    q = _normalise(question)
    terms = {
        "correlation",
        "r2",
        "r²",
        "metric",
        "mean",
        "range",
        "coefficient",
        "p value",
        "confidence interval",
        "how many",
    }
    return any(term in q for term in terms)
