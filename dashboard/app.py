import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from datetime import date

from src.db.queries import load_sales_weather, load_stores, load_products
from src.analysis.kpis import total_revenue, stockout_rate_pct, inventory_turnover
from config.settings import DATE_START, DATE_END

st.set_page_config(page_title="WeatherRetail Intelligence", layout="wide")
st.title("WeatherRetail Intelligence — Overview")
st.caption("Does weather really move our sales, and is it costing us money?")

# --- Sidebar filters ---
stores_df = load_stores()
products_df = load_products()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input("Date range", value=(DATE_START, DATE_END), min_value=DATE_START, max_value=DATE_END)
    selected_stores = st.multiselect("Stores", stores_df["store_id"].tolist(), default=stores_df["store_id"].tolist())
    selected_products = st.multiselect("Products", products_df["product_category"].tolist(), default=products_df["product_category"].tolist())

start_date, end_date = date_range if len(date_range) == 2 else (DATE_START, DATE_END)
df = load_sales_weather(start_date, end_date, selected_stores or stores_df["store_id"].tolist(),
                         selected_products or products_df["product_category"].tolist())

if df.empty:
    st.warning("No data for this filter combination. Try widening the date range or selecting more stores/products.")
    st.stop()

# --- KPI cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue(df):,.0f}")
col2.metric("Stockout Rate", f"{stockout_rate_pct(df)}%")
col3.metric("Inventory Turnover", f"{inventory_turnover(df)}x")
avg_temp = round(df["temp_max_c"].mean(), 1)
col4.metric("Avg Daily High Temp", f"{avg_temp} C")

st.divider()

# --- Revenue and weather over time ---
st.subheader("Revenue vs. Average Temperature Over Time")
daily = df.groupby("date").agg(revenue=("revenue", "sum"), avg_temp=("temp_max_c", "mean")).reset_index()

fig = go.Figure()
fig.add_bar(x=daily["date"], y=daily["revenue"], name="Revenue ($)", yaxis="y1")
fig.add_scatter(x=daily["date"], y=daily["avg_temp"], name="Avg Temp (C)", yaxis="y2", line=dict(color="orange"))
fig.update_layout(
    yaxis=dict(title="Revenue ($)"),
    yaxis2=dict(title="Avg Temp (C)", overlaying="y", side="right"),
    legend=dict(orientation="h"),
)
st.plotly_chart(fig, use_container_width=True)
st.caption("This chart answers: does revenue visibly move together with temperature, before we even run statistics?")