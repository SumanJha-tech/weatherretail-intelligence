import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import plotly.express as px
import numpy as np

from src.db.queries import load_sales_weather, load_stores, load_products, load_sensitivity_scores
from config.settings import DATE_START, DATE_END

st.set_page_config(page_title="Weather Sensitivity", layout="wide")
st.title("Which Products Are Weather-Sensitive?")

sensitivity_df = load_sensitivity_scores()

st.subheader("Sensitivity Score by Product")
color_map = {"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c"}
fig = px.bar(
    sensitivity_df.sort_values("correlation_r", key=abs),
    x="correlation_r", y="product_category", color="sensitivity_label",
    color_discrete_map=color_map, orientation="h",
    labels={"correlation_r": "Correlation with weather (r)", "product_category": "Product"},
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Bars further from zero (either direction) mean weather explains more of that product's sales swings.")

st.divider()
st.subheader("Sales vs. Weather — Pick a Product")

stores_df, products_df = load_stores(), load_products()
chosen_product = st.selectbox("Product", products_df["product_category"].tolist())

df = load_sales_weather(DATE_START, DATE_END, stores_df["store_id"].tolist(), [chosen_product])
driver_row = sensitivity_df[sensitivity_df["product_category"] == chosen_product].iloc[0]
driver = driver_row["weather_driver"]

fig2 = px.scatter(df, x=driver, y="units_sold", trendline="ols", opacity=0.4,
                   labels={driver: driver, "units_sold": "Units Sold"})
st.plotly_chart(fig2, use_container_width=True)

slope = driver_row["slope_units_per_unit_weather"]
st.write(f"**In plain English:** for every 1-unit rise in `{driver}`, "
         f"**{chosen_product}** sales change by about **{slope:+.2f} units/day** "
         f"(correlation r = {driver_row['correlation_r']}, sensitivity: **{driver_row['sensitivity_label']}**).")

st.divider()
st.subheader("All Products — Full Table")
st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)