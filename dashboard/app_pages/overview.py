import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import plotly.graph_objects as go
import streamlit as st

from config.settings import DATE_END, DATE_START
from src.analysis.kpis import inventory_turnover, stockout_rate_pct, total_revenue
from src.dashboard_ui import BRONZE, CHART_CONFIG, LAVENDER, MINT, monthly_values, polish
from src.db.queries import load_products, load_sales_weather, load_stores

st.title("Overview")
st.caption("Does weather move sales in this slice, and what does that cost?")

stores_df = load_stores()
products_df = load_products()

with st.sidebar:
    st.header("Filters")
    st.caption("Date, store, and category. Every figure on this page uses this slice.")
    date_range = st.date_input(
        "Date range",
        value=(DATE_START, DATE_END),
        min_value=DATE_START,
        max_value=DATE_END,
    )
    selected_stores = st.multiselect(
        "Stores",
        stores_df["store_id"].tolist(),
        default=stores_df["store_id"].tolist(),
    )
    selected_products = st.multiselect(
        "Products",
        products_df["product_category"].tolist(),
        default=products_df["product_category"].tolist(),
    )

start_date, end_date = date_range if len(date_range) == 2 else (DATE_START, DATE_END)
df = load_sales_weather(
    start_date,
    end_date,
    selected_stores or stores_df["store_id"].tolist(),
    selected_products or products_df["product_category"].tolist(),
)

if df.empty:
    st.warning("No data for this filter combination. Try widening the date range or selecting more stores/products.")
    st.stop()

revenue_trend = monthly_values(df, "revenue", how="sum")
stockout_trend = monthly_values(df.assign(stockout_flag=df["stockout_flag"].astype(float)), "stockout_flag", how="mean")
temp_trend = monthly_values(df, "temp_max_c", how="mean")
if stockout_trend is not None:
    stockout_trend = [v * 100 for v in stockout_trend]

avg_temp = round(df["temp_max_c"].mean(), 1)

with st.container(horizontal=True):
    st.metric(
        "Total revenue",
        f"${total_revenue(df):,.0f}",
        help="Sum of units × price in the filtered slice.",
        icon=":material/payments:",
        border=True,
        chart_data=revenue_trend,
        chart_type="area",
    )
    st.metric(
        "Stockout rate",
        f"{stockout_rate_pct(df)}%",
        help="Share of store–category–days with a stockout.",
        icon=":material/inventory_2:",
        border=True,
        chart_data=stockout_trend,
        chart_type="line",
    )
    st.metric(
        "Inventory turnover",
        f"{inventory_turnover(df)}x",
        help="Units sold ÷ average units on hand.",
        icon=":material/autorenew:",
        border=True,
    )
    st.metric(
        "Avg daily high",
        f"{avg_temp}°C",
        help="Mean of daily high temperature in the filtered slice.",
        icon=":material/device_thermostat:",
        border=True,
        chart_data=temp_trend,
        chart_type="line",
    )

daily = df.groupby("date").agg(revenue=("revenue", "sum"), avg_temp=("temp_max_c", "mean")).reset_index()
by_store = df.groupby("store_id", as_index=False)["revenue"].sum().sort_values("revenue", ascending=True)

trend_col, store_col = st.columns([1.45, 1])
with trend_col:
    with st.container(border=True):
        st.subheader("Revenue and temperature")
        fig = go.Figure()
        fig.add_bar(x=daily["date"], y=daily["revenue"], name="Revenue ($)", marker_color=MINT, yaxis="y1")
        fig.add_scatter(
            x=daily["date"],
            y=daily["avg_temp"],
            name="Avg temp (°C)",
            yaxis="y2",
            line=dict(color=BRONZE, width=2),
        )
        fig.update_layout(
            yaxis=dict(title="Revenue ($)"),
            yaxis2=dict(title="Avg temp (°C)", overlaying="y", side="right"),
        )
        st.plotly_chart(polish(fig), width="stretch", theme="streamlit", config=CHART_CONFIG)
        st.caption("Does revenue move with temperature, before any statistical model is applied?")

with store_col:
    with st.container(border=True):
        st.subheader("Revenue by store")
        store_fig = go.Figure(go.Bar(
            x=by_store["revenue"],
            y=by_store["store_id"],
            orientation="h",
            marker_color=LAVENDER,
            name="Revenue",
        ))
        store_fig.update_layout(xaxis_title="Revenue ($)", yaxis_title="")
        st.plotly_chart(polish(store_fig), width="stretch", theme="streamlit", config=CHART_CONFIG)
        st.caption("Same slice, split by store. Climate is what separates these locations.")
