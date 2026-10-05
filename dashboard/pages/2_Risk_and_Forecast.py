import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.express as px

from src.db.queries import load_risk_forecast, load_forecast_weather

st.set_page_config(page_title="Risk & Forecast", layout="wide")
st.title("This Week's Risk — What Should We Do?")

forecast_weather = load_forecast_weather()
st.subheader("7-Day Weather Forecast by City")
cols = st.columns(len(forecast_weather["city"].unique()) or 1)
for i, city in enumerate(sorted(forecast_weather["city"].unique())):
    city_df = forecast_weather[forecast_weather["city"] == city]
    with cols[i % len(cols)]:
        st.markdown(f"**{city}**")
        for _, row in city_df.iterrows():
            st.write(f"{row['date']}: {row['temp_max_c']}C, {row['precipitation_mm']}mm rain, {row['snowfall_cm']}cm snow")

st.divider()

risk_df = load_risk_forecast()
if risk_df.empty:
    st.warning("No risk scores found yet. Run `python -m src.analysis.risk_scoring` first.")
    st.stop()

st.subheader("Risk Score Table (Highest Risk First)")


def _risk_color(score):
    if score >= 60:
        return "background-color: #f8d7da"  # red
    if score >= 30:
        return "background-color: #fff3cd"  # yellow
    return "background-color: #d4edda"      # green


styled = risk_df.style.applymap(lambda v: _risk_color(v) if isinstance(v, (int, float)) else "", subset=["risk_score"])
st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption("Red = act now. This table is the single most useful output of the whole project — a manager can follow it directly.")

st.divider()
st.subheader("Total Revenue-at-Risk by Store")
by_store = risk_df.groupby("store_id")["risk_score"].sum().reset_index()
fig = px.bar(by_store, x="store_id", y="risk_score", labels={"risk_score": "Summed Risk Score"})
st.plotly_chart(fig, use_container_width=True)