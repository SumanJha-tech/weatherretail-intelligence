"""Open-Meteo history and a 7-day forecast for each store city.

History is cached until the file is deleted: the archive for a closed date
does not change. A forecast file is reused for six hours, then fetched again.
After three failed attempts the city falls back to data/sample/weather_backup.csv.
"""
import os
import time
import requests
import pandas as pd

from config.settings import STORES, DATE_START, DATE_END, WEATHER_CACHE_DIR, SAMPLE_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)
FORECAST_CACHE_TTL_SECONDS = 6 * 60 * 60

HISTORY_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,windspeed_10m_max"
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 3


def _call_with_retries(url: str, params: dict) -> dict | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS)
    logger.error(f"All {MAX_RETRIES} attempts failed for {url}. Giving up.")
    return None


def _json_to_dataframe(payload: dict, city: str) -> pd.DataFrame:
    daily = payload["daily"]
    return pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "city": city,
        "temp_max_c": daily["temperature_2m_max"],
        "temp_min_c": daily["temperature_2m_min"],
        "precipitation_mm": daily["precipitation_sum"],
        "snowfall_cm": daily["snowfall_sum"],
        "windspeed_max_kmh": daily["windspeed_10m_max"],
    })


def fetch_history_for_city(city: str, lat: float, lon: float) -> pd.DataFrame:
    cache_path = os.path.join(WEATHER_CACHE_DIR, f"{city.replace(' ', '_')}_history.csv")
    if os.path.exists(cache_path):
        logger.info(f"[{city}] Using cached history (no API call needed).")
        return pd.read_csv(cache_path, parse_dates=["date"])

    logger.info(f"[{city}] Calling Open-Meteo history API...")
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": DATE_START.isoformat(), "end_date": DATE_END.isoformat(),
        "daily": DAILY_FIELDS, "timezone": "auto",
    }
    payload = _call_with_retries(HISTORY_URL, params)

    if payload is None:
        logger.warning(f"[{city}] API unavailable -> falling back to sample backup data.")
        return _load_backup_for_city(city)

    df = _json_to_dataframe(payload, city)
    os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def fetch_forecast_for_city(city: str, lat: float, lon: float) -> pd.DataFrame:
    cache_path = os.path.join(WEATHER_CACHE_DIR, f"{city.replace(' ', '_')}_forecast.csv")
    if os.path.exists(cache_path):
        age_seconds = time.time() - os.path.getmtime(cache_path)
        if age_seconds < FORECAST_CACHE_TTL_SECONDS:
            logger.info(f"[{city}] Using cached forecast (still fresh).")
            return pd.read_csv(cache_path, parse_dates=["date"])

    logger.info(f"[{city}] Calling Open-Meteo forecast API...")
    params = {"latitude": lat, "longitude": lon, "daily": DAILY_FIELDS, "forecast_days": 7, "timezone": "auto"}
    payload = _call_with_retries(FORECAST_URL, params)

    if payload is None:
        logger.warning(f"[{city}] Forecast API unavailable -> falling back to sample backup data.")
        return _load_backup_for_city(city).tail(7)

    df = _json_to_dataframe(payload, city)
    os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def _load_backup_for_city(city: str) -> pd.DataFrame:
    backup_path = os.path.join(SAMPLE_DIR, "weather_backup.csv")
    if not os.path.exists(backup_path):
        raise FileNotFoundError(
            f"No cache, no API response, and no backup at {backup_path}. "
            "Place a city-level weather CSV there to run offline."
        )
    df = pd.read_csv(backup_path, parse_dates=["date"])
    return df[df["city"] == city].copy()


def main():
    history_frames, forecast_frames = [], []
    for store in STORES:
        history_frames.append(fetch_history_for_city(store["city"], store["latitude"], store["longitude"]))
        forecast_frames.append(fetch_forecast_for_city(store["city"], store["latitude"], store["longitude"]))

    history_df = pd.concat(history_frames, ignore_index=True)
    forecast_df = pd.concat(forecast_frames, ignore_index=True)

    os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)
    history_df.to_csv(os.path.join(WEATHER_CACHE_DIR, "all_cities_history.csv"), index=False)
    forecast_df.to_csv(os.path.join(WEATHER_CACHE_DIR, "all_cities_forecast.csv"), index=False)

    logger.info(f"Done. History rows: {len(history_df):,}. Forecast rows: {len(forecast_df):,}.")


if __name__ == "__main__":
    main()