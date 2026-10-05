import os
import pandas as pd
from sqlalchemy import text

from config.settings import RAW_SALES_DIR, WEATHER_CACHE_DIR, PROCESSED_DIR
from src.db.connection import get_engine
from src.cleaning.clean_sales import clean_sales
from src.cleaning.clean_weather import clean_weather
from src.quality.data_quality_checks import check_sales, check_weather, log_report
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_dataframe(df: pd.DataFrame, table_name: str) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        df.to_sql(table_name, conn, if_exists="append", index=False)
    logger.info(f"Loaded {len(df):,} rows into '{table_name}'.")


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    dim_date = pd.read_csv(os.path.join(RAW_SALES_DIR, "dim_date.csv"), parse_dates=["date"])
    dim_store = pd.read_csv(os.path.join(RAW_SALES_DIR, "dim_store.csv"))
    dim_product = pd.read_csv(os.path.join(RAW_SALES_DIR, "dim_product.csv"))
    raw_sales = pd.read_csv(os.path.join(RAW_SALES_DIR, "fact_sales.csv"))
    raw_weather = pd.read_csv(os.path.join(WEATHER_CACHE_DIR, "all_cities_history.csv"))

    clean_sales_df = clean_sales(raw_sales)
    clean_weather_df = clean_weather(raw_weather)

    sales_report = check_sales(clean_sales_df, dim_store, dim_product, dim_date)
    log_report("fact_sales", sales_report)
    weather_report = check_weather(clean_weather_df)
    log_report("fact_weather_daily", weather_report)

    clean_sales_df.to_csv(os.path.join(PROCESSED_DIR, "fact_sales_clean.csv"), index=False)
    clean_weather_df.to_csv(os.path.join(PROCESSED_DIR, "fact_weather_clean.csv"), index=False)

    # Load in dependency order: dimension tables first, then fact tables.
    load_dataframe(dim_date, "dim_date")
    load_dataframe(dim_store, "dim_store")
    load_dataframe(dim_product, "dim_product")
    load_dataframe(clean_sales_df, "fact_sales")
    load_dataframe(clean_weather_df, "fact_weather_daily")

    logger.info("All tables loaded successfully.")


if __name__ == "__main__":
    main()