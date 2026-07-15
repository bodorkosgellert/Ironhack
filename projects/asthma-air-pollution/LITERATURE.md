# Literature review and study-design comparison

I use this review to place the Version 2 county analysis within the wider evidence on fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5, and asthma. A weak ecological association in Alabama does not conflict with evidence from individual, longitudinal, or daily time-series studies because the designs estimate different quantities.

## Air pollution and respiratory health

1. **Pope CA III, Burnett RT, Thun MJ, et al.** (2002). Lung cancer, cardiopulmonary mortality, and long-term exposure to fine particulate air pollution. *JAMA*, 287(9), 1132–1141. https://doi.org/10.1001/jama.287.9.1132

2. **World Health Organization.** (2021). *WHO global air quality guidelines: particulate matter, ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide*. ISBN 978-92-4-003422-8. https://www.who.int/publications/i/item/9789240034228

3. **Boogaard H, Patton AP, Atkinson RW, et al.** (2022). Long-term exposure to traffic-related air pollution and selected health outcomes: a systematic review and meta-analysis. *Environment International*, 164, 107262. https://doi.org/10.1016/j.envint.2022.107262

4. **Zanobetti A, Ryan PH, Coull BA, et al.** (2024). Early-life exposure to air pollution and childhood asthma cumulative incidence in the ECHO CREW Consortium. *JAMA Network Open*, 7(2), e240535. https://doi.org/10.1001/jamanetworkopen.2024.0535

5. **Andersen ZJ, Thacher JD, Hvidtfeldt UA, et al.** (2023). Early-life exposure to ambient air pollution from multiple sources and asthma incidence in children. *Environmental Health Perspectives*, 131(5), 057003. https://doi.org/10.1289/EHP11539

These sources support concern about PM2.5 as a population-health hazard. The asthma studies use stronger temporal and individual exposure information than my county cross-section.

## Ecological inference

6. **Robinson WS.** (1950). Ecological correlations and the behavior of individuals. *American Sociological Review*, 15(3), 351–357. https://doi.org/10.2307/2087176

7. **Greenland S.** (2001). Ecologic versus individual-level sources of bias in ecologic estimates of contextual health effects. *International Journal of Epidemiology*, 30(6), 1343–1350. https://doi.org/10.1093/ije/30.6.1343

8. **Bechle MJ, Millet DB, Marshall JD.** (2020). Air pollution and COVID-19 mortality in the United States: strengths and limitations of an ecological regression analysis. *Science Advances*, 6(45), eabd4049. https://doi.org/10.1126/sciadv.abd4049

9. **Roumeliotis S, Abdelfattah S, Hafeez S, et al.** (2020). Be careful with ecological associations. *Nephrology*, 25(6), 435–440. https://doi.org/10.1111/nep.13861

These papers explain why group-level associations cannot be read as individual effects. County averages combine heterogeneous people, environments, and health-care contexts.

## Centers for Disease Control and Prevention PLACES methodology

10. **Zhang X, Holt JB, Lu H, et al.** (2014). Multilevel regression and poststratification for small-area estimation of population health outcomes. *American Journal of Epidemiology*, 179(8), 1025–1033. https://doi.org/10.1093/aje/kwu018

11. **Holt JB, Zhang X, Lu H, et al.** (2022). PLACES: Local Data for Better Health. *Preventing Chronic Disease*, 19, 210459. https://doi.org/10.5888/pcd19.210459

12. **Centers for Disease Control and Prevention.** PLACES: Local Data for Better Health. https://www.cdc.gov/places/

Centers for Disease Control and Prevention (CDC) PLACES estimates are model-based small-area values derived from Behavioral Risk Factor Surveillance System data. Asthma and the five county health indicators in Version 2 come from related methodology. Their strong correlations may partly reflect shared source structure and broad population-health patterns.

## Related risk-factor evidence

13. **Beuther KR, Sutherland ER.** (2007). Overweight, obesity, and incident asthma: a meta-analysis of prospective epidemiologic studies. *American Journal of Respiratory and Critical Care Medicine*, 175(7), 661–666. https://doi.org/10.1164/rccm.200611-1717OC

14. **Chen J, Hoek G.** (2020). Long-term exposure to particulate matter and all-cause and cause-specific mortality: a systematic review and meta-analysis. *Environment International*, 143, 105974. https://doi.org/10.1016/j.envint.2020.105974

Evidence that obesity is related to asthma does not turn the Version 2 obesity correlation into a causal estimate. My study lacks the individual and temporal information needed for that inference.

## Design comparison

| Aspect | Individual or cohort study | Version 2 |
|---|---|---|
| Unit | Person or household | 67 Alabama counties |
| Exposure | Residence-linked monitor or spatial model | Annual mean PM2.5 at county centroid |
| Outcome | Diagnosis, incidence, lung function, symptoms, or acute event | Model-based current adult asthma prevalence |
| Adjustment | Individual demographic, behavioural, clinical, and socioeconomic variables | Five correlated county health indicators |
| Time | Longitudinal follow-up or daily series | Single-year cross-section |
| Inference | Individual association under design assumptions | County-level association and prediction |

## How I reconcile the evidence

The raw Version 2 Pearson correlation is approximately negative 0.06. A PM2.5-only random forest has holdout R² near 0.03 in one split, while cross-validated R² is negative. The adjusted correlation near positive 0.20 is suppression or collinearity-sensitive and is not a causal effect. PM2.5 does not improve prediction after the county health indicators are included.

The PM2.5 coefficient of variation near 0.035 indicates limited exposure contrast, which reduces detectable association and statistical power. It does not mathematically constrain biological effects. County aggregation, centroid exposure assignment, small sample size, and the model-based outcome also limit inference.

Chronic prevalence, incidence, and acute exacerbations must remain distinct. Annual exposure is not biologically irrelevant, but daily outcomes and lagged exposure are better suited to studying short-term PM2.5 spikes and acute exacerbations.

See the [validation document](v2/VALIDATION.md) for current metrics and the [roadmap](ROADMAP.md) for planned design improvements.
