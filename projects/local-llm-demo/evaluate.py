"""Run fixed retrieval benchmarks without requiring Ollama."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from rag.assistant import EvidenceAssistant

HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "evaluation" / "benchmarks.json"
DEFAULT_OUTPUT = HERE / "outputs" / "benchmark.json"


def run(
    cases_path: Path = DEFAULT_CASES,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    retrieval: str = "tfidf",
) -> dict:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    assistant = EvidenceAssistant(retrieval_mode=retrieval)
    records: list[dict] = []

    for case in cases:
        started = time.perf_counter()
        answer = assistant.ask(case["question"], retrieval_only=True, top_k=5)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        sources = [item.chunk.source for item in answer.passages]
        locators = [item.chunk.locator for item in answer.passages]
        passed = answer.refused == case.get("expect_refusal", False)
        if expected := case.get("expected_source"):
            passed = passed and any(expected in source for source in sources)
        if expected := case.get("expected_locator"):
            passed = passed and expected in locators
        records.append(
            {
                "id": case["id"],
                "question": case["question"],
                "passed": passed,
                "refused": answer.refused,
                "elapsed_ms": elapsed_ms,
                "top_score": answer.passages[0].score if answer.passages else None,
                "retrieval_mode": answer.retrieval_mode,
                "sources": sources,
                "locators": locators,
            }
        )

    summary = {
        "total": len(records),
        "passed": sum(record["passed"] for record in records),
        "failed": sum(not record["passed"] for record in records),
        "retrieval": retrieval,
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--retrieval",
        choices=("tfidf", "dense", "hybrid"),
        default="tfidf",
        help="Retrieval mode for the deterministic benchmark (default: tfidf)",
    )
    args = parser.parse_args()
    summary = run(args.cases, args.output, retrieval=args.retrieval)
    print(f"Benchmark: {summary['passed']}/{summary['total']} passed; {summary['failed']} failed")
    print(f"Wrote {args.output}")
    if summary["failed"]:
        for record in summary["records"]:
            if not record["passed"]:
                print(f"- FAIL {record['id']}: {record['sources'][:2]} {record['locators'][:2]}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
