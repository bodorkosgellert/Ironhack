from __future__ import annotations

import unittest

from rag.assistant import EvidenceAssistant
from rag.corpus import PUBLIC_JSON, PUBLIC_MARKDOWN, build_corpus
from rag.metrics import exact_metric_chunks
from rag.ollama import OllamaStatus
from rag.retrieval import LexicalRetriever


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chunks = build_corpus()

    def test_allowlist_contains_only_public_markdown_and_json(self) -> None:
        expected = {f"projects/asthma-air-pollution/{path}" for path in PUBLIC_MARKDOWN + PUBLIC_JSON}
        sources = {chunk.source for chunk in self.chunks}
        self.assertEqual(sources, expected)
        self.assertFalse(any("docs/internal" in source or "archive/" in source for source in sources))
        self.assertFalse(any(source.endswith((".csv", ".ipynb")) for source in sources))

    def test_markdown_is_chunked_by_heading(self) -> None:
        validation = [
            chunk for chunk in self.chunks
            if chunk.source.endswith("v2/VALIDATION.md") and chunk.kind == "markdown"
        ]
        self.assertGreater(len(validation), 5)
        self.assertTrue(any("PM2.5-only evidence" in chunk.locator for chunk in validation))
        self.assertTrue(all(chunk.text.strip() for chunk in validation))

    def test_json_chunks_retain_exact_key_paths(self) -> None:
        matches = [
            chunk for chunk in self.chunks
            if chunk.source.endswith("outputs/metrics.json")
            and chunk.locator == "$.pearson_r_pm25_asthma"
        ]
        self.assertEqual(len(matches), 1)
        self.assertIn("-0.05726740504810031", matches[0].text)


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retriever = LexicalRetriever()
        cls.assistant = EvidenceAssistant(retriever=cls.retriever)

    def test_retrieval_is_deterministic(self) -> None:
        question = "What are the ecological limitations?"
        first = self.retriever.search(question)
        second = self.retriever.search(question)
        self.assertEqual(
            [(item.chunk.source, item.chunk.locator, item.score) for item in first.passages],
            [(item.chunk.source, item.chunk.locator, item.score) for item in second.passages],
        )

    def test_exact_pearson_metric_lookup(self) -> None:
        question = "What is the Pearson correlation between PM2.5 and asthma?"
        chunks = exact_metric_chunks(question, self.retriever.chunks)
        self.assertEqual(chunks[0].locator, "$.pearson_r_pm25_asthma")
        answer = self.assistant.ask(question, retrieval_only=True)
        self.assertIn("-0.05726740504810031", answer.text)
        self.assertIn("metrics.json — $.pearson_r_pm25_asthma", answer.text)

    def test_cross_validated_pm25_metric_is_negative(self) -> None:
        answer = self.assistant.ask(
            "What is the cross-validated R² for the PM2.5-only model?",
            retrieval_only=True,
        )
        self.assertIn("-0.321694185275063", answer.text)
        self.assertIn("$.models[0].r2_cv_mean", answer.text)

    def test_causality_question_retrieves_ecological_context(self) -> None:
        result = self.retriever.search("Does this prove PM2.5 causes asthma in individuals?")
        combined = " ".join(item.chunk.text.lower() for item in result.passages)
        self.assertFalse(result.refused)
        self.assertTrue("causal" in combined or "individual" in combined)

    def test_outside_geography_refuses(self) -> None:
        answer = self.assistant.ask(
            "What is the specific PM2.5 effect estimate for California?",
            retrieval_only=True,
        )
        self.assertTrue(answer.refused)
        self.assertIn("does not answer", answer.text)
        self.assertIn("California", answer.text)

    def test_low_score_refuses(self) -> None:
        result = self.retriever.search("quantum chromodynamics supersymmetry")
        self.assertTrue(result.refused)

    def test_every_returned_passage_has_citation_metadata(self) -> None:
        result = self.retriever.search("What are the study limitations?")
        self.assertTrue(result.passages)
        for item in result.passages:
            self.assertTrue(item.chunk.source)
            self.assertTrue(item.chunk.locator)
            self.assertIn(" — ", item.citation)


class GeneratedAnswerCompositionTests(unittest.TestCase):
    MODEL = "mock:model"

    def setUp(self) -> None:
        self.calls: list[str] = []

    def assistant(self, response: str) -> EvidenceAssistant:
        def mocked_chat(*args, **kwargs) -> str:
            self.calls.append(args[0])
            return response

        return EvidenceAssistant(
            status_fn=lambda: OllamaStatus(True, (self.MODEL,)),
            chat_fn=mocked_chat,
        )

    def test_exact_pearson_and_citation_override_wrong_model_number(self) -> None:
        answer = self.assistant("The Pearson correlation is -0.99.").ask(
            "What is the exact Pearson correlation between PM2.5 and asthma?",
            model=self.MODEL,
        )
        self.assertIn("-0.05726740504810031", answer.text)
        self.assertIn("metrics.json — $.pearson_r_pm25_asthma", answer.text)
        self.assertNotIn("-0.99", answer.text)
        self.assertIn("omitted", answer.notice or "")

    def test_exact_cross_validated_r2_survives_model_omission(self) -> None:
        answer = self.assistant("The retrieved evidence indicates weak predictive performance.").ask(
            "What is the cross-validated R² for the PM2.5-only model?",
            model=self.MODEL,
        )
        self.assertIn("-0.321694185275063", answer.text)
        self.assertIn("$.models[0].r2_cv_mean", answer.text)
        self.assertIn("Optional model interpretation", answer.text)

    def test_citations_are_appended_when_model_omits_them(self) -> None:
        answer = self.assistant("This is an ecological county-level analysis.").ask(
            "Does this study prove that PM2.5 causes asthma in individuals?",
            model=self.MODEL,
        )
        self.assertIn("Retrieved citations:", answer.text)
        self.assertIn("projects/asthma-air-pollution/", answer.text)

    def test_unsupported_geography_bypasses_generation(self) -> None:
        answer = self.assistant("This must never be returned.").ask(
            "What is the specific PM2.5 effect estimate for California?",
            model=self.MODEL,
        )
        self.assertTrue(answer.refused)
        self.assertFalse(answer.generation_used)
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
