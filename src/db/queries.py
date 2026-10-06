"""Dashboard reads. Cached for 10 minutes so a filter change does not re-query Postgres."""
import os

import pandas as pd
import streamlit as st
from config.settings import PROCESSED_DIR
from src.db.connection import get_engine


@st.cache_data(ttl=600)
def load_sales_weather(start_date, end_date, stores: list[str], products: list[str]) -> pd.DataFrame:
    engine = get_engine()
    query = """
        SELECT * FROM vw_sales_weather
        WHERE date BETWEEN %(start)s AND %(end)s
          AND store_id = ANY(%(stores)s)
          AND product_category = ANY(%(products)s)
    """
    return pd.read_sql(query, engine, params={"start": start_date, "end": end_date, "stores": stores, "products": products})


@st.cache_data(ttl=600)
def load_stores() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM dim_store ORDER BY store_id", get_engine())


@st.cache_data(ttl=600)
def load_products() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM dim_product ORDER BY product_category", get_engine())


@st.cache_data(ttl=600)
def load_sensitivity_scores() -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, "sensitivity_scores.csv")
    return pd.read_csv(path)


@st.cache_data(ttl=600)
def load_risk_forecast() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM fact_risk_forecast ORDER BY risk_score DESC", get_engine())


@st.cache_data(ttl=600)
def load_forecast_weather() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM fact_weather_daily WHERE date >= CURRENT_DATE ORDER BY city, date", get_engine()
    )