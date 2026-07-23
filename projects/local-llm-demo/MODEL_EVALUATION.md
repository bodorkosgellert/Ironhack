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

The following figures come from the latest direct local command (`--timeout 360`, `--continue-on-error`). Total time is the sum of recorded model-call latency in that run. **Complete cases** means every objective check for that question passed (not merely that the model finished generating).

| Model | Complete cases | Objective checks | Total recorded time | Recorded errors |
|---|---:|---:|---:|---:|
| `qwen2.5-coder:3b` | 3/5 | 16/18 | 54,241.79 ms | 0 |
| `llama3.1:latest` | 4/5 | 17/18 | 144,517.88 ms | 0 |
| `deepseek-r1:7b` | 1/5 | 7/18 | 173,867.50 ms | 0 |

With a 360-second per-call budget, all three models finished every case without transport timeouts (wall clock for the full comparison was about 6.5 minutes). Llama scored highest on raw complete-case and objective-check counts. Qwen was fastest and strong on interpretation/refusal cases, but missed exact Pearson / outcome citation checks on this run. DeepSeek finished slowly and passed only the application-owned unsupported-geography refusal as a complete case; its generated answers usually missed exact numeric strings, required citations, or terminology checks.

An earlier run with `--timeout 120` and stop-on-first-error made Llama and DeepSeek look like total failures (5 recorded errors each) because the first generated call hit the time limit and remaining cases were skipped. That was a hardware/timeout budget effect, not proof that those models cannot answer. The 360-second continue-on-error run above is now the public raw comparison.

### Hardened assistant comparison

| Configuration | Complete cases | Objective checks | Errors |
|---|---:|---:|---:|
| Evidence assistant with optional `qwen2.5-coder:3b` narration | 5/5 | 18/18 | 0 |

This is an assistant architecture result, not evidence that raw Qwen achieved 5/5. For recognised metric questions, application code loads authoritative values from allowlisted JSON files by exact key path and renders the value and citation. Generated prose is optional and is omitted if it introduces a conflicting number. Unsupported geography refuses before any model call.

The deterministic retrieval benchmark separately passed 16/16 fixed cases on the default TF-IDF path. The unit suite covers corpus construction, retrieval, structural synonym routing, answer composition, hybrid score fusion, and graceful fallback when `sentence-transformers` is absent. Those unit tests do not download MiniLM weights.

## Interpretation

Even when they finish, raw local models remain unreliable authorities for exact stored values and citation compliance (none reached 5/5 or 18/18 on this harness). Qwen remains the default optional narrator because it is much faster on this machine; Llama’s higher raw score does not replace application-owned metric routing. No model calculates, improves, or replaces the epidemiological analysis.

### What sets these models apart on this harness

The five cases share the same retrieved context and prompts, so score gaps are not from different document pools. They track a few concrete model features against the **density and strictness** of the task:

| Feature | Why it mattered here |
|---|---|
| **Parameter scale / download size** | `qwen2.5-coder:3b` (~1.9 GB) vs `llama3.1:latest` (~4.9 GB) vs `deepseek-r1:7b` (~4.7 GB). Larger Llama capacity helped on exact-number and citation checks once the time budget allowed a full answer. |
| **Latency vs completeness** | Same top-k passages and a hard response-length cap. Qwen finished generations in ~10–19 s; Llama often ~15–88 s; DeepSeek ~40–51 s. Under a short timeout, the slower models looked “broken”; with 360 s they were comparable on wall-clock success but not on quality. |
| **Reasoning overhead** | DeepSeek R1-style models spend tokens on internal deliberation before the final answer. For a **high-density, low-ambiguity** task (paste the exact float and citation path from the prompt), that extra scope adds latency without improving objective string checks—and can bury the required literal. |
| **Task complexity fit** | Cases split into (a) **exact metric copy** (Pearson, CV R²), (b) **constrained explanation** (ecological / outcome definitions), (c) **app-owned refusal** (California). Llama led (a)+(b) when allowed to finish; all models can “pass” (c) without generating because the application refuses first. |
| **Evidence density in the prompt** | Each generation sees several retrieved chunks plus instructions to cite paths and keep numbers exact. That is a **narrow, dense** instruction surface: models that paraphrase freely lose points even when the prose is sensible. The assistant mode removes that failure mode by rendering JSON metrics in application code. |

In short: on this portfolio corpus, **scope is small and checks are literal**. The differentiating feature set is not “who knows more medicine,” but **size/speed trade-off**, **whether the model over-elaborates**, and **obedience to dense citation/number constraints**. That is why the hardened assistant still uses Qwen only for optional narration and keeps metric authority outside the model.

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
python evaluate.py --retrieval tfidf
python compare_models.py --mode raw --models qwen2.5-coder:3b llama3.1:latest deepseek-r1:7b --limit 5 --timeout 360 --continue-on-error --output outputs/model_comparison_raw_timeout360.csv
python compare_models.py --mode assistant --models qwen2.5-coder:3b --limit 5 --timeout 120 --output outputs/model_comparison_assistant.csv
```

Optional hybrid retrieval (requires `pip install -r requirements-hybrid.txt` and a one-time MiniLM download):

```powershell
python evaluate.py --retrieval hybrid
python -m rag.ask --retrieval hybrid --retrieval-only --show-sources "Why can county associations not prove individual risk?"
```

The comparison commands require the named Ollama models. They should not be rerun merely to reproduce this document when local hardware or time limits differ. Unit tests and the default TF-IDF benchmark do not require Ollama or MiniLM downloads.

Verbose benchmark and model-comparison outputs under `outputs/` are generated evidence and remain ignored by Git. This document is the curated public summary.

## Limitations and next evaluation steps

- The benchmark has five model-comparison cases and twelve retrieval cases from one small project.
- Objective string checks are transparent but cannot establish that every sentence is supported by its cited passage.
- Latency is specific to one local machine and run; it is not a general model benchmark.
- A timeout is evidence about this configuration and hardware, not an intrinsic judgment of a model family.
- Hybrid TF-IDF plus `all-MiniLM-L6-v2` retrieval is implemented as an optional path; published objective scores in this document still refer to the TF-IDF assistant configuration unless a new controlled run is recorded.
- Future evaluation should add larger paraphrase sets, reranking, citation-faithfulness review, repeated latency measurements, and hosted-model fallback testing with the same objective checks.

Reasoning-model `<think>` and `<analysis>` blocks are removed from public output. The evaluation records final observable answers and check results; it does not expose hidden chain-of-thought.
