# Local language model document search experiment

This directory describes a planned experiment in local document retrieval and generation. I intend to index the public documentation in this repository, retrieve relevant passages for a question, and generate an answer with source references without sending the documents to a hosted model.

## Objective

I will build and evaluate a retrieval-augmented generation workflow using a local large language model. The evaluation will cover retrieval quality, response latency, context size, and answer traceability.

## Proposed implementation

1. Run a compact model through [Ollama](https://ollama.com/).
2. Divide the public asthma project documentation into identifiable passages.
3. Create local embeddings with `nomic-embed-text`.
4. Store and retrieve vectors with either Chroma or its LangChain integration.
5. Provide a command-line query interface with passage references.
6. Evaluate a fixed set of questions and record latency, retrieved passages, and answer length.
7. Add a Streamlit interface after the command-line workflow is reliable.

## Intended outputs

| Output | Purpose |
|---|---|
| `data/chunks.jsonl` | Traceable document passages |
| `rag/index.py` | Local indexing workflow |
| `rag/ask.py` | Retrieval and generation command |
| `outputs/benchmark.csv` | Repeatable quality and latency measurements |
| `streamlit_app.py` | Optional interactive interface |

## Boundaries

This is a project plan, not a completed benchmark. Fine-tuning, multi-agent orchestration, and claims of equivalence to large hosted models are outside the current scope. No private working notes are included in the retrieval corpus.
