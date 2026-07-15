"""Permutation importance, forward selection, variance analysis (v2 extension)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import SequentialFeatureSelector
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
FULL_CSV = HERE / "outputs" / "alabama_counties_full.csv"
FIG_DIR = HERE / "figures"
OUT_DIR = HERE / "outputs"
OUT_JSON = OUT_DIR / "feature_analysis.json"
RESIDUALS_CSV = OUT_DIR / "county_residuals_confounders_only.csv"

TARGET = "asthma_pct"
PM25 = "pm25_ug_m3_annual_mean"
CONFOUNDERS = [
    "smoking_pct",
    "obesity_pct",
    "diabetes_pct",
    "no_physical_activity_pct",
    "binge_drinking_pct",
]
ALL_FEATURES = [PM25, *CONFOUNDERS]
VARIANCE_FEATURES = [PM25, "obesity_pct", "diabetes_pct", TARGET]


def load_data() -> pd.DataFrame:
    if not FULL_CSV.exists():
        raise FileNotFoundError(f"Missing {FULL_CSV}. Run: python download_data.py")
    return pd.read_csv(FULL_CSV)


def make_pipeline(features: list[str]) -> Pipeline:
    return Pipeline(
        [
            ("scale", ColumnTransformer([("num", StandardScaler(), features)])),
            (
                "model",
                RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2),
            ),
        ]
    )


def coefficient_of_variation(series: pd.Series) -> dict:
    mean = float(series.mean())
    std = float(series.std())
    return {
        "mean": mean,
        "std": std,
        "min": float(series.min()),
        "max": float(series.max()),
        "range": float(series.max() - series.min()),
        "cv": float(std / mean) if mean else float("nan"),
    }


def mae_comparison(df: pd.DataFrame) -> dict:
    x_full = df[ALL_FEATURES]
    x_no_pm25 = df[CONFOUNDERS]
    y = df[TARGET]
    x_tr, x_te, y_tr, y_te = train_test_split(x_full, y, test_size=0.25, random_state=42)

    pipe_full = make_pipeline(ALL_FEATURES)
    pipe_full.fit(x_tr, y_tr)
    mae_full = float(mean_absolute_error(y_te, pipe_full.predict(x_te)))

    pipe_no = make_pipeline(CONFOUNDERS)
    pipe_no.fit(x_tr[CONFOUNDERS], y_tr)
    mae_no = float(mean_absolute_error(y_te, pipe_no.predict(x_te[CONFOUNDERS])))

    delta = mae_full - mae_no
    return {
        "mae_test_with_pm25": mae_full,
        "mae_test_without_pm25": mae_no,
        "mae_delta_full_minus_no_pm25": delta,
        "removing_pm25_improves_mae": bool(delta > 0),
        "interpretation": (
            "Positive delta means confounders-only model has lower MAE on the holdout set; "
            "PM2.5 adds noise or overfitting, not signal."
        ),
    }


def permutation_importance_report(
    pipe: Pipeline, x_test: pd.DataFrame, y_test: pd.Series, features: list[str]
) -> dict:
    result = permutation_importance(
        pipe,
        x_test,
        y_test,
        n_repeats=30,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )
    rows = []
    for i, feat in enumerate(features):
        rows.append(
            {
                "feature": feat,
                "importance_mean": float(result.importances_mean[i]),
                "importance_std": float(result.importances_std[i]),
            }
        )
    rows.sort(key=lambda r: r["importance_mean"], reverse=True)
    return {"scoring": "neg_mean_absolute_error", "n_repeats": 30, "ranked": rows}


def forward_selection_report(df: pd.DataFrame) -> dict:
    x = df[ALL_FEATURES]
    y = df[TARGET]
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.25, random_state=42)

    base = RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)
    sfs = SequentialFeatureSelector(
        base,
        n_features_to_select="auto",
        direction="forward",
        scoring="neg_mean_absolute_error",
        cv=5,
        n_jobs=1,
    )
    pipe = Pipeline(
        [
            ("scale", ColumnTransformer([("num", StandardScaler(), ALL_FEATURES)])),
            ("select", sfs),
            ("model", RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2)),
        ]
    )
    pipe.fit(x_tr, y_tr)
    mask = pipe.named_steps["select"].get_support()
    selected = [f for f, keep in zip(ALL_FEATURES, mask, strict=True) if keep]

    pred = pipe.predict(x_te)
    return {
        "selected_features": selected,
        "pm25_selected": PM25 in selected,
        "n_selected": len(selected),
        "mae_test_forward_selection": float(mean_absolute_error(y_te, pred)),
        "r2_test_forward_selection": float(r2_score(y_te, pred)),
    }


def manual_forward_steps(df: pd.DataFrame) -> list[dict]:
    """Greedy forward steps by test MAE (same train/test split)."""
    x = df[ALL_FEATURES]
    y = df[TARGET]
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.25, random_state=42)

    remaining = list(ALL_FEATURES)
    selected: list[str] = []
    steps: list[dict] = []

    while remaining:
        best_feat = None
        best_mae = float("inf")
        for feat in remaining:
            trial = selected + [feat]
            pipe = make_pipeline(trial)
            pipe.fit(x_tr[trial], y_tr)
            mae = float(mean_absolute_error(y_te, pipe.predict(x_te[trial])))
            if mae < best_mae:
                best_mae = mae
                best_feat = feat
        assert best_feat is not None
        selected.append(best_feat)
        remaining.remove(best_feat)
        steps.append(
            {
                "step": len(selected),
                "added": best_feat,
                "features": list(selected),
                "mae_test": best_mae,
                "pm25_included": PM25 in selected,
            }
        )
    return steps


def plot_variance_histograms(df: pd.DataFrame) -> Path:
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    sns.histplot(df[PM25], kde=True, ax=axes[0], color="#4C72B0", bins=12)
    axes[0].set_title(f"PM2.5 distribution (CV={df[PM25].std() / df[PM25].mean():.3f})")
    axes[0].set_xlabel("Annual mean PM2.5 (µg/m³)")

    sns.histplot(df["obesity_pct"], kde=True, ax=axes[1], color="#55A868", bins=12)
    axes[1].set_title(
        f"Obesity % distribution (CV={df['obesity_pct'].std() / df['obesity_pct'].mean():.3f})"
    )
    axes[1].set_xlabel("Obesity prevalence (%)")

    fig.suptitle("Exposure contrast: PM2.5 vs obesity across 67 Alabama counties", y=1.02)
    fig.tight_layout()
    out = FIG_DIR / "pm25_obesity_variance_histogram.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def export_county_residuals(df: pd.DataFrame) -> Path:
    """Hold-out residuals from confounders-only model (one row per county)."""
    x = df[CONFOUNDERS]
    y = df[TARGET]
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.25, random_state=42)
    pipe = make_pipeline(CONFOUNDERS)
    pipe.fit(x_tr, y_tr)
    pred = pipe.predict(df[CONFOUNDERS])
    out_df = df[
        ["county_fips", "county", TARGET, PM25, "obesity_pct", "diabetes_pct"]
    ].copy()
    out_df["predicted_asthma_pct"] = pred
    out_df["residual"] = out_df[TARGET] - out_df["predicted_asthma_pct"]
    out_df["in_test_holdout"] = out_df.index.isin(y_te.index)
    out_df.to_csv(RESIDUALS_CSV, index=False)
    return RESIDUALS_CSV


def plot_permutation_importance(ranked: list[dict]) -> Path:
    sns.set_theme(style="whitegrid")
    plot_df = pd.DataFrame(ranked).sort_values("importance_mean", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(
        plot_df["feature"],
        plot_df["importance_mean"],
        xerr=plot_df["importance_std"],
        color="#4C72B0",
        alpha=0.85,
    )
    ax.set_xlabel("Permutation importance (Δ neg_MAE; higher = more important)")
    ax.set_title("Permutation feature importance — full model (PM2.5 + confounders)")
    fig.tight_layout()
    out = FIG_DIR / "permutation_importance.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    x = df[ALL_FEATURES]
    y = df[TARGET]
    x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.25, random_state=42)

    pipe_full = make_pipeline(ALL_FEATURES)
    pipe_full.fit(x_tr, y_tr)

    variance = {col: coefficient_of_variation(df[col]) for col in VARIANCE_FEATURES}
    mae_cmp = mae_comparison(df)
    perm = permutation_importance_report(pipe_full, x_te, y_te, ALL_FEATURES)
    fwd_sfs = forward_selection_report(df)
    fwd_steps = manual_forward_steps(df)

    report = {
        "n_counties": int(len(df)),
        "variance_analysis": variance,
        "variance_interpretation": (
            "Lower coefficient of variation (CV) means less relative spread across counties. "
            "PM2.5 with low CV has limited leverage for explaining asthma differences."
        ),
        "mae_with_vs_without_pm25": mae_cmp,
        "permutation_importance": perm,
        "forward_selection_sklearn": fwd_sfs,
        "forward_selection_greedy_steps": fwd_steps,
        "pm25_permutation_rank": next(
            i + 1
            for i, row in enumerate(perm["ranked"])
            if row["feature"] == PM25
        ),
    }

    hist_path = plot_variance_histograms(df)
    perm_path = plot_permutation_importance(perm["ranked"])
    residuals_path = export_county_residuals(df)
    report["outputs"] = {
        "json": str(OUT_JSON.name),
        "residuals_csv": str(RESIDUALS_CSV.name),
        "histogram_figure": str(hist_path.name),
        "permutation_figure": str(perm_path.name),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nSaved -> {OUT_JSON}")
    print(f"Saved -> {residuals_path}")
    print(f"Saved -> {hist_path}")
    print(f"Saved -> {perm_path}")
    print(
        f"\nPM2.5 CV={variance[PM25]['cv']:.4f} vs obesity CV={variance['obesity_pct']['cv']:.4f}"
    )
    print(
        f"Removing PM2.5 improves MAE: {mae_cmp['removing_pm25_improves_mae']} "
        f"(delta={mae_cmp['mae_delta_full_minus_no_pm25']:.4f})"
    )


if __name__ == "__main__":
    main()
