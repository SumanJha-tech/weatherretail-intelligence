import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import DATE_END, DATE_START
from src.analysis.kpis import stockout_rate_pct, total_revenue
from src.dashboard_ui import CHART_CONFIG, HEATMAP_SCALE, monthly_values, polish
from src.db.queries import load_products, load_sales_weather, load_stores

st.title("Store deep dive")
st.caption("Revenue, stockouts, and category contribution for one location.")

stores_df = load_stores()
products_df = load_products()
chosen_store = st.selectbox("Store", stores_df["store_id"].tolist())

df = load_sales_weather(DATE_START, DATE_END, [chosen_store], products_df["product_category"].tolist())
df["date"] = pd.to_datetime(df["date"])

revenue_trend = monthly_values(df, "revenue", how="sum")
stockout_trend = monthly_values(df.assign(stockout_flag=df["stockout_flag"].astype(float)), "stockout_flag", how="mean")
if stockout_trend is not None:
    stockout_trend = [v * 100 for v in stockout_trend]

with st.container(horizontal=True):
    st.metric(
        "Total revenue",
        f"${total_revenue(df):,.0f}",
        help="Sum of units × price for this store.",
        icon=":material/payments:",
        border=True,
        chart_data=revenue_trend,
        chart_type="area",
    )
    st.metric(
        "Stockout rate",
        f"{stockout_rate_pct(df)}%",
        help="Share of category-days with a stockout.",
        icon=":material/inventory_2:",
        border=True,
        chart_data=stockout_trend,
        chart_type="line",
    )

with st.container(border=True):
    st.subheader("Stockout calendar")
    heat = df.groupby("date")["stockout_flag"].max().reset_index()
    heat["week"] = heat["date"].dt.isocalendar().week
    heat["weekday"] = heat["date"].dt.day_name()
    pivot = heat.pivot_table(index="weekday", columns="week", values="stockout_flag", aggfunc="max").fillna(0)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(weekday_order)

    fig = px.imshow(
        pivot,
        color_continuous_scale=HEATMAP_SCALE,
        aspect="auto",
        labels=dict(x="Week of year", y="Day of week", color="Stockout"),
    )
    fig.update_layout(height=420)
    st.plotly_chart(polish(fig), width="stretch", theme="streamlit", config=CHART_CONFIG)
    st.caption("A rose cell is a day this store stocked out of at least one category.")

st.subheader("Sales by category")
by_product = df.groupby("product_category").agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum")).reset_index()
st.dataframe(
    by_product.sort_values("revenue", ascending=False),
    width="stretch",
    hide_index=True,
    column_config={
        "product_category": st.column_config.TextColumn("Category"),
        "revenue": st.column_config.NumberColumn("Revenue", format="dollar"),
        "units_sold": st.column_config.NumberColumn("Units sold", format="localized"),
    },
)
