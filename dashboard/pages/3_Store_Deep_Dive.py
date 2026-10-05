import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import streamlit as st
import plotly.express as px

from src.db.queries import load_sales_weather, load_stores, load_products
from src.analysis.kpis import total_revenue, stockout_rate_pct
from config.settings import DATE_START, DATE_END

st.set_page_config(page_title="Store Deep Dive", layout="wide")
st.title("Store Deep Dive")

stores_df = load_stores()
products_df = load_products()
chosen_store = st.selectbox("Choose a store", stores_df["store_id"].tolist())

df = load_sales_weather(DATE_START, DATE_END, [chosen_store], products_df["product_category"].tolist())
df["date"] = pd.to_datetime(df["date"])

col1, col2 = st.columns(2)
col1.metric("Total Revenue", f"${total_revenue(df):,.0f}")
col2.metric("Stockout Rate", f"{stockout_rate_pct(df)}%")

st.subheader("Stockout Calendar Heatmap")
heat = df.groupby("date")["stockout_flag"].max().reset_index()
heat["week"] = heat["date"].dt.isocalendar().week
heat["weekday"] = heat["date"].dt.day_name()
pivot = heat.pivot_table(index="weekday", columns="week", values="stockout_flag", aggfunc="max").fillna(0)
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
pivot = pivot.reindex(weekday_order)

fig = px.imshow(pivot, color_continuous_scale=["#eeeeee", "#d62728"], aspect="auto",
                 labels=dict(x="Week of Year", y="Day of Week", color="Stockout"))
st.plotly_chart(fig, use_container_width=True)
st.caption("Red cells show exactly when this store ran out of stock — patterns like 'every summer weekend' jump out here.")

st.subheader("Sales by Product")
by_product = df.groupby("product_category").agg(revenue=("revenue", "sum"), units_sold=("units_sold", "sum")).reset_index()
st.dataframe(by_product.sort_values("revenue", ascending=False), use_container_width=True, hide_index=True)