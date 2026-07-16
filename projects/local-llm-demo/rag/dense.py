"""Optional dense embeddings with sentence-transformers (offline after first download)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .corpus import Chunk
from .textnorm import search_text

DEFAULT_DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".rag-cache"


@dataclass(frozen=True)
class DenseStatus:
    available: bool
    model_name: str = DEFAULT_DENSE_MODEL
    loaded: bool = False
    error: str | None = None


def sentence_transformers_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def dense_status(model_name: str = DEFAULT_DENSE_MODEL) -> DenseStatus:
    if not sentence_transformers_available():
        return DenseStatus(
            False,
            model_name,
            error="sentence-transformers is not installed; lexical retrieval remains available.",
        )
    return DenseStatus(True, model_name)


def _corpus_fingerprint(chunks: list[Chunk], model_name: str) -> str:
    digest = hashlib.sha256()
    digest.update(model_name.encode("utf-8"))
    for chunk in chunks:
        digest.update(chunk.source.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.locator.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk.text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


class DenseIndex:
    """Cosine similarity over MiniLM embeddings, with disk cache under `.rag-cache/`."""

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        model_name: str = DEFAULT_DENSE_MODEL,
        cache_dir: Path | None = None,
    ):
        if not sentence_transformers_available():
            raise ImportError(
                "sentence-transformers is required for dense retrieval. "
                "Install with: pip install sentence-transformers"
            )
        from sentence_transformers import SentenceTransformer

        self.chunks = chunks
        self.model_name = model_name
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = SentenceTransformer(model_name)
        self.matrix = self._load_or_encode()

    def _cache_paths(self) -> tuple[Path, Path]:
        fingerprint = _corpus_fingerprint(self.chunks, self.model_name)
        stem = self.cache_dir / f"minilm-{fingerprint}"
        return stem.with_suffix(".npy"), stem.with_suffix(".meta.json")

    def _load_or_encode(self) -> np.ndarray:
        npy_path, meta_path = self._cache_paths()
        if npy_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("model_name") == self.model_name and meta.get("n_chunks") == len(self.chunks):
                    matrix = np.load(npy_path)
                    if matrix.shape[0] == len(self.chunks):
                        return matrix
            except (OSError, ValueError, json.JSONDecodeError):
                pass

        texts = [
            search_text(f"{chunk.source} {chunk.locator} {chunk.text}")
            for chunk in self.chunks
        ]
        matrix = np.asarray(
            self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )
        np.save(npy_path, matrix)
        meta_path.write_text(
            json.dumps(
                {
                    "model_name": self.model_name,
                    "n_chunks": len(self.chunks),
                    "dim": int(matrix.shape[1]) if matrix.ndim == 2 else 0,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return matrix

    def scores(self, question: str) -> np.ndarray:
        query = np.asarray(
            self._model.encode(
                [search_text(question)],
                normalize_embeddings=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )[0]
        return self.matrix @ query
