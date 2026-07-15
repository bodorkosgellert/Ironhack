# Feature analysis methods and caveats

I use this analysis to examine model behaviour, not to rank causes of asthma. PM2.5 denotes fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less.

Run:

```bash
python run_feature_analysis.py
```

The script writes `outputs/feature_analysis.json`, `outputs/county_residuals_confounders_only.csv`, and figures under `figures/`.

## Exposure spread

| Variable | Range | Coefficient of variation |
|---|---:|---:|
| PM2.5, micrograms per cubic metre | 9.4 to 11.7 | 0.035 |
| Obesity prevalence, percent | 31.7 to 52.9 | 0.105 |
| Diabetes prevalence, percent | 11.2 to 27.1 | 0.198 |
| Asthma prevalence, percent | 9.3 to 12.0 | 0.059 |

The coefficient of variation is the standard deviation divided by the mean. The narrow PM2.5 spread limits detectable association and statistical power in this design. It does not mathematically restrict the possible biological effect and does not establish why the observed correlation is weak.

## Holdout prediction

The full random forest has holdout mean absolute error of approximately 0.205. The model without PM2.5 has holdout mean absolute error of approximately 0.182.

This comparison uses a holdout of roughly 17 counties. It indicates that PM2.5 did not improve this split, but the difference is not a stable population estimate. The corresponding cross-validated R² values are nearly identical, at approximately 0.757 with and without PM2.5.

## Permutation feature importance

Permutation feature importance measures how much a fitted model's score changes when one feature is shuffled. The current analysis uses negative mean absolute error, 30 repeats, and the same roughly 17-county holdout.

| Feature | Mean importance |
|---|---:|
| Diabetes prevalence | 0.163 |
| Binge drinking prevalence | 0.135 |
| Obesity prevalence | 0.027 |
| Physical inactivity prevalence | 0.019 |
| Smoking prevalence | 0.007 |
| PM2.5 | negative 0.013 |

These estimates are noisy because the holdout is small. They are model-dependent and not causal. Correlated predictors can share or mask importance, so the ordering does not establish that diabetes or binge drinking is more causally important than another variable. Random forest split importance is similarly unstable under strong predictor correlation and should not be interpreted causally.

Negative PM2.5 importance means that shuffling PM2.5 did not worsen prediction in this specific split and slightly improved the selected score. It does not mean PM2.5 universally harms prediction.

## Feature selection

The script reports two different procedures.

The manual greedy procedure selected the next variable by test mean absolute error. It therefore reused the test set for model selection and does not provide independent evidence. I retain it only as exploratory model diagnostics. It added PM2.5 last and the final test error increased, but that path should not be used as a headline result.

The cross-validation-based sequential selector chose PM2.5, obesity prevalence, and binge drinking prevalence. This contradicts the simple narrative that PM2.5 is always excluded. Given the small sample and correlated variables, selection instability is expected. Cross-validation-based selection is methodologically preferable to selecting on test error, but it is still not definitive evidence that a variable has a stable effect.

## Residual file

`outputs/county_residuals_confounders_only.csv` contains observed and predicted asthma prevalence, residuals, and PM2.5 values. It supports inspection of model errors but does not identify causal explanations for individual counties.

## Conclusion

Across holdout and cross-validated prediction, PM2.5 adds no clear predictive improvement after the five correlated county health indicators are included. Feature importance and selection results should be treated as unstable model diagnostics, not causal rankings.

See [`VALIDATION.md`](VALIDATION.md) for the statistical evidence and [`../LITERATURE.md`](../LITERATURE.md) for study-design context.
