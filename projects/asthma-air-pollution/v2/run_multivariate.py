"""Partial correlation + multivariate prediction (v2 extension)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
FULL_CSV = HERE / "outputs" / "alabama_counties_full.csv"
FIG_DIR = HERE / "figures"
OUT_DIR = HERE / "outputs"
METRICS_JSON = OUT_DIR / "multivariate_metrics.json"

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


def load_data() -> pd.DataFrame:
    if not FULL_CSV.exists():
        raise FileNotFoundError(f"Missing {FULL_CSV}. Run: python download_data.py")
    return pd.read_csv(FULL_CSV)


def partial_correlation(df: pd.DataFrame, x: str, y: str, controls: list[str]) -> float:
    """Pearson r between residuals after linearly removing controls."""
    if not controls:
        return float(df[x].corr(df[y]))

    def residuals(col: str) -> pd.Series:
        lr = LinearRegression()
        lr.fit(df[controls], df[col])
        return df[col] - lr.predict(df[controls])

    return float(residuals(x).corr(residuals(y)))


def evaluate(name: str, features: list[str], df: pd.DataFrame) -> dict:
    x = df[features]
    y = df[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)

    pipe = Pipeline(
        [
            ("scale", ColumnTransformer([("num", StandardScaler(), features)])),
            (
                "model",
                RandomForestRegressor(n_estimators=300, random_state=42, min_samples_leaf=2),
            ),
        ]
    )
    pipe.fit(x_train, y_train)
    pred = pipe.predict(x_test)
    cv = cross_val_score(
        pipe, x, y, cv=5, scoring="r2"
    )
    importances = dict(
        zip(features, map(float, pipe.named_steps["model"].feature_importances_), strict=True)
    )
    return {
        "model": name,
        "features": features,
        "r2_test": float(r2_score(y_test, pred)),
        "mae_test": float(mean_absolute_error(y_test, pred)),
        "r2_cv_mean": float(cv.mean()),
        "r2_cv_std": float(cv.std()),
        "feature_importance": importances,
        "n_counties": int(len(df)),
    }


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    numeric_cols = [TARGET, *ALL_FEATURES]

    pearson = df[numeric_cols].corr(method="pearson")
    partials: dict[str, float] = {}
    for col in ALL_FEATURES:
        if col == PM25:
            controls = CONFOUNDERS
        else:
            controls = [PM25] + [c for c in CONFOUNDERS if c != col]
        partials[f"partial_r_{col}_vs_asthma"] = partial_correlation(df, col, TARGET, controls)

    models = [
        evaluate("pm25_only", [PM25], df),
        evaluate("confounders_only", CONFOUNDERS, df),
        evaluate("pm25_plus_confounders", ALL_FEATURES, df),
    ]

    summary = {
        "state": "Alabama",
        "year": 2023,
        "n_counties": int(len(df)),
        "pearson_correlation_matrix": pearson.round(4).to_dict(),
        "partial_correlations_vs_asthma": {k: round(v, 4) for k, v in partials.items()},
        "models": models,
        "interpretation": (
            "Partial correlation removes linear effects of other county health metrics. "
            "Multivariate models test whether PM2.5 adds predictive value beyond "
            "smoking/obesity/diabetes/etc. Higher R² here means better county-level "
            "prediction, not proof of causation."
        ),
    }
    METRICS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(pearson, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Pearson correlations — asthma, PM2.5, PLACES confounders")
    fig.tight_layout()
    heatmap_path = FIG_DIR / "correlation_heatmap.png"
    fig.savefig(heatmap_path, dpi=150)
    plt.close(fig)

    print(json.dumps(summary, indent=2))
    print(f"\nSaved -> {METRICS_JSON}")
    print(f"Saved -> {heatmap_path}")
    best = max(models, key=lambda m: m["r2_test"])
    print(f"Best test R² ({best['model']}): {best['r2_test']:.3f}")


if __name__ == "__main__":
    main()
