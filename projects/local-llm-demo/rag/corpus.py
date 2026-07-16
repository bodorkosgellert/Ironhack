"""Build a small, traceable corpus from public asthma project artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

DEMO_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DEMO_ROOT.parents[1]
ASTHMA_ROOT = REPO_ROOT / "projects" / "asthma-air-pollution"

# An allowlist makes it impossible for future private notes, notebooks, or data
# files to enter the corpus merely because they were added below this directory.
PUBLIC_MARKDOWN = (
    "README.md",
    "LITERATURE.md",
    "ROADMAP.md",
    "v2/README.md",
    "v2/VALIDATION.md",
    "v2/FEATURE_ANALYSIS.md",
)
PUBLIC_JSON = (
    "v2/outputs/metrics.json",
    "v2/outputs/multivariate_metrics.json",
    "v2/outputs/robustness_report.json",
    "v2/outputs/feature_analysis.json",
)


@dataclass(frozen=True)
class Chunk:
    """A retrievable passage with a stable citation."""

    source: str
    locator: str
    text: str
    kind: str

    @property
    def citation(self) -> str:
        return f"{self.source} — {self.locator}"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _split_long_section(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split long prose on paragraph boundaries while retaining small overlap."""
    if len(text) <= max_chars:
        return [text.strip()] if text.strip() else []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            pieces.append(current)
            tail = current[-overlap:].lstrip() if overlap else ""
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_markdown(path: Path, max_chars: int = 1400, overlap: int = 160) -> list[Chunk]:
    """Chunk Markdown by heading-defined sections."""
    text = path.read_text(encoding="utf-8")
    source = _relative(path)
    chunks: list[Chunk] = []
    heading_stack: list[tuple[int, str]] = []
    current_heading = "Document introduction"
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if not body:
            return
        heading_path = " > ".join(title for _, title in heading_stack) or current_heading
        for piece in _split_long_section(body, max_chars, overlap):
            chunks.append(Chunk(source, heading_path, piece, "markdown"))

    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not match:
            current_lines.append(line)
            continue
        flush()
        current_lines = []
        level = len(match.group(1))
        title = match.group(2)
        heading_stack = [(n, h) for n, h in heading_stack if n < level]
        heading_stack.append((level, title))
        current_heading = title
    flush()
    return chunks


def _json_leaves(value: Any, path: str = "$", context: tuple[str, ...] = ()) -> Iterable[tuple[str, Any, tuple[str, ...]]]:
    if isinstance(value, dict):
        labels = tuple(
            f"{key}={item}"
            for key, item in value.items()
            if key in {"model", "feature", "check", "state", "year"} and not isinstance(item, (dict, list))
        )
        for key in sorted(value):
            yield from _json_leaves(value[key], f"{path}.{key}", context + labels)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _json_leaves(item, f"{path}[{index}]", context)
    else:
        yield path, value, context


def chunk_json(path: Path) -> list[Chunk]:
    """Convert every deterministic JSON leaf into an exact key-path passage."""
    data = json.loads(path.read_text(encoding="utf-8"))
    source = _relative(path)
    chunks: list[Chunk] = []
    for key_path, value, context in _json_leaves(data):
        context_text = f" Context: {', '.join(dict.fromkeys(context))}." if context else ""
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        text = f"JSON metric at key path {key_path}.{context_text} Exact stored value: {rendered}."
        chunks.append(Chunk(source, key_path, text, "json"))
    return chunks


def build_corpus() -> list[Chunk]:
    """Build the complete allowlisted corpus in stable source order."""
    chunks: list[Chunk] = []
    for relative in PUBLIC_MARKDOWN:
        chunks.extend(chunk_markdown(ASTHMA_ROOT / relative))
    for relative in PUBLIC_JSON:
        chunks.extend(chunk_json(ASTHMA_ROOT / relative))
    return chunks


def write_manifest(path: Path) -> int:
    """Write an inspectable JSON Lines corpus manifest when explicitly requested."""
    chunks = build_corpus()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
    return len(chunks)
