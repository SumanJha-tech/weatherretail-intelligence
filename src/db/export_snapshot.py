"""Dump the warehouse tables to data/snapshot so the dashboard can run without Postgres (e.g. Streamlit Cloud)."""
import os

import pandas as pd

from config.settings import SNAPSHOT_DIR
from src.db.connection import get_engine

TABLES = ["dim_date", "dim_store", "dim_product", "fact_sales", "fact_weather_daily", "fact_risk_forecast"]


def main():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    engine = get_engine()
    for table in TABLES:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        df.to_csv(os.path.join(SNAPSHOT_DIR, f"{table}.csv"), index=False)
        print(f"{table}: {len(df):,} rows")


if __name__ == "__main__":
    main()
