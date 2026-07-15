"""v2: county-level merge + supervised models with honest metrics."""

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
DATA_CSV = HERE / "outputs" / "alabama_counties_merged.csv"
FIG_DIR = HERE / "figures"
OUT_DIR = HERE / "outputs"
METRICS_JSON = OUT_DIR / "metrics.json"

FEATURES = ["pm25_ug_m3_annual_mean"]
TARGET = "asthma_pct"


def load_data() -> pd.DataFrame:
    if not DATA_CSV.exists():
        raise FileNotFoundError(
            f"Missing {DATA_CSV}. Run: python download_data.py"
        )
    return pd.read_csv(DATA_CSV)


def evaluate_model(name: str, model, x_train, x_test, y_train, y_test) -> dict:
    pipe = Pipeline(
        [
            ("scale", ColumnTransformer([("num", StandardScaler(), FEATURES)])),
            ("model", model),
        ]
    )
    pipe.fit(x_train, y_train)
    pred = pipe.predict(x_test)
    cv = cross_val_score(pipe, pd.concat([x_train, x_test]), pd.concat([y_train, y_test]), cv=5, scoring="r2")
    return {
        "model": name,
        "r2_test": float(r2_score(y_test, pred)),
        "mae_test": float(mean_absolute_error(y_test, pred)),
        "r2_cv_mean": float(cv.mean()),
        "r2_cv_std": float(cv.std()),
        "n_counties": int(len(x_train) + len(x_test)),
    }


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    x = df[FEATURES]
    y = df[TARGET]

    # v1 bug was concatenating unrelated series; v2 uses one row per county.
    pearson_r = float(df[FEATURES[0]].corr(df[TARGET]))

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)

    metrics = [
        evaluate_model("linear_regression", LinearRegression(), x_train, x_test, y_train, y_test),
        evaluate_model(
            "random_forest",
            RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=2),
            x_train,
            x_test,
            y_train,
            y_test,
        ),
    ]

    summary = {
        "state": "Alabama",
        "year": 2023,
        "pearson_r_pm25_asthma": pearson_r,
        "models": metrics,
        "interpretation": (
            "County-level PM2.5 (Open-Meteo annual mean at CDC centroid) vs "
            "CDC PLACES crude asthma prevalence. Weak or moderate association "
            "is still a valid scientific outcome."
        ),
    }
    METRICS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.regplot(data=df, x=FEATURES[0], y=TARGET, ax=ax, scatter_kws={"alpha": 0.7})
    ax.set_title("Alabama counties: PM2.5 vs adult asthma prevalence (v2)")
    ax.set_xlabel("PM2.5 annual mean (µg/m³, Open-Meteo 2023)")
    ax.set_ylabel("Current asthma among adults (%, CDC PLACES crude)")
    fig.tight_layout()
    scatter_path = FIG_DIR / "pm25_vs_asthma_scatter.png"
    fig.savefig(scatter_path, dpi=150)
    plt.close(fig)

    best = max(metrics, key=lambda m: m["r2_test"])
    print(json.dumps(summary, indent=2))
    print(f"\nSaved metrics -> {METRICS_JSON}")
    print(f"Saved figure -> {scatter_path}")
    print(f"Best test R² ({best['model']}): {best['r2_test']:.3f}")


if __name__ == "__main__":
    main()
