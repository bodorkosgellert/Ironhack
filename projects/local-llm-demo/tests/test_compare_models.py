from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from compare_models import CASES, compare, score_answer, strip_reasoning, write_results
from rag.ollama import OllamaStatus


class ComparisonScoringTests(unittest.TestCase):
    def test_exact_metric_requires_value_and_inline_citation(self) -> None:
        case = CASES[0]
        good = (
            "The exact Pearson correlation is -0.05726740504810031 "
            "[projects/asthma-air-pollution/v2/outputs/metrics.json — "
            "$.pearson_r_pm25_asthma]."
        )
        self.assertTrue(score_answer(case, good, refused=False)["passed"])
        self.assertFalse(
            score_answer(case, "The correlation is approximately -0.06.", refused=False)["passed"]
        )

    def test_causal_overstatement_fails(self) -> None:
        case = next(item for item in CASES if item.id == "ecological_causality")
        answer = (
            "This ecological analysis proves that PM2.5 causes asthma in individuals "
            "[projects/asthma-air-pollution/README.md — Research question]."
        )
        self.assertFalse(score_answer(case, answer, refused=False)["passed"])

    def test_reasoning_blocks_are_removed(self) -> None:
        text = "<think>private working</think>\nSupported answer."
        self.assertEqual(strip_reasoning(text), "Supported answer.")


class ComparisonFailureTests(unittest.TestCase):
    def test_unavailable_ollama_records_errors_without_chat_calls(self) -> None:
        calls = []

        def fail_if_called(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("chat should not be called")

        records = compare(
            ["missing:model"],
            limit=2,
            status_fn=lambda: OllamaStatus(False, error="connection refused"),
            chat_fn=fail_if_called,
        )
        self.assertEqual(len(records), 2)
        self.assertFalse(calls)
        self.assertTrue(all(not record["success"] for record in records))
        self.assertTrue(all("Ollama is unavailable" in record["error"] for record in records))

    def test_absent_model_records_errors_without_chat_calls(self) -> None:
        records = compare(
            ["missing:model"],
            limit=1,
            status_fn=lambda: OllamaStatus(True, ("installed:model",)),
            chat_fn=lambda *args, **kwargs: self.fail("chat should not be called"),
        )
        self.assertEqual(len(records), 1)
        self.assertFalse(records[0]["success"])
        self.assertIn("not installed", records[0]["error"])
        with TemporaryDirectory() as directory:
            csv_path, json_path = write_results(records, Path(directory) / "comparison.csv")
            self.assertTrue(csv_path.is_file())
            self.assertTrue(json_path.is_file())


class ComparisonModeTests(unittest.TestCase):
    def test_raw_and_assistant_modes_report_distinct_correctness(self) -> None:
        ollama = lambda: OllamaStatus(True, ("mock:model",))
        wrong_model = lambda *args, **kwargs: "The exact value is -0.99."

        raw = compare(
            ["mock:model"],
            limit=1,
            status_fn=ollama,
            chat_fn=wrong_model,
            mode="raw",
        )
        assistant = compare(
            ["mock:model"],
            limit=1,
            status_fn=ollama,
            chat_fn=wrong_model,
            mode="assistant",
        )

        self.assertEqual(raw[0]["evaluation_mode"], "raw")
        self.assertFalse(raw[0]["passed"])
        self.assertEqual(assistant[0]["evaluation_mode"], "assistant")
        self.assertTrue(assistant[0]["passed"])
        self.assertNotIn("-0.99", assistant[0]["answer"])


if __name__ == "__main__":
    unittest.main()
