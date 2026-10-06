"""Presentation helpers for the dashboard. KPI formulas stay in src.analysis.kpis."""
import pandas as pd
import plotly.graph_objects as go

CHART_CONFIG = {"displaylogo": False}

DRIVER_LABELS = {
    "temp_max_c": "Daily high (°C)",
    "precipitation_mm": "Precipitation (mm)",
    "snowfall_cm": "Snowfall (cm)",
}

# Sage, bronze, and lavender. Dark enough to read on white.
MINT = "#2F7A68"
BRONZE = "#8A5A16"
LAVENDER = "#6B5EA8"
ROSE = "#B24D62"
SENSITIVITY_COLORS = {"High": ROSE, "Medium": BRONZE, "Low": MINT}
HEATMAP_SCALE = ["#F3EFE8", ROSE]
RISK_CELL_STYLES = {
    "high": "background-color: #F8E4E6; color: #7A2430",
    "medium": "background-color: #F8EFD6; color: #7A5410",
    "low": "background-color: #E5F3EC; color: #1E5C40",
}


def driver_label(column: str) -> str:
    return DRIVER_LABELS.get(column, column)


def monthly_values(df: pd.DataFrame, column: str, how: str = "sum") -> list[float] | None:
    """Evenly spaced monthly points for a metric sparkline. None when a line cannot be drawn."""
    if df.empty or column not in df.columns:
        return None
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"])
    grouped = work.groupby(work["date"].dt.to_period("M"))[column]
    series = grouped.mean() if how == "mean" else grouped.sum()
    values = [float(v) for v in series.tolist() if pd.notna(v)]
    return values if len(values) >= 2 else None


def polish(fig: go.Figure) -> go.Figure:
    """Transparent chart chrome so Plotly sits inside a bordered card."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(gridcolor="rgba(31,26,23,0.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(31,26,23,0.08)", zeroline=False)
    return fig
