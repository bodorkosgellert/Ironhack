# Local cited evidence assistant

I built this local retrieval-augmented generation (RAG) assistant to explain the existing public results of my Alabama asthma and fine particulate matter analysis. It retrieves traceable passages before answering and can use a local Ollama model without sending repository content to a hosted model. See the [model evaluation](MODEL_EVALUATION.md) for the verified raw-model and complete-assistant results.

The assistant is an explanatory layer over saved aggregate evidence. It does not modify data, rerun statistical scripts, produce new epidemiological estimates, or support causal conclusions.

This Streamlit app is **separate** from the Version 2 epidemiology dashboard in `projects/asthma-air-pollution/v2/streamlit_app.py`. The dashboard does not embed this assistant; use the live links or launch commands below for each app.

## Live demonstration

- [Evidence assistant (Q&A)](https://asthma-evidence-assistant.streamlit.app/)
- [County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/)
- [Assistant source on `main`](https://github.com/bodorkosgellert/ironhack-data-analytics/tree/main/projects/local-llm-demo)
- [Dashboard source on `main`](https://github.com/bodorkosgellert/ironhack-data-analytics/tree/main/projects/asthma-air-pollution/v2)

## Implemented capabilities

- evidence navigation across methods, literature, validation notes, and saved outputs;
- exact metric lookup from allowlisted JSON key paths;
- synonym / structural-intent routing for sample size, tract counts, and not-patient clarifications;
- deterministic source-path and locator citations;
- explanation of epidemiological limitations and outcome definitions;
- unsupported-geography refusal before generation;
- fixed retrieval, guardrail, and model-comparison benchmarks;
- optional local narration with deterministic fallback;
- optional hybrid lexical plus dense retrieval (`all-MiniLM-L6-v2`) when `sentence-transformers` is installed;
- optional hosted OpenAI-compatible chat via secrets when local Ollama is unreachable (for example on Streamlit Community Cloud).

## Practical use cases

Within this project, the assistant supports exact result lookup, reproducibility guidance, interpretation of ecological limitations, source inspection, local-model comparison, and guardrail testing. Local narration can remain offline. The indexed material here is public aggregate evidence rather than private patient data; see [Local inference and confidential health data](#local-inference-and-confidential-health-data) for how the same pattern applies to restricted corpora.

The same architecture could be adapted to compliance and policy lookup, quality manuals and standard operating procedures, financial-report metric lookup, scientific evidence synthesis, internal analytics documentation, or technical-support knowledge bases. Those are analogous examples, not features implemented here. In regulated, financial, scientific, or safety-sensitive settings, human review and the authoritative source remain necessary.

## Architecture

The implementation deliberately uses the repository's existing scikit-learn dependency for the default path rather than adding a framework or vector database. Dense embeddings are an optional local upgrade.

1. `rag/corpus.py` loads an explicit allowlist of public Markdown documentation and deterministic JavaScript Object Notation (JSON) outputs.
2. Markdown is divided along heading boundaries. Long sections use paragraph-aware chunks with a small overlap.
3. Every JSON leaf becomes stable text containing its exact key path, context label, and stored value.
4. `rag/retrieval.py` builds an in-memory term frequency-inverse document frequency (TF-IDF) index and ranks passages with cosine similarity. Optional dense scores from `all-MiniLM-L6-v2` can be fused for hybrid ranking.
5. `rag/metrics.py` routes recognised numeric and structural intents (including sample-size synonyms) to allowlisted JSON key paths or documented clarification passages, and loads metric values directly from the source files.
6. `rag/assistant.py` renders routed values and citations in application code before optional Ollama or hosted narration. Conflicting numeric narration is discarded.
7. `streamlit_app.py` and `rag/ask.py` expose the same assistant through graphical and command-line interfaces.

The TF-IDF index is rebuilt quickly in memory. Optional dense embeddings are cached under the ignored `.rag-cache/` directory. No machine-specific index is required in Git for the default path.

## Corpus boundary

I index only these public asthma artifacts:

- the project overview, literature review, roadmap, Version 1 retrospective notes, and Version 2 documentation;
- `metrics.json`, `multivariate_metrics.json`, `robustness_report.json`, and `feature_analysis.json`.

The allowlist excludes `docs/internal/`, repository archives, Version 1 notebook/original archive prose (`v1/ORIGINAL_README.md`), notebooks, comma-separated value files, generated caches, and all unrelated portfolio projects. Every retrieved chunk retains a repository-relative source path plus a Markdown heading or JSON key path.

Guardrail levels (L0–L7), including which are implemented now versus future work, are documented in [GUARDRAILS.md](GUARDRAILS.md).

## Scientific safeguards

The system prompt requires the local or hosted model to:

- answer only from retrieved context and cite the source file and locator;
- state that evidence is unavailable when the context is insufficient;
- narrate stored statistics without inventing or recomputing values;
- distinguish asthma prevalence, incidence, and acute exacerbations;
- avoid causal and individual-level claims from this county ecological study;
- report holdout and cross-validated metrics with appropriate uncertainty.

Prompt instructions are not the numeric safeguard. Deterministic metric routing is important because generation did not reliably preserve exact values. For example, a Pearson question loads the full stored value from `$.pearson_r_pm25_asthma`, while a PM2.5-only cross-validation question loads `$.models[0].r2_cv_mean`. Application code displays each exact value and source/key-path citation first. Optional narration may add clearly labelled interpretation, but it cannot replace the deterministic block; narration containing a conflicting numeric value is omitted. Hybrid search never bypasses exact metric routing or geography refusals.

## What this project demonstrates

I designed the assistant so deterministic evidence lookup and probabilistic language generation have separate responsibilities. Exact metrics and their citations come from stored JSON key paths and application code; a language model may narrate the retrieved evidence, but it cannot improve, rerun, or replace the epidemiological analysis. The interface refuses unsupported geographies before generation and adds retrieved source citations independently of model compliance.

The project also demonstrates practical local-model operations: consistent prompts and retrieval settings, bounded timeouts, automatic checks for numeric and citation compliance, and graceful fallback when Ollama or a requested model is unavailable. Local execution gives control over model availability and data flow. It is not presented as a privacy necessity for the current public corpus; see the confidential-health section below for the intended restricted-data use case.

My engineering contribution is the complete evidence boundary: corpus allowlisting, deterministic JSON routing, refusal behavior, composed answer rendering, fixed evaluation cases, failure recording, command-line and Streamlit interfaces, and documentation. Development provenance is documented in the repository's [AI-assisted development disclosure](../../AI_ASSISTED_DEVELOPMENT.md).

## Launch the assistant (Streamlit)

From the repository root in PowerShell, after creating and activating a virtual environment and installing `requirements.txt`:

```powershell
cd projects\local-llm-demo
streamlit run streamlit_app.py
```

Ollama must be running for local generation (`ollama serve`, or the Ollama desktop application). Pull the default chat model once:

```powershell
ollama pull qwen2.5-coder:3b
ollama list
```

The epidemiology dashboard is a different app:

```powershell
cd projects\asthma-air-pollution\v2
streamlit run streamlit_app.py
```

That dashboard does not currently embed the LLM assistant. Keep them separate and use the cross-links in each README.

## Windows setup

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Set-Location projects\local-llm-demo
```

The retrieval-only workflow does not need Ollama:

```powershell
python -m rag.ask --retrieval-only "What is the Pearson correlation between PM2.5 and asthma?"
python -m rag.ask --lexical-only --show-sources --top-k 5 "Why can this study not establish causality?"
```

I use [Ollama](https://ollama.com/download/windows) for optional local generation. Installation and model download are manual; the application never starts a multi-gigabyte download:

```powershell
ollama pull qwen2.5-coder:3b
ollama serve
ollama list
```

In a second PowerShell window:

```powershell
Set-Location projects\local-llm-demo
python -m rag.ask --model qwen2.5-coder:3b "What is the PM2.5-only cross-validated R²?"
streamlit run streamlit_app.py
```

If Ollama is stopped or the requested model is absent, both interfaces show setup guidance and continue with cited retrieval. If `HOSTED_LLM_*` secrets are configured, the assistant may use that OpenAI-compatible chat endpoint instead.

## Hybrid search

TF-IDF remains the default and the path used by unit tests. Optional dense retrieval uses the `sentence-transformers` model `all-MiniLM-L6-v2` for semantic paraphrases. Hybrid mode combines clipped TF-IDF and dense cosine scores with configurable weights (defaults: lexical `0.55`, dense `0.45`). Embeddings are cached under `.rag-cache/` (ignored by Git).

```powershell
py -m pip install -r requirements-hybrid.txt
python -m rag.ask --retrieval hybrid --retrieval-only --show-sources "Why can county associations not prove individual risk?"
python evaluate.py --retrieval tfidf
```

Environment variables: `RETRIEVAL_MODE`, `RETRIEVAL_LEXICAL_WEIGHT`, `RETRIEVAL_DENSE_WEIGHT`, `DENSE_EMBEDDING_MODEL`.

The first dense run may download model weights and needs network access. If `sentence-transformers` is missing, hybrid and dense modes fall back to TF-IDF with a status notice. I keep `sentence-transformers` out of the main repository `requirements.txt` so Streamlit Community Cloud stays lean; install `requirements-hybrid.txt` only on machines that need dense retrieval.

## Online hosting for GitHub visitors

The live [Evidence assistant (Q&A)](https://asthma-evidence-assistant.streamlit.app/) is deployed from `main`. It pairs with the [County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/).

Streamlit Community Cloud **cannot** reach Ollama on my Windows machine. Opening a deployed `streamlit_app.py` does **not** run local models on visitors' computers or on my personal computer. The cloud container runs the Python code on Streamlit's servers.

| Option | What visitors get | Notes |
|---|---|---|
| A. Retrieval-only on Streamlit Cloud | Deterministic metrics, citations, refusals | Already feasible with the public corpus; no generation |
| B. Streamlit Cloud + hosted chat secrets | Optional narration via OpenAI-compatible API | Set secrets below; never commit keys |
| C. Self-hosted backend elsewhere | Full control of Ollama or another runtime | Documented as a direction only; not provisioned in this repository |

### Streamlit Community Cloud secrets (optional hosted generation)

In the app settings, add:

```toml
HOSTED_LLM_API_KEY = "..."
HOSTED_LLM_BASE_URL = "https://api.groq.com/openai/v1"
HOSTED_LLM_MODEL = "llama-3.1-8b-instant"
```

Any OpenAI-compatible chat completions endpoint works (Groq free tier, OpenAI, and similar providers). Local Ollama remains preferred when available; without Ollama and without these secrets, the app stays retrieval-only.

Deploying this file to Streamlit Cloud does **not** mean “everyone runs my local `qwen2.5-coder:3b`.” Cloud without secrets equals retrieval-only (plus deterministic metric routing). Cloud with secrets equals retrieval plus that remote model, still constrained by the same citations and refusal rules.

## Local inference and confidential health data

The current demo corpus is **public aggregate** Centers for Disease Control and Prevention (CDC) PLACES county estimates for Alabama, joined with public environmental and documentation artifacts. It is **not** confidential individual health data. I do not claim that this 67-county dataset demonstrates patient confidentiality protection.

Local inference is still a relevant pattern when the corpus would be clinic notes, patient-level surveys, restricted registry extracts, or other Institutional Review Board (IRB)–bound materials that must not leave an institutional network. In those settings, benefits of a local (or privately hosted) retrieval-plus-generation design include data residency, avoiding third-party training exposure for prompts and passages, auditability of retrieval and prompts, and pairing generation with deterministic metric routing so stored numbers remain authoritative.

Limits remain: a local large language model is not Health Insurance Portability and Accountability Act (HIPAA) compliance by itself. Access control, encryption, logging, retention policy, and institutional governance still apply. Any future private corpus would need its own allowlist, evaluation, and legal review; this public demo does not substitute for that work.

## How to test the assistant

Run each command from `projects/local-llm-demo`.

1. **Retrieval-only smoke test:** this isolates corpus construction, exact metric routing, ranking, and citations from model behavior.

   ```powershell
   python -m rag.ask --retrieval-only --show-sources "What is the exact Pearson correlation between PM2.5 and asthma?"
   python -m rag.ask --retrieval-only "What is the specific PM2.5 effect estimate for California?"
   ```

2. **Generated-answer test:** choose an exact name reported by `ollama list`. For a routed metric, the application-owned authoritative block must contain the stored value and source/key-path citation even if narration is omitted. The `Retrieved citations` list is also generated from passage metadata rather than entrusted to the model.

   ```powershell
   python -m rag.ask --model <installed-model> --show-sources "What is the cross-validated R² for the PM2.5-only model?"
   ```

3. **Streamlit test:** first check existing terminals so that a second server is not started, then run `streamlit run streamlit_app.py` if needed. Test one metric question, one interpretation question, and the California refusal. Expand `Retrieved sources` and compare the answer with the quoted passages and JSON key paths. Use the sidebar to confirm Ollama, hosted-secret, and dense-embedding status.

4. **Unit and retrieval tests:**

   ```powershell
   python -m unittest discover -s tests -v
   python evaluate.py
   ```

   The fixed retrieval benchmark writes the ignored `outputs/benchmark.json`. A valid run should retrieve the expected path or locator and refuse the unsupported geography; it does not assess prose quality. Unit tests must pass without downloading MiniLM weights.

When reviewing an answer, verify the exact numeric string against the cited JSON leaf, check that every factual generated claim has an inline citation, and confirm that county-level associations are not described as individual or causal effects. For unsupported questions, the correct behavior is an explicit evidence refusal, not a fluent guess.

To report a failure reproducibly, include the exact command and question, operating system, Python and Ollama versions, exact model name from `ollama list`, relevant `ollama show <model>` output, timeout and top-k settings, whether Ollama's health endpoint responds, and the generated comparison row. Include available random-access memory (RAM) and processor or graphics hardware when reporting latency. Remove secrets and avoid attaching unrelated local data.

## Model evaluation

`compare_models.py` uses five fixed questions covering exact metrics, ecological causality, outcome definitions, and unsupported geography. `--mode raw` scores model output alone. `--mode assistant` scores the composed answer, including application-owned values, citations, and refusal behavior.

```powershell
ollama list
python compare_models.py --mode raw --models <model> --limit 5 --timeout 120 --output outputs/model_comparison_raw.csv
python compare_models.py --mode assistant --models <model> --limit 5 --timeout 120 --output outputs/model_comparison_assistant.csv
```

The verified results are 37/37 unit tests (plus hybrid fusion tests in the same suite), 16/16 deterministic retrieval cases, and 5/5 cases with 18/18 objective checks for the hardened Qwen assistant. On a longer raw comparison (`--timeout 360`, continue-on-error), Llama led complete cases (4/5) and objective checks (17/18), Qwen was fastest (3/5, 16/18), and DeepSeek passed only 1/5 complete cases. None of the raw models matched the assistant’s 5/5 / 18/18; that score is an architecture result, not raw-model superiority. Full methodology, timings, limitations, and reproducible commands are in [MODEL_EVALUATION.md](MODEL_EVALUATION.md). Generated reports remain ignored.

## Industry context and repository prevalence

Basic document-chat and RAG projects are common tutorial and beginner portfolio patterns. [GitHub RAG topic pages](https://github.com/topics/retrieval-augmented-generation-rag) show examples, but they do not provide a reliable denominator for all beginner repositories, so I do not claim a percentage. More substantive elements here are deterministic structured-data routing, refusal tests, citation checks, fixed benchmarks, raw-versus-system comparison, and explicit failure documentation.

This small project does not match enterprise scale, security, or operations. It does share architectural patterns with:

- [Azure AI Search](https://learn.microsoft.com/en-us/azure/app-service/tutorial-ai-openai-search-python), which documents hybrid retrieval and citation-backed RAG;
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-retrieve-generate.html), which returns generated responses with source references;
- [Google grounding with Agent Search](https://cloud.google.com/vertex-ai/generative-ai/docs/grounding/grounding-with-vertex-ai-search), which connects response segments to retrieved chunks;
- [Elastic RAG](https://www.elastic.co/docs/solutions/search/rag), which supports full-text, vector, and hybrid retrieval;
- [OpenAI file search](https://platform.openai.com/docs/guides/tools-file-search), which provides managed file retrieval and result annotations.

Across these systems, recurring patterns include retrieval, grounding, structured tools, citations, guardrails, evaluation, and observability.

## Limitations

- Term frequency-inverse document frequency retrieval recognises wording overlap, not deep semantic equivalence. Optional MiniLM hybrid search improves paraphrase recall but still depends on the small allowlisted corpus.
- The metric router covers the most important stored numeric intents but is not a general query language.
- The refusal threshold is a practical safeguard, not a calibrated probability of answerability.
- A language model can still produce poorly worded, unsupported, or incompletely cited non-numeric narration. The deterministic metric block and retrieved passages remain authoritative.
- The corpus covers one small, cross-sectional Alabama county study. It cannot provide other-state estimates, patient advice, individual risks, or causal effects.
- The source analysis has 67 counties, model-based Centers for Disease Control and Prevention PLACES outcomes, narrow PM2.5 exposure contrast, correlated predictors, and uncertain split-specific metrics.
- The generation harness checks exact, observable requirements but cannot prove that every sentence is entailed by its citation. A stronger evaluation would add blinded human review, a larger paraphrase benchmark, citation-entailment assessment, latency comparisons across machines, and interface accessibility testing.
- Hosted generation on Streamlit Community Cloud sends retrieved public passages to the configured provider. That is acceptable for this public corpus and inappropriate for confidential records unless a qualifying business associate agreement and institutional policy are in place.

## Cloud limitation

Streamlit Community Cloud cannot reach Ollama running on my local Windows machine. A cloud deployment therefore provides retrieval-only behavior unless Streamlit secrets supply a separately hosted OpenAI-compatible model. Secrets must never be committed to Git.

## Future work

I plan to expand paraphrase evaluation for hybrid retrieval, add reranking, strengthen citation-faithfulness review, and document a self-hosted backend path for institutions that cannot use third-party chat application programming interfaces. A production extension would add a FastAPI service, deployment checks, structured logging, latency monitoring, and access controls.
