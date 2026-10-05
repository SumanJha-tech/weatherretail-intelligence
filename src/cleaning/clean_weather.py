import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_weather(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["city"] = df["city"].str.strip().str.title()

    df = df.drop_duplicates(subset=["date", "city"])
    df = df.sort_values(["city", "date"])

    for col in ["precipitation_mm", "snowfall_cm"]:
        df[col] = df[col].clip(lower=0)

    # Fill small gaps (a missing day here and there) using the previous day's value, per city.
    weather_cols = ["temp_max_c", "temp_min_c", "precipitation_mm", "snowfall_cm", "windspeed_max_kmh"]
    filled_count = df[weather_cols].isna().sum().sum()
    df[weather_cols] = df.groupby("city")[weather_cols].ffill()
    if filled_count:
        logger.info(f"Filled {int(filled_count)} missing weather values using the previous day's reading.")

    return df