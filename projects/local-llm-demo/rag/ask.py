"""Command-line entry point for the cited evidence assistant."""

from __future__ import annotations

import argparse

from .assistant import EvidenceAssistant
from .ollama import DEFAULT_MODEL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Question about the public asthma analysis")
    parser.add_argument(
        "--retrieval-only",
        "--lexical-only",
        action="store_true",
        dest="retrieval_only",
        help="Skip generation and return deterministic cited passages",
    )
    parser.add_argument(
        "--retrieval",
        choices=("tfidf", "dense", "hybrid"),
        default="tfidf",
        help="Retrieval mode (default: tfidf). dense/hybrid need sentence-transformers.",
    )
    parser.add_argument(
        "--lexical-weight",
        type=float,
        default=None,
        help="Hybrid fusion weight for term frequency-inverse document frequency scores",
    )
    parser.add_argument(
        "--dense-weight",
        type=float,
        default=None,
        help="Hybrid fusion weight for dense embedding scores",
    )
    parser.add_argument("--show-sources", action="store_true", help="Print ranked source metadata")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Installed Ollama chat model")
    parser.add_argument("--top-k", type=int, default=5, help="Number of passages to retrieve")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.12,
        help="Minimum top cosine-similarity score before refusal",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assistant = EvidenceAssistant(
        threshold=args.threshold,
        retrieval_mode=args.retrieval,
        lexical_weight=args.lexical_weight,
        dense_weight=args.dense_weight,
    )
    answer = assistant.ask(
        args.question,
        top_k=args.top_k,
        retrieval_only=args.retrieval_only,
        model=args.model,
    )
    print(answer.text)
    if answer.notice:
        print(f"\nStatus:\n{answer.notice}")
    if args.show_sources and answer.passages:
        print("\nRanked sources:")
        for passage in answer.passages:
            print(f"- {passage.score:.3f} | {passage.citation}")
        print(f"\nRetrieval mode: {answer.retrieval_mode}")
    return 2 if answer.refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
