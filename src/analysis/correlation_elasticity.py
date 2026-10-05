import os
import pandas as pd
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression

from config.settings import PROCESSED_DIR
from src.db.connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _sensitivity_label(r: float) -> str:
    r_abs = abs(r)
    if r_abs >= 0.5:
        return "High"
    if r_abs >= 0.25:
        return "Medium"
    return "Low"


def compute_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """df must have columns: product_category, primary_weather_driver, units_sold,
    temp_max_c, precipitation_mm, snowfall_cm"""
    results = []
    for product, group in df.groupby("product_category"):
        driver = group["primary_weather_driver"].iloc[0]
        if pd.isna(driver):
            driver = "temp_max_c"  # still measure the control group against temperature, expect ~0

        x = group[driver].values
        y = group["units_sold"].values

        r, p_value = pearsonr(x, y)
        model = LinearRegression().fit(x.reshape(-1, 1), y)
        slope = model.coef_[0]

        results.append({
            "product_category": product,
            "weather_driver": driver,
            "correlation_r": round(r, 3),
            "p_value": round(p_value, 5),
            "slope_units_per_unit_weather": round(slope, 3),
            "sensitivity_label": _sensitivity_label(r),
        })

    return pd.DataFrame(results).sort_values("correlation_r", key=abs, ascending=False)


def main():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM vw_sales_weather", engine)

    sensitivity_df = compute_sensitivity(df)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    out_path = os.path.join(PROCESSED_DIR, "sensitivity_scores.csv")
    sensitivity_df.to_csv(out_path, index=False)

    logger.info(f"Saved sensitivity scores to {out_path}")
    logger.info("\n" + sensitivity_df.to_string(index=False))

    control_row = sensitivity_df[sensitivity_df["product_category"].str.contains("control")]
    if not control_row.empty and abs(control_row.iloc[0]["correlation_r"]) < 0.25:
        logger.info("Sanity check PASSED: control product shows weak correlation, as expected.")
    else:
        logger.warning("Sanity check WARNING: control product shows unexpectedly strong correlation — review your data generator.")


if __name__ == "__main__":
    main()