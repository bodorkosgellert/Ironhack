# Scientific roadmap

I plan to extend this work by improving exposure contrast, temporal alignment, and geographic resolution. The objective is better study design, not a larger score for its own sake.

## Current evidence

Version 2 uses 67 Alabama counties and annual mean fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5. The raw correlation with current adult asthma prevalence is approximately negative 0.06. One random forest holdout score is near 0.03, while cross-validated R² is negative. The design therefore provides little evidence of useful county-level PM2.5 prediction.

## Priority 1: validate exposure estimates

I will compare Open-Meteo estimates with United States Environmental Protection Agency Air Quality System monitor data where coverage permits. This can quantify disagreement in county ranks and annual means. It will not create complete county exposure coverage, because monitors are unevenly distributed.

Sources:

- [United States Environmental Protection Agency AirData](https://aqs.epa.gov/aqsweb/airdata/download_files.html)
- [OpenAQ](https://openaq.org/)

## Priority 2: increase geographic contrast

I will repeat the documented county pipeline in a state or multi-state region with greater PM2.5 variation. The comparison should report exposure distributions, missingness, model stability, and cross-validated performance rather than selecting a region because it produces a preferred result.

Low exposure contrast limits detectable association and statistical power in Alabama. It does not mathematically restrict a biological effect.

## Priority 3: align acute questions with daily data

Short-term PM2.5 spikes may contribute to acute asthma exacerbations. I will study that question with daily exposure and daily or weekly outcomes, using pre-specified lag windows.

Potential sources include:

- [CDC daily county PM2.5 concentrations](https://data.cdc.gov/Environmental-Health-Toxicology/Daily-County-Level-PM2-5-Concentrations-2001-2022/53mz-4zqd)
- [CDC Environmental Public Health Tracking Network](https://ephtracking.cdc.gov/)

If suitable asthma emergency or hospitalisation outcomes are unavailable, I will document the data gap rather than substitute annual prevalence as though it measured acute events.

## Priority 4: improve spatial resolution

Tract-level or address-linked exposure can preserve variation that county averages hide. A finer analysis would still be ecological unless it links individual outcomes and exposures. It would also remain subject to the Modifiable Areal Unit Problem.

I will require explicit geographic keys, documented aggregation, consistent years, and clear PM2.5 units. The Version 1 row concatenation will not be reused.

## Priority 5: strengthen validation

Future modelling should include:

- repeated or nested cross-validation for model and feature selection;
- uncertainty intervals for predictive differences;
- spatially aware validation where sample size permits;
- sensitivity analyses for exposure source and outcome year;
- separate reporting of exploratory and confirmatory analyses.

Feature selection must occur inside the resampling process. The current manual greedy selection reused the test set and is retained only as exploratory diagnostics.

## Interpretation commitments

I will keep prevalence, incidence, and acute exacerbations separate. I will use causal terms only with an explicit causal design and assumptions. Model importance will remain a predictive diagnostic rather than a ranking of biological causes.

The [literature review](LITERATURE.md) provides the design context, and the [validation document](v2/VALIDATION.md) records the current evidence.
