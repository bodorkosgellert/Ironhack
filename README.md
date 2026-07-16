# Ironhack data analytics portfolio

This repository brings together my Ironhack Data Analytics bootcamp work from 2021 and selected later learning projects. I reorganized the material in 2026 so that the current work is easy to navigate while the original submissions remain available unchanged.

## Project map

| Area | Description |
|---|---|
| [`projects/asthma-air-pollution/`](projects/asthma-air-pollution/) | Fine particulate matter and adult asthma prevalence: [Live demo](https://ironhack-fk9xtt3fmoama8fdpvbzj.streamlit.app/) · [Source](projects/asthma-air-pollution/v2/) |
| [`projects/local-llm-demo/`](projects/local-llm-demo/) | A local cited evidence assistant with deterministic metric routing and model evaluation |
| [`learning/`](learning/) | Notes and a roadmap for my continuing technical education |
| [`labs/`](labs/) | Selected classroom exercises in Python, Structured Query Language, natural language processing, and computer vision |
| [`archive/bootcamp-original/`](archive/bootcamp-original/) | The original bootcamp upload, preserved without editorial changes |

## Featured project

In the asthma and air pollution project, I ask whether annual mean fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5, predicts model-based adult asthma prevalence across Alabama counties.

Version 2 uses 67 counties, a reproducible county key, Centers for Disease Control and Prevention PLACES estimates, and Open-Meteo air-quality estimates. The raw Pearson correlation is approximately negative 0.06. A random forest achieved holdout R² near 0.03 in one split, but its cross-validated R² was negative. I therefore interpret PM2.5 as a poor out-of-sample county-level predictor in the current data, not as biologically irrelevant.

Read the [project overview](projects/asthma-air-pollution/README.md) for the research question, results, limitations, and reproduction steps.

The companion [local evidence assistant](projects/local-llm-demo/) provides cited navigation across the project's public methods, literature, and saved outputs. Its [evaluation](projects/local-llm-demo/MODEL_EVALUATION.md) distinguishes unreliable raw model generation from hardened assistant behavior.

## Development provenance

Version 1 reflects my original bootcamp work. The 2026 restructuring, Version 2, dashboard, documentation, and local evidence assistant were developed iteratively with Cursor's coding agent under my direction and review. See the [AI-assisted development disclosure](AI_ASSISTED_DEVELOPMENT.md) for the division of responsibility and verification approach.

## Archive policy

I keep `archive/bootcamp-original/` as a historical record of the files originally uploaded after the bootcamp. Curated copies and retrospective corrections are located elsewhere in the repository. The preserved archive may contain terminology or methods that I would describe differently today.

## Reuse and attribution

Some laboratory materials reflect Ironhack coursework. The repository distinguishes original bootcamp work from later AI-assisted development. Paid or proprietary course content should not be redistributed from this repository.
