from __future__ import annotations

import unittest
from unittest.mock import patch

from rag.dense import dense_status, sentence_transformers_available
from rag.fusion import (
    clip_unit_interval,
    fuse_weighted_scores,
    normalize_scores,
    reciprocal_rank_fusion,
)
from rag.hosted import HostedLLMConfig, load_hosted_config
from rag.retrieval import HybridRetriever, make_retriever


class FusionMathTests(unittest.TestCase):
    def test_normalize_scores_minmax(self) -> None:
        normalized = normalize_scores({0: 0.2, 1: 0.4, 2: 0.6})
        self.assertAlmostEqual(normalized[0], 0.0)
        self.assertAlmostEqual(normalized[1], 0.5)
        self.assertAlmostEqual(normalized[2], 1.0)
        self.assertEqual(normalize_scores({0: 0.3, 1: 0.3}), {0: 0.0, 1: 0.0})
        self.assertEqual(normalize_scores({}), {})

    def test_clip_unit_interval(self) -> None:
        self.assertEqual(clip_unit_interval({0: -0.2, 1: 0.5, 2: 1.7}), {0: 0.0, 1: 0.5, 2: 1.0})

    def test_weighted_fusion_preserves_absolute_scale(self) -> None:
        fused = fuse_weighted_scores(
            {0: 0.8, 1: 0.1},
            {0: 0.2, 1: 0.9},
            lexical_weight=0.5,
            dense_weight=0.5,
        )
        self.assertAlmostEqual(fused[0], 0.5)
        self.assertAlmostEqual(fused[1], 0.5)

    def test_weighted_fusion_rejects_invalid_weights(self) -> None:
        with self.assertRaises(ValueError):
            fuse_weighted_scores({0: 1.0}, {0: 1.0}, lexical_weight=0.0, dense_weight=0.0)
        with self.assertRaises(ValueError):
            fuse_weighted_scores({0: 1.0}, {0: 1.0}, lexical_weight=-1.0, dense_weight=1.0)

    def test_reciprocal_rank_fusion_order(self) -> None:
        fused = reciprocal_rank_fusion([[0, 1, 2], [1, 0, 2]], rank_constant=60)
        self.assertGreater(fused[1], fused[2])
        self.assertGreater(fused[0], fused[2])


class HybridFallbackTests(unittest.TestCase):
    def test_make_retriever_defaults_to_tfidf(self) -> None:
        retriever = make_retriever("tfidf")
        self.assertEqual(retriever.effective_mode, "tfidf")
        result = retriever.search("What are the ecological limitations?")
        self.assertFalse(result.refused)
        self.assertEqual(result.mode, "tfidf")

    def test_hybrid_falls_back_when_sentence_transformers_missing(self) -> None:
        with patch("rag.dense.sentence_transformers_available", return_value=False):
            retriever = HybridRetriever(mode="hybrid")
            self.assertFalse(retriever.dense_loaded)
            self.assertEqual(retriever.effective_mode, "tfidf")
            result = retriever.search("What is the Pearson correlation between PM2.5 and asthma?")
            self.assertFalse(result.refused)
            self.assertIn("sentence-transformers", result.notice or "")

    def test_dense_status_without_package(self) -> None:
        with patch("rag.dense.sentence_transformers_available", return_value=False):
            status = dense_status()
            self.assertFalse(status.available)
            self.assertIn("not installed", status.error or "")

    def test_low_score_still_refuses_in_hybrid_fallback(self) -> None:
        with patch("rag.dense.sentence_transformers_available", return_value=False):
            retriever = HybridRetriever(mode="hybrid")
            result = retriever.search("quantum chromodynamics supersymmetry")
            self.assertTrue(result.refused)

    def test_geography_refusal_not_bypassed_by_hybrid_mode(self) -> None:
        with patch("rag.dense.sentence_transformers_available", return_value=False):
            retriever = HybridRetriever(mode="hybrid")
            result = retriever.search("What is the specific PM2.5 effect estimate for California?")
            self.assertTrue(result.refused)
            self.assertIn("California", result.reason or "")


class HostedConfigTests(unittest.TestCase):
    def test_load_hosted_config_from_mapping(self) -> None:
        config = load_hosted_config(
            {
                "HOSTED_LLM_API_KEY": "test-key",
                "HOSTED_LLM_BASE_URL": "https://api.groq.com/openai/v1",
                "HOSTED_LLM_MODEL": "llama-3.1-8b-instant",
            }
        )
        self.assertIsInstance(config, HostedLLMConfig)
        assert config is not None
        self.assertEqual(config.model, "llama-3.1-8b-instant")
        self.assertTrue(config.configured)

    def test_load_hosted_config_requires_key_and_model(self) -> None:
        self.assertIsNone(load_hosted_config({"HOSTED_LLM_API_KEY": "only-key"}))
        self.assertIsNone(load_hosted_config({}))


class SentenceTransformersProbeTests(unittest.TestCase):
    def test_probe_returns_bool(self) -> None:
        self.assertIsInstance(sentence_transformers_available(), bool)


if __name__ == "__main__":
    unittest.main()
