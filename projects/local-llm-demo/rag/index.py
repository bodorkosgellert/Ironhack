"""Inspect or explicitly export the deterministic corpus manifest."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .corpus import build_corpus, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=Path, help="Optional JSON Lines output path")
    args = parser.parse_args()
    chunks = build_corpus()
    counts = Counter(chunk.kind for chunk in chunks)
    print(f"Built {len(chunks)} chunks: {dict(sorted(counts.items()))}")
    if args.write:
        write_manifest(args.write)
        print(f"Wrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
