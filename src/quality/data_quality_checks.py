import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_sales(df: pd.DataFrame, dim_store: pd.DataFrame, dim_product: pd.DataFrame, dim_date: pd.DataFrame) -> dict:
    report = {"rows_checked": len(df), "errors_found": 0, "issues": []}

    unknown_stores = set(df["store_id"]) - set(dim_store["store_id"])
    if unknown_stores:
        report["issues"].append(f"Unknown store_id values: {unknown_stores}")

    unknown_products = set(df["product_category"]) - set(dim_product["product_category"])
    if unknown_products:
        report["issues"].append(f"Unknown product_category values: {unknown_products}")

    negative_sales = (df["units_sold"] < 0).sum()
    if negative_sales:
        report["issues"].append(f"{negative_sales} rows with negative units_sold")

    duplicate_keys = df.duplicated(subset=["date", "store_id", "product_category"]).sum()
    if duplicate_keys:
        report["issues"].append(f"{duplicate_keys} duplicate (date, store_id, product_category) rows")

    expected_days = set(pd.to_datetime(dim_date["date"]).dt.date)
    actual_days = set(pd.to_datetime(df["date"]).dt.date)
    missing_days = expected_days - actual_days
    report["missing_days"] = len(missing_days)
    if missing_days:
        report["issues"].append(f"{len(missing_days)} calendar days missing entirely from fact_sales")

    report["errors_found"] = len(report["issues"])
    return report


def check_weather(df: pd.DataFrame) -> dict:
    report = {"rows_checked": len(df), "errors_found": 0, "issues": []}

    out_of_range = ((df["temp_max_c"] < -40) | (df["temp_max_c"] > 50)).sum()
    if out_of_range:
        report["issues"].append(f"{out_of_range} rows with temp_max_c outside -40C to 50C")

    negative_precip = (df["precipitation_mm"] < 0).sum()
    negative_snow = (df["snowfall_cm"] < 0).sum()
    if negative_precip or negative_snow:
        report["issues"].append(f"{negative_precip} negative precipitation rows, {negative_snow} negative snowfall rows")

    duplicate_keys = df.duplicated(subset=["date", "city"]).sum()
    if duplicate_keys:
        report["issues"].append(f"{duplicate_keys} duplicate (date, city) rows")

    report["errors_found"] = len(report["issues"])
    return report


def check_forecast_freshness(forecast_df: pd.DataFrame, today: pd.Timestamp) -> dict:
    max_date = pd.to_datetime(forecast_df["date"]).max()
    days_ahead = (max_date - today).days
    is_fresh = days_ahead >= 6
    return {"is_fresh": is_fresh, "days_of_forecast_available": days_ahead}


def log_report(name: str, report: dict) -> None:
    if report["errors_found"] == 0:
        logger.info(f"[{name}] PASSED — {report['rows_checked']} rows checked, 0 issues.")
    else:
        logger.warning(f"[{name}] {report['errors_found']} issue(s) found: {report['issues']}")