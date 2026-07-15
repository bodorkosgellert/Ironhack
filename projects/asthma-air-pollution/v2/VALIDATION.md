# Statistical validation and uncertainty

This document records the evidence behind my Version 2 interpretation. It separates computational checks, predictive performance, and scientific inference.

Run the relevant analysis with:

```bash
python download_data.py
python run_analysis.py
python run_multivariate.py
python run_robustness.py
```

## Scope

The dataset contains 67 Alabama counties. The outcome is model-based current adult asthma prevalence from Centers for Disease Control and Prevention (CDC) PLACES. PM2.5 is the annual mean concentration of fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less at each county centroid.

The candidate adjustment variables are smoking prevalence, obesity prevalence, diabetes prevalence, physical inactivity prevalence, and binge drinking prevalence. I do not call them established confounders because this ecological study does not identify a causal structure or establish causal confounding.

## PM2.5-only evidence

| Measure | Current result |
|---|---:|
| Pearson correlation | Approximately negative 0.06 |
| Spearman correlation | Approximately negative 0.06 |
| Linear regression holdout R² | Approximately negative 0.02 |
| Random forest holdout R² | Approximately 0.04 in `metrics.json` and 0.03 in the multivariate comparison |
| Linear regression mean cross-validated R² | Approximately negative 0.21 |
| Random forest mean cross-validated R² | Approximately negative 0.26, or negative 0.32 in the multivariate comparison |

The one-split random forest result near 0.03 should not be presented alone. Cross-validated R² is negative in the current outputs, indicating poor out-of-sample performance. Negative R² means performance was worse than predicting the target mean on the evaluated data.

Bootstrap confidence intervals for the correlation include zero, and the permutation test does not reject a zero association. These results do not establish that the true effect is zero; they show that this design does not resolve a clear county-level association.

## Adjusted association

The partial correlation between PM2.5 and asthma is approximately positive 0.20 after linear adjustment for the five county health indicators. Its sign differs from the raw correlation, which makes it a suppression or collinearity-sensitive adjusted association.

I do not interpret this value as a causal effect. The indicators are strongly correlated with one another, the sample is small, and partial correlation depends on the adjustment specification. PM2.5 did not improve holdout or cross-validated prediction after the other indicators were included.

## Same-source health indicators

| Model or association | Result |
|---|---:|
| Obesity and asthma Pearson correlation | Approximately 0.86 |
| Five-indicator random forest holdout R² | Approximately 0.86 |
| Five-indicator mean cross-validated R² | Approximately 0.76 |

Asthma and the five predictors are all model-based CDC PLACES estimates produced through related source methodology. Their strong associations check basic join and computation behavior, but they are not independent external validation. Shared source structure and correlated population-health patterns can contribute substantially to the fit.

The holdout contains approximately 17 counties from only 67 total counties, so the holdout R² is uncertain and split-sensitive. Five-fold cross-validation uses the data more fully and is more informative, but it is still constrained by sample size, correlated predictors, and dependence among nearby counties.

## Exposure contrast and power

Annual mean PM2.5 ranges from approximately 9.4 to 11.7 micrograms per cubic metre, with a coefficient of variation near 0.035. This low exposure contrast limits detectable association and statistical power in the current design.

The coefficient of variation does not mathematically restrict a biological effect and does not by itself explain the weak correlation. It is one limitation among geographic aggregation, centroid exposure assignment, model-based outcomes, temporal mismatch, and small sample size.

## Interpretation boundaries

This analysis concerns chronic asthma prevalence. It does not measure asthma incidence or daily acute exacerbations. Short-term PM2.5 spikes may be better studied with daily emergency visits, symptoms, or hospitalisations and lagged exposure designs. Annual exposure can still matter biologically; the designs answer different questions.

County-level associations also cannot be transferred to individuals. This is an ecological study affected by the Modifiable Areal Unit Problem, which means results can depend on the chosen geographic boundaries.

## What the evidence supports

The current evidence supports the statement that annual mean PM2.5 is a poor predictor of model-based adult asthma prevalence across Alabama counties in this dataset.

It does not support claims that PM2.5 does not affect asthma, that obesity or diabetes causes asthma, or that a high same-source model score validates the analysis externally.

## Version 1 comparison

Version 1 used census tract-level PLACES estimates, not patient records. Its local Excel inputs are absent, row concatenation did not establish a geographic key join, and source years and PM2.5 units were unclear. Version 2 improves traceability through public downloads and FIPS-keyed county merges, but it remains an ecological analysis.

See [`FEATURE_ANALYSIS.md`](FEATURE_ANALYSIS.md) for model-dependent feature analysis and [`../LITERATURE.md`](../LITERATURE.md) for comparison with stronger epidemiological designs.
