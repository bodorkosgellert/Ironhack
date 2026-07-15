"""Fetch full county dataset (asthma + confounders + PM2.5)."""

from __future__ import annotations

from pathlib import Path

from data_utils import build_county_dataset

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
MERGED_CSV = OUTPUT_DIR / "alabama_counties_merged.csv"
FULL_CSV = OUTPUT_DIR / "alabama_counties_full.csv"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    full = build_county_dataset()
    full.to_csv(FULL_CSV, index=False)
    print(f"Wrote {len(full)} counties to {FULL_CSV}")

    # Back-compat for original v2 script
    slim_cols = ["county_fips", "county", "asthma_pct", "lat", "lon", "pm25_ug_m3_annual_mean"]
    for extra in ("low_confidence_limit", "high_confidence_limit"):
        if extra in full.columns:
            slim_cols.insert(-1, extra)
    slim = full[slim_cols]
    slim.to_csv(MERGED_CSV, index=False)
    print(f"Wrote {len(slim)} counties to {MERGED_CSV}")


if __name__ == "__main__":
    main()
