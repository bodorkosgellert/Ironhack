# Asthma prevalence and air pollution

I began this project as my 2021 Ironhack capstone and rebuilt it in 2026 to make the data integration reproducible and the scientific interpretation more careful.

## Research question

I ask whether annual mean fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5, is associated with current adult asthma prevalence across Alabama counties.

This is an ecological, cross-sectional analysis. Its unit is a county, not a person. It can describe county-level patterns and predictive performance, but it cannot estimate an individual causal effect.

## Project versions

| Version | Purpose |
|---|---|
| [Version 1](v1/) | My original 2021 exploratory analysis, with a separate retrospective correction |
| [Version 2](v2/) | My 2026 reproducible county-level pipeline |

The original 2021 write-up remains unchanged in [`v1/ORIGINAL_README.md`](v1/ORIGINAL_README.md). I document corrections without altering that historical record.

## Version 2 data

Version 2 contains one row for each of Alabama's 67 counties.

- The outcome is the Centers for Disease Control and Prevention (CDC) PLACES model-based estimate of current adult asthma prevalence, identified by `CASTHMA`.
- The exposure is Open-Meteo annual mean PM2.5 at each county centroid.
- The correlated county health indicators are smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity prevalence, and binge drinking prevalence.
- Counties are joined with Federal Information Processing Standards (FIPS) codes.

Version 2 does not include access to care or urbanicity.

## Main result

The raw Pearson correlation between PM2.5 and asthma prevalence is approximately negative 0.06. In one holdout split, a PM2.5-only random forest produced R² near 0.03. Cross-validated R² is negative in the current outputs, indicating poor out-of-sample performance. Negative R² means the model performed worse than predicting the target mean on the evaluated data.

The five county health indicators fit asthma prevalence much more closely. Their random forest produced holdout R² near 0.86 and mean cross-validated R² near 0.76. Obesity alone correlates with asthma at approximately 0.86.

I interpret those large values cautiously. Asthma and all five indicators are model-based CDC PLACES estimates derived through related source methodology. Strong fit can reflect shared source structure and correlated population-health patterns. It is not causal evidence. The holdout contains approximately 17 counties from only 67 total counties, so its metrics are uncertain. Cross-validation is more informative, although it remains limited by the small sample and correlated predictors.

The adjusted PM2.5 association is approximately positive 0.20 after linear adjustment for the five health indicators. I treat this as a suppression or collinearity-sensitive adjusted association, not a causal effect. PM2.5 did not improve holdout or cross-validated prediction after those indicators were included.

## Scientific interpretation

The current result supports a narrow conclusion: annual mean PM2.5 is not a useful predictor of model-based adult asthma prevalence across Alabama counties in this dataset.

It does not indicate that particulate pollution is harmless. The PM2.5 coefficient of variation is approximately 0.035, so the limited exposure contrast reduces detectable association and statistical power in this design. County aggregation can also obscure local exposure differences.

Chronic asthma prevalence, asthma incidence, and acute asthma exacerbations are distinct outcomes. Annual exposure may be relevant to chronic health, but short-term PM2.5 spikes are better studied with daily outcomes and lagged exposure designs when the question concerns acute exacerbations.

## Quick start

From the repository root:

```bash
pip install -r requirements.txt
cd projects/asthma-air-pollution/v2
python download_data.py
python run_analysis.py
python run_multivariate.py
python run_robustness.py
python run_feature_analysis.py
streamlit run streamlit_app.py
```

The data download generally takes one to three minutes because it requests air-quality estimates county by county. The analysis scripts write JavaScript Object Notation metrics, comma-separated value tables, and figures under `v2/outputs/` and `v2/figures/`.

## What changed in the rebuild

| Version 1 limitation | Version 2 approach |
|---|---|
| Local source files were unavailable | Public data downloads are scripted |
| Row concatenation did not establish a geographic key join | County rows are merged by FIPS code |
| Geography and units were unclear | County resolution and PM2.5 units are documented |
| Evaluation relied on individual splits | Holdout metrics are supplemented with cross-validation and resampling |

## Limitations

- There are only 67 observations.
- The outcome and health indicators share CDC PLACES source methodology.
- County centroids do not represent exposure throughout a county.
- Annual averages cannot test short-term exposure lags.
- Ecological associations cannot be transferred to individuals.
- Correlated predictors make coefficients and model importance unstable.

## Documentation

- [`v2/README.md`](v2/README.md): technical runbook
- [`v2/VALIDATION.md`](v2/VALIDATION.md): statistical evidence and uncertainty
- [`v2/FEATURE_ANALYSIS.md`](v2/FEATURE_ANALYSIS.md): feature methods and caveats
- [`LITERATURE.md`](LITERATURE.md): literature and study-design comparison
- [`ROADMAP.md`](ROADMAP.md): future scientific work
- [`v1/README_EXTENDED.md`](v1/README_EXTENDED.md): concise retrospective correction

## Short glossary

- **R²:** coefficient of determination, a predictive score relative to a target-mean baseline.
- **Coefficient of variation:** standard deviation divided by the mean, used here to describe relative spread.
- **Ecological study:** an analysis whose observations are geographic groups rather than individuals.
- **Modifiable Areal Unit Problem:** sensitivity of results to the choice of geographic boundaries and aggregation.

## External resources

- [CDC PLACES](https://www.cdc.gov/places/)
- [Open-Meteo Air Quality application programming interface](https://open-meteo.com/en/docs/air-quality-api)
- [Original Tableau visualization](https://public.tableau.com/app/profile/gell.rt.bodork.s/viz/Asthmacases/Sheet5?publish=yes)
