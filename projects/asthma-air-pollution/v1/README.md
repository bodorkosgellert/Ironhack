# Version 1: original Ironhack capstone

This directory contains my original 2021 analysis and a current retrospective explanation.

## Contents

- [`code/asthma2.ipynb`](code/asthma2.ipynb): original analysis notebook
- [`ORIGINAL_README.md`](ORIGINAL_README.md): original project write-up, preserved unchanged
- [`README_EXTENDED.md`](README_EXTENDED.md): my 2026 retrospective correction
- `docs/`: original presentation material, where available

## Reproducibility status

Version 1 is not fully reproducible from the repository. The notebook refers to local Excel workbooks, but the repository contains no Excel dependencies. The absent inputs include `PLACES__Local_Data_for_Better_Health__Census_Tract_Data_2020_release.xlsx` and `alabama3.xlsx`.

The notebook also concatenated rows without establishing a geographic key join. Data years and units for fine particulate matter with an aerodynamic diameter of 2.5 micrometres or less, known as PM2.5, were unclear. I therefore retain Version 1 as historical exploratory work rather than treating it as a validated analysis.

The 1,175 Alabama observations were census tract-level, model-based prevalence estimates, not patients. The CDC PLACES measure `CASTHMA` represents current adult asthma prevalence, not asthma incidence.

For a reproducible analysis with county Federal Information Processing Standards (FIPS) joins, use [Version 2](../v2/).
