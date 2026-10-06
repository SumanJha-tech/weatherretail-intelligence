import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize keys, enforce the grain, and recompute revenue.

    Grain is (date, store_id, product_category). Negative quantities are
    floored at zero and kept; they are not dropped.
    """
    before = len(df)
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["store_id"] = df["store_id"].str.strip().str.upper()
    df["product_category"] = df["product_category"].str.strip()

    df = df.drop_duplicates(subset=["date", "store_id", "product_category"])

    for col in ["units_sold", "inventory_on_hand", "units_replenished"]:
        negative_count = (df[col] < 0).sum()
        if negative_count:
            logger.warning(f"Fixed {negative_count} negative values in '{col}' (set to 0).")
        df[col] = df[col].clip(lower=0)

    df["revenue"] = (df["units_sold"] * df["unit_price"]).round(2)

    after = len(df)
    if before != after:
        logger.info(f"Removed {before - after} duplicate rows during cleaning.")
    return df