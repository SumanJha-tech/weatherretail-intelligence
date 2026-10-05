import os
import numpy as np
import pandas as pd

from config.settings import STORES, PRODUCTS, DATE_START, DATE_END, RAW_SALES_DIR, WEATHER_CACHE_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)
RNG_SEED = 42  # fixed seed -> same output every time you run this (reproducibility)


def build_dim_date(start, end) -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"date": dates})
    df["day_of_week"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6])
    df["season"] = df["month"].map(_month_to_season)
    return df


def _month_to_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Fall"


def build_dim_store() -> pd.DataFrame:
    return pd.DataFrame(STORES)


def build_dim_product() -> pd.DataFrame:
    direction_label = {1: "up_when_hot_or_wet", -1: "up_when_cold", 0: "none"}
    rows = []
    for p in PRODUCTS:
        rows.append({
            "product_category": p["product_category"],
            "department": p["department"],
            "avg_unit_price": p["avg_unit_price"],
            "primary_weather_driver": p["weather_driver"],
            "expected_direction": direction_label[p["direction"]],
        })
    return pd.DataFrame(rows)


def _load_city_weather(city: str) -> pd.DataFrame | None:
    """Reads the weather this city already has cached, so sales can react to REAL weather."""
    path = os.path.join(WEATHER_CACHE_DIR, f"{city.replace(' ', '_')}_history.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    return df


def _seasonal_wave(day_of_year: np.ndarray) -> np.ndarray:
    """A smooth up-and-down wave across the year, peaking in summer."""
    return np.sin(2 * np.pi * (day_of_year - 80) / 365.0)


def generate_fact_sales(dim_date: pd.DataFrame, dim_store: pd.DataFrame, dim_product: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RNG_SEED)
    all_rows = []

    for _, store in dim_store.iterrows():
        weather = _load_city_weather(store["city"])
        for _, product in dim_product.iterrows():
            base_demand = 40 if "control" in product["product_category"].lower() else 25
            weekend_boost = 1.15
            weather_driver = product["primary_weather_driver"]

            merged = dim_date.copy()
            if weather is not None:
                merged = merged.merge(weather, on="date", how="left")
            merged["temp_max_c"] = merged.get("temp_max_c", pd.Series(dtype=float)).fillna(15.0)
            merged["precipitation_mm"] = merged.get("precipitation_mm", pd.Series(dtype=float)).fillna(0.0)
            merged["snowfall_cm"] = merged.get("snowfall_cm", pd.Series(dtype=float)).fillna(0.0)

            day_of_year = merged["date"].dt.dayofyear.values
            seasonal = _seasonal_wave(day_of_year) * 8  # +/- 8 units from the yearly wave

            weather_effect = np.zeros(len(merged))
            if weather_driver == "temp_max_c":
                direction = 1 if "Hot" in product["expected_direction"] or "hot" in str(product["primary_weather_driver"]) else -1
                direction = 1 if product["expected_direction"].startswith("up_when_hot") else -1
                weather_effect = direction * (merged["temp_max_c"].values - 15) * 0.9
            elif weather_driver == "precipitation_mm":
                weather_effect = merged["precipitation_mm"].values * 0.8
            elif weather_driver == "snowfall_cm":
                weather_effect = merged["snowfall_cm"].values * 1.5

            weekend_mult = np.where(merged["is_weekend"], weekend_boost, 1.0)
            noise = rng.normal(0, 4, size=len(merged))

            demand = (base_demand + seasonal + weather_effect) * weekend_mult + noise
            demand = np.clip(demand, 0, None).round().astype(int)

            # --- simple inventory simulation: starting stock + weekly deliveries ---
            inventory = 200
            weekly_delivery = int(demand.mean() * 7 * 1.1)
            units_sold_list, inventory_list, replenished_list, stockout_list = [], [], [], []

            for i, day_demand in enumerate(demand):
                replenished = weekly_delivery if merged["day_of_week"].iloc[i] == "Monday" else 0
                inventory += replenished
                actual_sold = min(day_demand, inventory)
                stockout = actual_sold < day_demand
                inventory -= actual_sold

                units_sold_list.append(actual_sold)
                inventory_list.append(inventory)
                replenished_list.append(replenished)
                stockout_list.append(stockout)

            store_product_df = pd.DataFrame({
                "date": merged["date"],
                "store_id": store["store_id"],
                "product_category": product["product_category"],
                "units_sold": units_sold_list,
                "unit_price": product["avg_unit_price"],
                "inventory_on_hand": inventory_list,
                "units_replenished": replenished_list,
                "stockout_flag": stockout_list,
            })
            store_product_df["revenue"] = (store_product_df["units_sold"] * store_product_df["unit_price"]).round(2)
            all_rows.append(store_product_df)

    return pd.concat(all_rows, ignore_index=True)


def main():
    logger.info("Generating dim_date, dim_store, dim_product...")
    dim_date = build_dim_date(DATE_START, DATE_END)
    dim_store = build_dim_store()
    dim_product = build_dim_product()

    logger.info("Generating fact_sales (this can take ~10-20 seconds)...")
    fact_sales = generate_fact_sales(dim_date, dim_store, dim_product)

    os.makedirs(RAW_SALES_DIR, exist_ok=True)
    dim_date.to_csv(os.path.join(RAW_SALES_DIR, "dim_date.csv"), index=False)
    dim_store.to_csv(os.path.join(RAW_SALES_DIR, "dim_store.csv"), index=False)
    dim_product.to_csv(os.path.join(RAW_SALES_DIR, "dim_product.csv"), index=False)
    fact_sales.to_csv(os.path.join(RAW_SALES_DIR, "fact_sales.csv"), index=False)

    logger.info(f"Done. fact_sales has {len(fact_sales):,} rows.")


if __name__ == "__main__":
    main()