# Artificial intelligence engineering learning roadmap

## Current position

I am currently at Lab 2 in the SuperDataScience artificial intelligence engineering online course. This is my reported progress; it is not a claim of course completion or certification.

I plan to join a six-month neue fische artificial intelligence engineering training program. The provider's current public page describes an eight-month full track and four-month modular entry points, so I will confirm the exact cohort schedule and modules with admissions before I present them as enrolled study.

## Public curriculum context

The [SuperDataScience public course catalog](https://www.superdatascience.com/courses) describes artificial intelligence engineering foundations, large language models, system design, and a second course focused on the Hugging Face ecosystem, models, datasets, Spaces, and experimentation. Detailed community course spaces are access-controlled. I used only the public descriptions and did not reproduce lab content.

The [neue fische public AI and machine-learning engineering page](https://www.neuefische.de/en/bootcamp/ai-and-machine-learning-engineering) describes a modular path spanning data foundations, machine learning, deep learning, generative artificial intelligence, data engineering, deployment, monitoring, and machine-learning operations. Public offerings and durations can change. No private curriculum or admissions material was accessed.

The repository's `learning/` directory contains only this roadmap and a short learning overview. No SuperDataScience course files or proprietary notebooks were found.

## Skill progression

### 1. Software and data foundations

- strengthen Python, typing, packaging, testing, and Git workflows;
- practise Structured Query Language, data validation, and reproducible data pipelines;
- document assumptions, schemas, missingness, and source provenance.

### 2. Machine-learning evaluation

- use baseline models before complex models;
- separate training, validation, and final test decisions;
- detect target leakage and perform feature selection inside resampling;
- report uncertainty, subgroup behavior, calibration, and failure cases.

### 3. Services and deployment

- expose a small model or retrieval system through FastAPI;
- add request validation, error handling, tests, and containerization;
- deploy to a controlled environment and document rollback and configuration.

### 4. Retrieval and generative systems

- compare lexical, semantic, and hybrid retrieval;
- add reranking and structured-data tools where exact lookup is required;
- evaluate answerability, citation faithfulness, refusal behavior, and latency;
- keep generated narration separate from authoritative calculations.

### 5. Operations and cloud fundamentals

- learn structured logging, metrics, traces, model and data versioning, and alerting;
- understand identity, secrets, least privilege, storage, networking, and cost controls;
- practise monitoring data quality, retrieval quality, drift, latency, and failures.

## Portfolio projects

### Local evidence assistant, evaluated extension

Extend the current assistant with hybrid retrieval, reranking, a paraphrase benchmark, citation-faithfulness review, and an optional hosted fallback with an explicit data boundary. Compare raw model behavior with complete system behavior and publish failure cases as well as successes.

### Asthma Version 3

Study daily PM2.5 and an acute asthma outcome using public Centers for Disease Control and Prevention or United States Environmental Protection Agency data, but only if compatible outcome data and temporal resolution exist. Pre-register lag windows and document the data gap rather than substituting annual prevalence for acute events.

### Production-style inference service

Build a small FastAPI service around a separate public dataset or model. Include schema validation, unit and integration tests, containerization, deployment, structured logs, health checks, latency metrics, and a short incident or rollback runbook.

These projects are planned work, not completed capabilities. I will update this roadmap as training details and evidence change.
