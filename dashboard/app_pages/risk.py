import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import plotly.graph_objects as go
import streamlit as st

from src.dashboard_ui import CHART_CONFIG, MINT, RISK_CELL_STYLES, polish
from src.db.queries import load_forecast_weather, load_risk_forecast

st.title("Risk and forecast")
st.caption("What is each city forecast to do, and which store–category pairs need a reorder?")

forecast_weather = load_forecast_weather()
st.subheader("Seven-day forecast")

if forecast_weather.empty:
    st.caption("No forecast days are loaded yet. Weather rows dated today or later belong in fact_weather_daily.")
else:
    with st.container(horizontal=True):
        for city in sorted(forecast_weather["city"].unique()):
            city_df = forecast_weather[forecast_weather["city"] == city].sort_values("date")
            temps = [float(v) for v in city_df["temp_max_c"].tolist() if v is not None]
            rain = float(city_df["precipitation_mm"].sum())
            snow = float(city_df["snowfall_cm"].sum())
            with st.container(border=True):
                st.metric(
                    city,
                    f"{temps[-1]:.0f}°C" if temps else "n/a",
                    help="Latest forecast daily high. The line is the rest of the window.",
                    chart_data=temps if len(temps) >= 2 else None,
                    chart_type="line",
                )
                st.caption(f"{rain:.1f} mm rain · {snow:.1f} cm snow")

    st.dataframe(
        forecast_weather.sort_values(["city", "date"]),
        width="stretch",
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "city": st.column_config.TextColumn("City"),
            "temp_max_c": st.column_config.NumberColumn("High (°C)", format="%.1f"),
            "temp_min_c": st.column_config.NumberColumn("Low (°C)", format="%.1f"),
            "precipitation_mm": st.column_config.NumberColumn("Rain (mm)", format="%.1f"),
            "snowfall_cm": st.column_config.NumberColumn("Snow (cm)", format="%.1f"),
            "windspeed_max_kmh": st.column_config.NumberColumn("Wind (km/h)", format="%.1f"),
        },
    )

risk_df = load_risk_forecast()
if risk_df.empty:
    st.warning("No risk scores found yet. Run `python -m src.analysis.risk_scoring` first.")
    st.stop()

high_n = int((risk_df["risk_score"] >= 60).sum())
medium_n = int(((risk_df["risk_score"] >= 30) & (risk_df["risk_score"] < 60)).sum())
low_n = int((risk_df["risk_score"] < 30).sum())

st.subheader("Action list")
with st.container(horizontal=True):
    st.metric("Reorder now", high_n, help="Score 60–100.", icon=":material/warning:", border=True)
    st.metric("Watch", medium_n, help="Score 30–59.", icon=":material/thermostat:", border=True)
    st.metric("No action", low_n, help="Score 0–29.", icon=":material/check:", border=True)


def _risk_color(score):
    """Same 60 / 30 bands as recommend_action in risk_scoring."""
    if score >= 60:
        return RISK_CELL_STYLES["high"]
    if score >= 30:
        return RISK_CELL_STYLES["medium"]
    return RISK_CELL_STYLES["low"]


styled = risk_df.style.map(
    lambda v: _risk_color(v) if isinstance(v, (int, float)) else "",
    subset=["risk_score"],
)
st.dataframe(styled, width="stretch", hide_index=True)
st.caption("A score of 60 or above is a reorder. 30 to 59 is a watch. Below 30 needs no action.")

with st.container(border=True):
    st.subheader("Risk by store")
    by_store = risk_df.groupby("store_id")["risk_score"].sum().reset_index()
    fig = go.Figure(go.Bar(
        x=by_store["store_id"],
        y=by_store["risk_score"],
        marker_color=MINT,
        name="Summed risk",
    ))
    fig.update_layout(xaxis_title="Store", yaxis_title="Summed risk score")
    st.plotly_chart(polish(fig), width="stretch", theme="streamlit", config=CHART_CONFIG)
