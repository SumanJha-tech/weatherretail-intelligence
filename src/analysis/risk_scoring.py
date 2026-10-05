import os
import pandas as pd
import numpy as np
from sqlalchemy import text

from config.settings import PROCESSED_DIR
from src.db.connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


def compute_weather_anomaly_z(forecast_value: float, historical_mean: float, historical_std: float) -> float:
    if historical_std == 0 or pd.isna(historical_std):
        return 0.0
    return (forecast_value - historical_mean) / historical_std


def compute_inventory_pressure(current_inventory: float, healthy_inventory: float) -> float:
    """1.0 = almost no stock left, 0.0 = plenty of stock. Clipped to [0, 1]."""
    if healthy_inventory == 0:
        return 0.0
    pressure = 1 - (current_inventory / healthy_inventory)
    return float(np.clip(pressure, 0, 1))


def compute_risk_score(weather_anomaly_z: float, sensitivity_score: float, inventory_pressure: float) -> float:
    score = abs(weather_anomaly_z) * sensitivity_score * inventory_pressure * (100 / 3)
    return round(float(np.clip(score, 0, 100)), 2)


def recommend_action(risk_score: float) -> str:
    if risk_score >= 60:
        return "High risk of running out - reorder now"
    if risk_score >= 30:
        return "Medium risk - watch closely, consider reordering soon"
    return "Low risk - no action needed"


def main():
    engine = get_engine()

    sensitivity_df = pd.read_csv(os.path.join(PROCESSED_DIR, "sensitivity_scores.csv"))
    forecast_df = pd.read_sql(
        "SELECT city, date, temp_max_c, precipitation_mm, snowfall_cm FROM fact_weather_daily "
        "WHERE date >= CURRENT_DATE ORDER BY date",
        engine,
    )
    history_df = pd.read_sql("SELECT city, date, temp_max_c, precipitation_mm, snowfall_cm FROM fact_weather_daily", engine)
    stores_df = pd.read_sql("SELECT store_id, city FROM dim_store", engine)
    latest_inventory = pd.read_sql(
        "SELECT DISTINCT ON (store_id, product_category) store_id, product_category, inventory_on_hand "
        "FROM fact_sales ORDER BY store_id, product_category, date DESC",
        engine,
    )
    avg_inventory = pd.read_sql(
        "SELECT store_id, product_category, AVG(inventory_on_hand) AS healthy_inventory FROM fact_sales GROUP BY 1, 2",
        engine,
    )

    if forecast_df.empty:
        logger.warning("No forecast rows found in fact_weather_daily (dates >= today). "
                        "Run fetch_weather.py and load_to_db.py again, making sure the forecast rows get loaded.")
        return

    results = []
    for _, sens_row in sensitivity_df.iterrows():
        if sens_row["sensitivity_label"] == "Low":
            continue  # only score products that actually respond to weather

        driver = sens_row["weather_driver"]
        product = sens_row["product_category"]

        for _, store in stores_df.iterrows():
            city_history = history_df[history_df["city"] == store["city"]]
            city_forecast = forecast_df[forecast_df["city"] == store["city"]]
            if city_history.empty or city_forecast.empty:
                continue

            hist_mean = city_history[driver].mean()
            hist_std = city_history[driver].std()

            inv_row = latest_inventory[(latest_inventory["store_id"] == store["store_id"]) &
                                        (latest_inventory["product_category"] == product)]
            healthy_row = avg_inventory[(avg_inventory["store_id"] == store["store_id"]) &
                                         (avg_inventory["product_category"] == product)]
            if inv_row.empty or healthy_row.empty:
                continue

            current_inventory = inv_row.iloc[0]["inventory_on_hand"]
            healthy_inventory = healthy_row.iloc[0]["healthy_inventory"]

            for _, day in city_forecast.iterrows():
                forecast_value = day[driver]
                z = compute_weather_anomaly_z(forecast_value, hist_mean, hist_std)
                pressure = compute_inventory_pressure(current_inventory, healthy_inventory)
                risk = compute_risk_score(z, abs(sens_row["correlation_r"]), pressure)

                results.append({
                    "forecast_date": day["date"],
                    "store_id": store["store_id"],
                    "product_category": product,
                    "forecasted_weather_value": round(float(forecast_value), 2),
                    "weather_anomaly_z": round(float(z), 3),
                    "sensitivity_score": round(abs(sens_row["correlation_r"]), 3),
                    "inventory_pressure": round(pressure, 3),
                    "risk_score": risk,
                    "recommended_action": recommend_action(risk),
                })

    risk_df = pd.DataFrame(results)
    if risk_df.empty:
        logger.warning("No risk rows were generated — check that sensitivity_scores.csv and forecast data both exist.")
        return

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_risk_forecast"))
    risk_df.to_sql("fact_risk_forecast", engine, if_exists="append", index=False)

    logger.info(f"Saved {len(risk_df)} risk rows to fact_risk_forecast.")


if __name__ == "__main__":
    main()