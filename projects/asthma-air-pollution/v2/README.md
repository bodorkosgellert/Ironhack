# Version 2 technical runbook

This directory contains my reproducible county-level analysis for Alabama in 2023. It evaluates fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5. For scientific interpretation, start with the [project overview](../README.md) and [validation document](VALIDATION.md).

I developed Version 2 iteratively with Cursor's coding agent under my direction, review, and local verification. See the repository's [AI-assisted development disclosure](../../../AI_ASSISTED_DEVELOPMENT.md).

## Dashboard

Open the [County dashboard (charts)](https://alabama-asthma-pm25.streamlit.app/), or run it locally from this directory:

```bash
streamlit run streamlit_app.py
```

This dashboard does not embed the evidence assistant. For cited question answering over the public project corpus, open the [Evidence assistant (Q&A)](https://asthma-evidence-assistant.streamlit.app/) or run the separate app in [`projects/local-llm-demo`](https://github.com/bodorkosgellert/Ironhack/tree/main/projects/local-llm-demo) (`streamlit run streamlit_app.py` from that directory).

## Requirements

- Python 3.10 or later
- Dependencies listed in the repository-level `requirements.txt`
- Internet access for the initial public data download

From the repository root:

```bash
pip install -r requirements.txt
cd projects/asthma-air-pollution/v2
```

## Pipeline

Run the scripts in this order:

```bash
python download_data.py
python run_analysis.py
python run_multivariate.py
python run_robustness.py
python run_feature_analysis.py
```

| Script | Function |
|---|---|
| `download_data.py` | Downloads Centers for Disease Control and Prevention PLACES estimates and Open-Meteo PM2.5 estimates, then builds county-level files |
| `run_analysis.py` | Fits univariate PM2.5 models and creates the main scatter plot |
| `run_multivariate.py` | Calculates partial correlations and compares random forest specifications |
| `run_robustness.py` | Runs bootstrap, permutation, and leave-one-out checks |
| `run_feature_analysis.py` | Calculates exposure spread, holdout permutation importance, residuals, and exploratory feature selection |

The download generally takes one to three minutes. The remaining scripts normally finish within seconds.

## Inputs and outputs

The pipeline creates:

- `outputs/alabama_counties_full.csv`
- `outputs/alabama_counties_merged.csv`
- `outputs/metrics.json`
- `outputs/multivariate_metrics.json`
- `outputs/robustness_report.json`
- `outputs/feature_analysis.json`
- `outputs/county_residuals_confounders_only.csv`
- figures under `figures/`

The current predictors are PM2.5, smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity prevalence, and binge drinking prevalence. Access to care and urbanicity are not included.

## Dashboard behavior

The dashboard reads precomputed comma-separated value and JavaScript Object Notation files. It does not train models or call external application programming interfaces during display. If a figure is missing, rerun the corresponding analysis script.

## Metric guidance

- `r2_test` is performance on a holdout of approximately 17 counties.
- `r2_cv_mean` is mean five-fold cross-validated performance and is more informative than one split, although 67 counties remain a small sample.
- Negative R² means performance was worse than predicting the target mean on the evaluated data.
- `mae_test` is holdout mean absolute error.

## Related documentation

- [`VALIDATION.md`](VALIDATION.md): evidence, uncertainty, and limitations
- [`FEATURE_ANALYSIS.md`](FEATURE_ANALYSIS.md): feature-analysis methods and caveats
- [`../LITERATURE.md`](../LITERATURE.md): literature comparison
- [`../ROADMAP.md`](../ROADMAP.md): planned scientific extensions
