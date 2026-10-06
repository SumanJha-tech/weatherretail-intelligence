import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

from config.settings import DATE_END, DATE_START
from src.dashboard_ui import BRONZE, CHART_CONFIG, MINT, SENSITIVITY_COLORS, driver_label, polish
from src.db.queries import load_products, load_sales_weather, load_sensitivity_scores, load_stores

st.title("Weather sensitivity")
st.caption("Which categories move with weather, and by how many units a day?")

sensitivity_df = load_sensitivity_scores()
counts = sensitivity_df["sensitivity_label"].value_counts()

with st.container(horizontal=True):
    st.badge(f"{int(counts.get('High', 0))} high", icon=":material/warning:", color="red")
    st.badge(f"{int(counts.get('Medium', 0))} medium", icon=":material/thermostat:", color="orange")
    st.badge(f"{int(counts.get('Low', 0))} low", icon=":material/check:", color="green")

with st.container(border=True):
    st.subheader("Correlation by category")
    fig = px.bar(
        sensitivity_df.sort_values("correlation_r", key=abs),
        x="correlation_r",
        y="product_category",
        color="sensitivity_label",
        color_discrete_map=SENSITIVITY_COLORS,
        orientation="h",
        labels={
            "correlation_r": "Correlation with weather (r)",
            "product_category": "Category",
            "sensitivity_label": "Sensitivity",
        },
    )
    fig.update_layout(height=420)
    st.plotly_chart(polish(fig), width="stretch", theme="streamlit", config=CHART_CONFIG)
    st.caption("Distance from zero is the strength of the co-movement. The sign is the direction.")

st.subheader("Sales against the weather driver")

stores_df, products_df = load_stores(), load_products()
chosen_product = st.selectbox("Product", products_df["product_category"].tolist())

df = load_sales_weather(DATE_START, DATE_END, stores_df["store_id"].tolist(), [chosen_product])
driver_row = sensitivity_df[sensitivity_df["product_category"] == chosen_product].iloc[0]
driver = driver_row["weather_driver"]
axis_label = driver_label(driver)

plot_df = df[[driver, "units_sold"]].dropna()
fig2 = px.scatter(
    plot_df,
    x=driver,
    y="units_sold",
    opacity=0.55,
    labels={driver: axis_label, "units_sold": "Units sold"},
    color_discrete_sequence=[MINT],
)
# Same estimator as the sensitivity job. Plotly's trendline="ols" imports
# statsmodels, which this project does not depend on.
if len(plot_df) >= 2:
    x = plot_df[driver].to_numpy(dtype=float)
    y = plot_df["units_sold"].to_numpy(dtype=float)
    fit = LinearRegression().fit(x.reshape(-1, 1), y)
    x_line = np.array([x.min(), x.max()])
    fig2.add_trace(go.Scatter(
        x=x_line,
        y=fit.predict(x_line.reshape(-1, 1)),
        mode="lines",
        name="Fitted line",
        line=dict(color=BRONZE, width=2),
    ))

with st.container(border=True):
    st.plotly_chart(polish(fig2), width="stretch", theme="streamlit", config=CHART_CONFIG)

slope = driver_row["slope_units_per_unit_weather"]
label = driver_row["sensitivity_label"]
badge_color = {"High": "red", "Medium": "orange", "Low": "green"}.get(label, "gray")

with st.container(border=True):
    st.badge(label, color=badge_color)
    st.markdown(
        f"For every 1-unit rise in `{driver}`, **{chosen_product}** "
        f"changes by **{slope:+.2f} units/day**."
    )
    st.caption(f"Correlation r = {driver_row['correlation_r']}. The slope is the sensitivity job's OLS estimate.")

st.subheader("Score table")
st.dataframe(
    sensitivity_df,
    width="stretch",
    hide_index=True,
    column_config={
        "product_category": st.column_config.TextColumn("Category"),
        "weather_driver": st.column_config.TextColumn("Driver"),
        "correlation_r": st.column_config.NumberColumn("Correlation (r)", format="%.3f"),
        "p_value": st.column_config.NumberColumn("p-value", format="%.5f"),
        "slope_units_per_unit_weather": st.column_config.NumberColumn("Units per driver unit", format="%+.3f"),
        "sensitivity_label": st.column_config.TextColumn("Label"),
    },
)
