# Version 1 retrospective correction

I wrote this retrospective in 2026 to clarify the design and interpretation of my 2021 capstone. The original text remains frozen in [`ORIGINAL_README.md`](ORIGINAL_README.md).

## What I built in 2021

I explored whether area-level air-pollution measures could predict model-based asthma prevalence. The notebook includes linear regression, k-nearest neighbours, and random forest models for Alabama and Arizona data. PM2.5 denotes fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less.

| Analysis | Geographic rows | Pollutants |
|---|---:|---|
| Alabama | 1,175 census tracts | PM2.5 |
| Arizona | 1,516 census tracts | PM10 |
| Arizona subset | 791 census tracts | Nitrogen dioxide, sulfur dioxide, carbon monoxide, and ozone |

These rows were geographic observations, not patients. The Centers for Disease Control and Prevention (CDC) PLACES values were model-based prevalence estimates. `CASTHMA` refers to current adult asthma prevalence, not incidence.

## Data integration correction

The notebook depended on local Excel files that are absent from the repository. More importantly, row concatenation did not establish that asthma and pollution records referred to the same geography. A defensible spatial analysis requires an explicit key, such as a Federal Information Processing Standards code, plus documented aggregation rules.

The source years and PM2.5 units were also unclear. The reported PM2.5 range cannot be compared directly with Version 2 without verified provenance and units.

## Outcome and exposure correction

Asthma prevalence, asthma incidence, and acute exacerbations answer different scientific questions.

- Prevalence describes the proportion of adults currently estimated to have asthma.
- Incidence describes new asthma cases over time.
- Acute exacerbations are short-term worsening events, often studied through emergency visits or daily symptoms.

An annual PM2.5 average may still be relevant to chronic exposure, but it cannot directly test whether short-term spikes precede acute exacerbations. That question is better addressed with daily outcomes and lagged exposure designs. The original analysis therefore had an exposure and outcome alignment limitation; this does not make annual PM2.5 biologically irrelevant.

## Interpreting negative R²

R² is the coefficient of determination. A negative R² on evaluated data means the model performed worse than predicting the target mean.

Negative performance can arise from weak signal, model mismatch, small samples, unstable splits, faulty joins, or overfitting. It does not necessarily establish a severe software defect. In Version 1, the unverified row alignment and missing source metadata are material reasons to avoid strong conclusions.

## Geographic interpretation

The Modifiable Areal Unit Problem describes how results can change when observations are grouped into different geographic boundaries. Version 1 used census tracts, while Version 2 uses counties. County aggregation reduces sample size and can smooth local exposure differences, so results at the two resolutions are not directly interchangeable.

## What Version 2 changes

Version 2 downloads public data, creates one row per Alabama county, and merges records through county Federal Information Processing Standards (FIPS) codes. It documents the outcome, exposure units, model inputs, holdout evaluation, cross-validation, and robustness checks.

The Version 2 result is still weak for PM2.5 prediction, but it rests on an auditable join. I treat the agreement between versions as a repeated qualitative observation, not evidence that the original alignment was correct.

See the [project overview](../README.md), [Version 2 runbook](../v2/README.md), and [validation analysis](../v2/VALIDATION.md).
