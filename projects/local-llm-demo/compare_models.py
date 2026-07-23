"""Compare installed Ollama models on fixed, cited asthma evidence questions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from rag.assistant import REFUSAL, EvidenceAssistant
from rag.ollama import OllamaStatus, chat, status
from rag.prompts import SYSTEM_PROMPT, user_prompt
from rag.retrieval import LexicalRetriever, ScoredChunk

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "outputs" / "model_comparison.csv"
TOP_K = 5
TEMPERATURE = 0
MAX_RESPONSE_TOKENS = 350


@dataclass(frozen=True)
class ComparisonCase:
    id: str
    question: str
    required_values: tuple[float, ...] = ()
    value_tolerance: float = 1e-9
    expected_citation: str | None = None
    required_terms: tuple[str, ...] = ()
    expect_refusal: bool = False
    forbidden_patterns: tuple[str, ...] = ()


CASES = (
    ComparisonCase(
        id="pearson_metric",
        question="What is the exact Pearson correlation between PM2.5 and asthma?",
        required_values=(-0.05726740504810031,),
        expected_citation="$.pearson_r_pm25_asthma",
    ),
    ComparisonCase(
        id="cross_validated_r2",
        question="What is the cross-validated R² for the PM2.5-only model?",
        required_values=(-0.321694185275063,),
        expected_citation="$.models[0].r2_cv_mean",
    ),
    ComparisonCase(
        id="ecological_causality",
        question="Does this study prove that PM2.5 causes asthma in individuals?",
        expected_citation="projects/asthma-air-pollution",
        required_terms=("ecological",),
        forbidden_patterns=(
            r"\bpm2\.?5 causes asthma\b",
            r"\bproves? (?:that )?pm2\.?5\b",
            r"\bcausal effect (?:is|was) established\b",
        ),
    ),
    ComparisonCase(
        id="outcome_distinction",
        question="How do prevalence, incidence, and acute exacerbations differ in this analysis?",
        expected_citation="projects/asthma-air-pollution",
        required_terms=("prevalence", "incidence", "exacerbation"),
    ),
    ComparisonCase(
        id="outside_geography",
        question="What is the specific PM2.5 effect estimate for California?",
        expect_refusal=True,
    ),
)


def _context(passages: Sequence[ScoredChunk]) -> str:
    return "\n\n".join(f"[{item.citation}]\n{item.chunk.text}" for item in passages)


def strip_reasoning(text: str) -> str:
    """Remove public-facing analysis blocks emitted by some reasoning models."""
    cleaned = re.sub(r"<(?:think|analysis)>.*?</(?:think|analysis)>", "", text, flags=re.I | re.S)
    cleaned = re.sub(r"<(?:think|analysis)>.*$", "", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"</?(?:think|analysis)>", "", cleaned, flags=re.I)
    return cleaned.strip()


def _contains_number(text: str, expected: float, tolerance: float) -> bool:
    number_pattern = r"(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    for match in re.finditer(number_pattern, text.replace(",", "")):
        try:
            if abs(float(match.group()) - expected) <= tolerance:
                return True
        except ValueError:
            continue
    return False


def score_answer(case: ComparisonCase, answer: str, refused: bool) -> dict:
    """Apply transparent objective checks; no language-model judge is used."""
    checks: dict[str, bool] = {"refusal": refused == case.expect_refusal}
    lowered = answer.lower()
    for value in case.required_values:
        checks[f"value:{value}"] = _contains_number(answer, value, case.value_tolerance)
    if case.expected_citation:
        checks[f"citation:{case.expected_citation}"] = case.expected_citation.lower() in lowered
    for term in case.required_terms:
        checks[f"term:{term}"] = term.lower() in lowered
    for pattern in case.forbidden_patterns:
        checks[f"forbidden:{pattern}"] = re.search(pattern, lowered) is None
    return {
        "passed": all(checks.values()),
        "objective_passed": sum(checks.values()),
        "objective_total": len(checks),
        "checks": checks,
    }


def _error_records(
    model: str,
    cases: Sequence[ComparisonCase],
    retriever: LexicalRetriever,
    error: str,
    mode: str,
) -> list[dict]:
    records = []
    for case in cases:
        retrieval = retriever.search(case.question, top_k=TOP_K)
        records.append(
            {
                "model": model,
                "evaluation_mode": mode,
                "question_id": case.id,
                "question": case.question,
                "answer": "",
                "retrieved_citations": [item.citation for item in retrieval.passages],
                "latency_ms": None,
                "success": False,
                "error": error,
                "refused": retrieval.refused,
                "generated": False,
                "passed": False,
                "objective_passed": 0,
                "objective_total": 0,
                "checks": {},
            }
        )
    return records


def compare(
    models: Sequence[str],
    *,
    limit: int = len(CASES),
    timeout: float = 120.0,
    status_fn: Callable[[], OllamaStatus] = status,
    chat_fn: Callable[..., str] = chat,
    retriever: LexicalRetriever | None = None,
    mode: str = "raw",
    continue_on_error: bool = False,
) -> list[dict]:
    """Compare raw model compliance or complete assistant correctness."""
    if mode not in {"raw", "assistant"}:
        raise ValueError("mode must be 'raw' or 'assistant'")
    selected_cases = CASES[: max(0, min(limit, len(CASES)))]
    evidence = retriever or LexicalRetriever()
    ollama = status_fn()
    records: list[dict] = []

    if not ollama.available:
        reason = f"Ollama is unavailable: {ollama.error or 'health check failed'}"
        for model in models:
            records.extend(_error_records(model, selected_cases, evidence, reason, mode))
        return records

    installed = set(ollama.models)
    for model in models:
        if model not in installed:
            records.extend(
                _error_records(
                    model,
                    selected_cases,
                    evidence,
                    f"Model is not installed: {model}. Check `ollama list`.",
                    mode,
                )
            )
            continue

        for case_index, case in enumerate(selected_cases):
            retrieval = evidence.search(case.question, top_k=TOP_K)
            citations = [item.citation for item in retrieval.passages]
            started = time.perf_counter()
            error = ""
            generated = False
            if mode == "assistant":
                bounded_chat = lambda selected_model, system, prompt: strip_reasoning(
                    chat_fn(
                        selected_model,
                        system,
                        prompt,
                        timeout=timeout,
                        num_predict=MAX_RESPONSE_TOKENS,
                        temperature=TEMPERATURE,
                    )
                )
                assistant = EvidenceAssistant(
                    retriever=evidence,
                    status_fn=lambda: ollama,
                    chat_fn=bounded_chat,
                )
                try:
                    result = assistant.ask(case.question, top_k=TOP_K, model=model)
                    answer = result.text
                    refused = result.refused
                    generated = result.generation_used
                except Exception as exc:  # client normalises expected transport failures
                    answer = ""
                    refused = retrieval.refused
                    error = f"{type(exc).__name__}: {exc}"
            elif retrieval.refused:
                answer = REFUSAL
                refused = True
            else:
                refused = False
                try:
                    answer = strip_reasoning(
                        chat_fn(
                            model,
                            SYSTEM_PROMPT,
                            user_prompt(case.question, _context(retrieval.passages)),
                            timeout=timeout,
                            num_predict=MAX_RESPONSE_TOKENS,
                            temperature=TEMPERATURE,
                        )
                    )
                    generated = True
                except Exception as exc:  # client normalises expected transport failures
                    answer = ""
                    error = f"{type(exc).__name__}: {exc}"
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            scored = score_answer(case, answer, refused) if not error else {
                "passed": False,
                "objective_passed": 0,
                "objective_total": 0,
                "checks": {},
            }
            records.append(
                {
                    "model": model,
                    "evaluation_mode": mode,
                    "question_id": case.id,
                    "question": case.question,
                    "answer": answer,
                    "retrieved_citations": citations,
                    "latency_ms": elapsed_ms,
                    "success": not error,
                    "error": error,
                    "refused": refused,
                    "generated": generated,
                    **scored,
                }
            )
            if error and not continue_on_error:
                remaining = selected_cases[case_index + 1:]
                records.extend(
                    _error_records(
                        model,
                        remaining,
                        evidence,
                        f"Skipped after prior model failure: {error}",
                        mode,
                    )
                )
                break
    return records


def write_results(records: Sequence[dict], output_path: Path) -> tuple[Path, Path]:
    """Write spreadsheet-friendly rows and a lossless JSON companion."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model", "evaluation_mode", "question_id", "question", "answer", "retrieved_citations",
        "latency_ms", "success", "error", "refused", "generated", "passed",
        "objective_passed", "objective_total", "checks",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["retrieved_citations"] = " | ".join(record["retrieved_citations"])
            row["checks"] = json.dumps(record["checks"], sort_keys=True)
            writer.writerow(row)

    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(list(records), indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path, json_path


def summarise(records: Sequence[dict]) -> list[dict]:
    summaries = []
    groups = dict.fromkeys((record["model"], record.get("evaluation_mode", "raw")) for record in records)
    for model, mode in groups:
        rows = [
            record for record in records
            if record["model"] == model and record.get("evaluation_mode", "raw") == mode
        ]
        latencies = [record["latency_ms"] for record in rows if record["latency_ms"] is not None]
        summaries.append(
            {
                "model": model,
                "evaluation_mode": mode,
                "cases_passed": sum(bool(record["passed"]) for record in rows),
                "cases_total": len(rows),
                "objective_passed": sum(record["objective_passed"] for record in rows),
                "objective_total": sum(record["objective_total"] for record in rows),
                "latency_ms": round(sum(latencies), 2),
                "errors": sum(not record["success"] for record in rows),
            }
        )
    return summaries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", required=True, help="Installed Ollama model names")
    parser.add_argument("--limit", type=int, default=len(CASES), help="Use the first N fixed cases (maximum 5)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Comparison CSV path")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-generation timeout in seconds")
    parser.add_argument(
        "--mode",
        choices=("raw", "assistant"),
        default="raw",
        help="Score raw model output or the end-to-end assistant composition",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep scoring remaining cases after a timeout or transport failure",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    records = compare(
        args.models,
        limit=args.limit,
        timeout=args.timeout,
        mode=args.mode,
        continue_on_error=args.continue_on_error,
    )
    csv_path, json_path = write_results(records, args.output)
    for summary in summarise(records):
        print(
            f"{summary['model']} ({summary['evaluation_mode']}): "
            f"{summary['cases_passed']}/{summary['cases_total']} cases; "
            f"{summary['objective_passed']}/{summary['objective_total']} objective checks; "
            f"{summary['latency_ms']:.2f} ms total; {summary['errors']} errors"
        )
    print(f"Wrote {csv_path} and {json_path}")
    return 1 if any(not record["success"] for record in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
