# Local model and assistant evaluation

This document separates raw local-model behavior from the behavior of the complete evidence assistant. The distinction matters: deterministic application code, not the language model, owns exact metric lookup, source-path rendering, and unsupported-geography refusal.

## Method

`compare_models.py` uses five fixed questions:

1. exact Pearson correlation;
2. PM2.5-only cross-validated R²;
3. ecological causality;
4. prevalence, incidence, and acute-exacerbation distinctions;
5. an unsupported California estimate.

Retrieval, prompt construction, top-k (`5`), temperature (`0`), and response cap are held constant. Raw mode scores only the model's generated text. Assistant mode scores the complete user-facing answer after deterministic routing and citation rendering. The California case refuses before generation in both modes, so it tests a shared application boundary rather than model quality.

The scoring code applies 18 observable checks across the five cases. Checks cover expected refusal behavior, exact stored numeric values, required citation strings, required terminology, and absence of specified causal overstatements. It uses no model judge. A case passes only when all checks assigned to it pass.

## Verified results

### Raw model comparison

The following figures come from the latest direct local command. Total time is the sum of recorded model-call latency in that run; skipped rows have no latency.

| Model | Complete cases | Objective checks | Total recorded time | Recorded errors |
|---|---:|---:|---:|---:|
| `qwen2.5-coder:3b` | 1/5 | 14/18 | 24,768.21 ms | 0 |
| `llama3.1:latest` | 0/5 | 0/0 completed checks | 120,223.58 ms | 5 |
| `deepseek-r1:7b` | 0/5 | 0/0 completed checks | 120,546.91 ms | 5 |

Qwen completed all five cases, including four generations and one pre-generation refusal, but did not reliably preserve exact numerical strings or place the required citations in its answer. Its only complete pass was the application-owned unsupported-geography refusal. Llama and DeepSeek timed out or failed on their first generated case; bounded failure handling recorded that failure and skipped the remaining four cases, producing five error records for each model.

An earlier bounded comparison also found Qwen faster and relatively better at citation compliance than the other installed models. The latest direct command above is the public comparison because it is the most recent controlled run.

### Hardened assistant comparison

| Configuration | Complete cases | Objective checks | Errors |
|---|---:|---:|---:|
| Evidence assistant with optional `qwen2.5-coder:3b` narration | 5/5 | 18/18 | 0 |

This is an assistant architecture result, not evidence that raw Qwen achieved 5/5. For recognised metric questions, application code loads authoritative values from allowlisted JSON files by exact key path and renders the value and citation. Generated prose is optional and is omitted if it introduces a conflicting number. Unsupported geography refuses before any model call.

The deterministic retrieval benchmark separately passed 12/12 fixed cases, and the hardened unit suite passed 20/20 tests.

## Interpretation

The raw local models tested here were unreliable authorities for exact values and citation compliance. Qwen is therefore used only for optional narration. It does not calculate, improve, or replace the epidemiological model.

The complete assistant has a narrower responsibility split:

- retrieval locates public methods, literature, and output evidence;
- structured routing resolves recognised numeric questions to JSON key paths;
- application code renders exact values and citations;
- refusal logic blocks unsupported geography before generation;
- optional prose may explain retrieved evidence but cannot replace or contradict routed values.

The 5/5 assistant result validates these fixed observable cases. It does not prove general factual accuracy, citation entailment, robustness to arbitrary paraphrases, or suitability for clinical decisions.

## Reproduction

Run from `projects/local-llm-demo`:

```powershell
python -m unittest discover -s tests -v
python evaluate.py
python compare_models.py --mode raw --models qwen2.5-coder:3b llama3.1:latest deepseek-r1:7b --limit 5 --timeout 120 --output outputs/model_comparison_raw.csv
python compare_models.py --mode assistant --models qwen2.5-coder:3b --limit 5 --timeout 120 --output outputs/model_comparison_assistant.csv
```

The comparison commands require the named Ollama models. They should not be rerun merely to reproduce this document when local hardware or time limits differ. Unit tests and the deterministic benchmark do not require Ollama.

Verbose benchmark and model-comparison outputs under `outputs/` are generated evidence and remain ignored by Git. This document is the curated public summary.

## Limitations and next evaluation steps

- The benchmark has five model-comparison cases and twelve retrieval cases from one small project.
- Objective string checks are transparent but cannot establish that every sentence is supported by its cited passage.
- Latency is specific to one local machine and run; it is not a general model benchmark.
- A timeout is evidence about this configuration and hardware, not an intrinsic judgment of a model family.
- Future evaluation should add paraphrase sets, hybrid retrieval, reranking, citation-faithfulness review, repeated latency measurements, and optional hosted-model fallback testing.

Reasoning-model `<think>` and `<analysis>` blocks are removed from public output. The evaluation records final observable answers and check results; it does not expose hidden chain-of-thought.
