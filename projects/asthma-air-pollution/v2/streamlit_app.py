"""Minimal Streamlit demo — reads precomputed v2 outputs only (no API calls)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = HERE / "outputs"
FIG = HERE / "figures"

CSV_FULL = OUT / "alabama_counties_full.csv"
METRICS_JSON = OUT / "metrics.json"
MULTIVARIATE_JSON = OUT / "multivariate_metrics.json"
FEATURE_JSON = OUT / "feature_analysis.json"
HEATMAP_PNG = FIG / "correlation_heatmap.png"
PERM_PNG = FIG / "permutation_importance.png"

DOC_FILES = {
    "Validation and uncertainty": HERE / "VALIDATION.md",
    "Feature analysis": HERE / "FEATURE_ANALYSIS.md",
    "Literature review": PROJECT / "LITERATURE.md",
}


@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data
def load_json(path: str) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@st.cache_data
def load_markdown_summary(path: str, max_chars: int = 1200) -> tuple[str, str]:
    """Return (relative link label, excerpt) for a markdown doc."""
    p = Path(path)
    if not p.exists():
        return p.name, "_File not found._"
    text = p.read_text(encoding="utf-8")
    # Drop leading title and horizontal rules for a cleaner excerpt.
    body = re.sub(r"^#\s+.+\n+", "", text, count=1)
    body = re.sub(r"\n---\n", "\n\n", body)
    excerpt = body.strip()
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rsplit(" ", 1)[0] + "…"
    return p.name, excerpt


def render_heatmap_from_json(matrix: dict) -> None:
    df = pd.DataFrame(matrix).astype(float)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Pearson correlations (from multivariate_metrics.json)")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)


def main() -> None:
    st.set_page_config(page_title="Asthma × PM2.5 (v2)", layout="wide")
    st.sidebar.caption(
        "Dashboard build: 2026.07.15.2 · corrected interactive scatter plot"
    )
    st.title("Asthma prevalence vs PM2.5 — Alabama counties (v2)")
    st.caption(
        "County-level CDC PLACES + Open-Meteo annual PM2.5. "
        "Loads saved CSV/JSON only — run `download_data.py` once if data is missing."
    )

    metrics = load_json(str(METRICS_JSON))
    multivariate = load_json(str(MULTIVARIATE_JSON))
    feature = load_json(str(FEATURE_JSON))

    with st.sidebar:
        st.markdown(
            "[Evidence assistant (Q&A)](https://asthma-evidence-assistant.streamlit.app/)"
        )
        st.caption("Separate app: cited answers over the public project corpus.")
        st.divider()
        st.header("Key metrics")
        if metrics:
            st.metric("Pearson r (PM2.5 × asthma)", f"{metrics.get('pearson_r_pm25_asthma', 0):.3f}")
            st.metric("Counties", metrics.get("models", [{}])[0].get("n_counties", "—"))
            for m in metrics.get("models", []):
                st.caption(f"{m['model']}: R² test = {m['r2_test']:.3f}, MAE = {m['mae_test']:.3f}")
        else:
            st.warning("Run `python run_analysis.py` to create metrics.json")

        if multivariate:
            st.divider()
            st.subheader("Multivariate")
            partials = multivariate.get("partial_correlations_vs_asthma", {})
            pm25_partial = partials.get("partial_r_pm25_ug_m3_annual_mean_vs_asthma")
            if pm25_partial is not None:
                st.metric("Partial r (PM2.5 | health indicators)", f"{pm25_partial:.3f}")
            for model in multivariate.get("models", []):
                if model["model"] == "confounders_only":
                    st.metric("Health-indicator R² (test)", f"{model['r2_test']:.3f}")
                if model["model"] == "pm25_plus_confounders":
                    st.metric("PM2.5 + indicators R² (test)", f"{model['r2_test']:.3f}")

        if feature:
            st.divider()
            st.subheader("Feature analysis")
            rank = feature.get("pm25_permutation_rank")
            n_feats = len(feature.get("permutation_importance", {}).get("ranked", []))
            if rank and n_feats:
                st.metric("PM2.5 permutation rank", f"{rank} / {n_feats}")
            mae = feature.get("mae_with_vs_without_pm25", {})
            if mae.get("removing_pm25_improves_mae"):
                st.info("Removing PM2.5 improves holdout MAE in this split.")

    if not CSV_FULL.exists():
        st.error(
            f"Missing `{CSV_FULL.name}`. From this folder run:\n\n"
            "```\npython download_data.py\npython run_analysis.py\npython run_multivariate.py\npython run_feature_analysis.py\n```"
        )
        return

    df = load_csv(str(CSV_FULL))
    col_scatter, col_table = st.columns([2, 1])
    with col_scatter:
        st.subheader("PM2.5 vs asthma prevalence")
        chart_columns = ["pm25_ug_m3_annual_mean", "asthma_pct"]
        if "obesity_pct" in df.columns:
            chart_columns.append("obesity_pct")

        chart_df = df[["county", *chart_columns]].copy()
        for column in chart_columns:
            chart_df[column] = pd.to_numeric(chart_df[column], errors="coerce")
        chart_df = chart_df.dropna(subset=["pm25_ug_m3_annual_mean", "asthma_pct"])

        if chart_df.empty:
            st.error(
                "No counties have numeric values for both annual PM2.5 and asthma prevalence."
            )
        else:
            tooltips = [
                alt.Tooltip("county:N", title="County"),
                alt.Tooltip(
                    "pm25_ug_m3_annual_mean:Q",
                    title="Annual mean PM2.5 (µg/m³)",
                    format=".2f",
                ),
                alt.Tooltip(
                    "asthma_pct:Q",
                    title="Current adult asthma prevalence",
                    format=".1f",
                ),
            ]
            if "obesity_pct" in chart_df.columns:
                tooltips.append(
                    alt.Tooltip(
                        "obesity_pct:Q",
                        title="Obesity prevalence",
                        format=".1f",
                    )
                )

            points = (
                alt.Chart(chart_df)
                .mark_circle(size=105, opacity=0.78, color="#1565C0", stroke="white", strokeWidth=0.7)
                .encode(
                    x=alt.X(
                        "pm25_ug_m3_annual_mean:Q",
                        title="Annual mean PM2.5 (µg/m³)",
                        scale=alt.Scale(zero=False, padding=0.25),
                    ),
                    y=alt.Y(
                        "asthma_pct:Q",
                        title="Current adult asthma prevalence (%)",
                        scale=alt.Scale(zero=False, padding=0.25),
                    ),
                    tooltip=tooltips,
                )
            )
            trend = (
                alt.Chart(chart_df)
                .transform_regression("pm25_ug_m3_annual_mean", "asthma_pct")
                .mark_line(color="#D84315", strokeDash=[7, 4], strokeWidth=2)
                .encode(
                    x="pm25_ug_m3_annual_mean:Q",
                    y="asthma_pct:Q",
                )
            )
            chart = (points + trend).properties(
                height=430,
                title=alt.Title(
                    "Alabama counties, 2023 — PM2.5 and current adult asthma prevalence",
                    subtitle=[
                        f"n={len(chart_df)}; Pearson r = "
                        f"{chart_df['pm25_ug_m3_annual_mean'].corr(chart_df['asthma_pct']):.3f}",
                        "Dashed line: descriptive ordinary least-squares trend (not causal).",
                    ],
                ),
            ).configure_axis(
                gridColor="#E5E7EB",
                labelColor="#263238",
                titleColor="#263238",
            )
            st.altair_chart(chart, width="stretch")

        st.caption(
            "**Sources:** Centers for Disease Control and Prevention PLACES "
            "(2023 county current adult asthma and obesity prevalence estimates); "
            "Open-Meteo (2023 gridded annual PM2.5 averaged at county centroids)."
        )
        st.caption(
            "**Limitation:** This is an ecological county-level comparison. Annual averages "
            "can hide local and short-term exposure differences."
        )
    with col_table:
        st.subheader("Sample counties")
        st.dataframe(
            df[["county", "asthma_pct", "pm25_ug_m3_annual_mean", "obesity_pct"]].head(10),
            hide_index=True,
            use_container_width=True,
        )

    col_h, col_p = st.columns(2)
    with col_h:
        st.subheader("Correlation heatmap")
        if HEATMAP_PNG.exists():
            st.image(str(HEATMAP_PNG), use_container_width=True)
        elif multivariate and "pearson_correlation_matrix" in multivariate:
            render_heatmap_from_json(multivariate["pearson_correlation_matrix"])
            st.caption("Rendered from JSON (run `run_multivariate.py` to save PNG).")
        else:
            st.warning("Run `python run_multivariate.py` for heatmap.")

    with col_p:
        st.subheader("Permutation importance")
        if PERM_PNG.exists():
            st.image(str(PERM_PNG), use_container_width=True)
        else:
            st.warning(
                f"`{PERM_PNG.name}` not found. Run:\n\n`python run_feature_analysis.py`"
            )
            if feature and "permutation_importance" in feature:
                ranked = feature["permutation_importance"].get("ranked", [])[:6]
                if ranked:
                    st.table(pd.DataFrame(ranked)[["feature", "importance_mean"]])

    st.divider()
    st.subheader("Project documentation")
    st.caption("Open the Markdown files in the repository for the complete analysis.")

    takeaway_cols = st.columns(3)
    if metrics:
        with takeaway_cols[0]:
            r = metrics.get("pearson_r_pm25_asthma", 0)
            st.metric("PM2.5 ↔ asthma (Pearson)", f"{r:.3f}")
        with takeaway_cols[1]:
            if multivariate:
                partials = multivariate.get("partial_correlations_vs_asthma", {})
                pr = partials.get("partial_r_pm25_ug_m3_annual_mean_vs_asthma")
                if pr is not None:
                    st.metric("Partial r (PM2.5 | health indicators)", f"{pr:.3f}")
        with takeaway_cols[2]:
            if feature:
                st.metric(
                    "PM2.5 permutation rank",
                    f"{feature.get('pm25_permutation_rank', '—')} / "
                    f"{len(feature.get('permutation_importance', {}).get('ranked', [])) or '—'}",
                )

    st.info(
        "**Takeaway:** PM2.5 is a poor predictor at Alabama county resolution in these data. "
        "The county health indicators are strongly associated with the model-based outcome, "
        "but this ecological analysis does not estimate causal effects."
    )

    for label, doc_path in DOC_FILES.items():
        fname, excerpt = load_markdown_summary(str(doc_path))
        rel = doc_path.relative_to(PROJECT.parent) if doc_path.is_relative_to(PROJECT.parent) else doc_path
        with st.expander(f"{label} — `{fname}`"):
            st.markdown(excerpt)
            st.markdown(f"Full file: `{rel.as_posix()}`")

    st.divider()
    st.markdown(
        "Related app: [Evidence assistant (Q&A)](https://asthma-evidence-assistant.streamlit.app/) "
        "· Source: "
        "[`projects/asthma-air-pollution/v2` on `main`]"
        "(https://github.com/bodorkosgellert/Ironhack/tree/main/projects/asthma-air-pollution/v2)"
    )


if __name__ == "__main__":
    main()
