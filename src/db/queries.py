"""Dashboard reads. Cached for 10 minutes so a filter change does not re-query Postgres.

When Postgres is unreachable (Streamlit Cloud has no database) every read falls back to the
CSV tables in data/snapshot, written by `python -m src.db.export_snapshot`.
"""
import os

import pandas as pd
import streamlit as st
from config.settings import DATE_END, PROCESSED_DIR, SNAPSHOT_DIR
from src.db.connection import get_engine


@st.cache_resource
def _use_database() -> bool:
    try:
        with get_engine().connect():
            return True
    except Exception:
        return False


def _snapshot(table: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(SNAPSHOT_DIR, f"{table}.csv"))


@st.cache_data(ttl=600)
def load_sales_weather(start_date, end_date, stores: list[str], products: list[str]) -> pd.DataFrame:
    if not _use_database():
        return _snapshot_sales_weather(start_date, end_date, stores, products)
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
    if not _use_database():
        return _snapshot("dim_store").sort_values("store_id").reset_index(drop=True)
    return pd.read_sql("SELECT * FROM dim_store ORDER BY store_id", get_engine())


@st.cache_data(ttl=600)
def load_products() -> pd.DataFrame:
    if not _use_database():
        return _snapshot("dim_product").sort_values("product_category").reset_index(drop=True)
    return pd.read_sql("SELECT * FROM dim_product ORDER BY product_category", get_engine())


@st.cache_data(ttl=600)
def load_sensitivity_scores() -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, "sensitivity_scores.csv")
    return pd.read_csv(path)


@st.cache_data(ttl=600)
def load_risk_forecast() -> pd.DataFrame:
    if not _use_database():
        return _snapshot("fact_risk_forecast").sort_values("risk_score", ascending=False).reset_index(drop=True)
    return pd.read_sql("SELECT * FROM fact_risk_forecast ORDER BY risk_score DESC", get_engine())


@st.cache_data(ttl=600)
def load_forecast_weather() -> pd.DataFrame:
    if not _use_database():
        weather = _snapshot("fact_weather_daily")
        # The snapshot is frozen, so "today or later" is anything past the history window.
        return weather[weather["date"] > DATE_END.isoformat()].sort_values(["city", "date"]).reset_index(drop=True)
    return pd.read_sql(
        "SELECT * FROM fact_weather_daily WHERE date >= CURRENT_DATE ORDER BY city, date", get_engine()
    )


def _snapshot_sales_weather(start_date, end_date, stores, products) -> pd.DataFrame:
    """pandas version of vw_sales_weather."""
    sales = _snapshot("fact_sales")
    sales["date"] = pd.to_datetime(sales["date"]).dt.date
    sales = sales[
        (sales["date"] >= start_date) & (sales["date"] <= end_date)
        & sales["store_id"].isin(stores) & sales["product_category"].isin(products)
    ]
    dim_store = _snapshot("dim_store")[["store_id", "city", "region"]]
    dim_product = _snapshot("dim_product")[["product_category", "department", "primary_weather_driver"]]
    dim_date = _snapshot("dim_date")[["date", "day_of_week", "is_weekend", "season"]]
    dim_date["date"] = pd.to_datetime(dim_date["date"]).dt.date
    weather = _snapshot("fact_weather_daily")
    weather["date"] = pd.to_datetime(weather["date"]).dt.date
    return (
        sales.merge(dim_store, on="store_id")
        .merge(dim_product, on="product_category")
        .merge(dim_date, on="date")
        .merge(weather, on=["date", "city"])
    )
