import pandas as pd


def total_revenue(df: pd.DataFrame) -> float:
    return round(df["revenue"].sum(), 2)


def stockout_rate_pct(df: pd.DataFrame) -> float:
    return round(100 * df["stockout_flag"].sum() / len(df), 2) if len(df) else 0.0


def overstock_rate_pct(df: pd.DataFrame, avg_daily_units: pd.Series) -> float:
    """Share of rows with more than 14 days of cover.

    avg_daily_units must align with df, one value per store and category.
    """
    days_of_supply = df["inventory_on_hand"] / avg_daily_units.replace(0, pd.NA)
    overstocked = (days_of_supply > 14).sum()
    return round(100 * overstocked / len(df), 2) if len(df) else 0.0


def revenue_at_risk(df: pd.DataFrame, predicted_units_col: str = "predicted_units_sold") -> float:
    """Unmet demand times price, on stockout days only. Surplus days contribute nothing."""
    stockout_days = df[df["stockout_flag"]]
    if stockout_days.empty:
        return 0.0
    lost_units = (stockout_days[predicted_units_col] - stockout_days["units_sold"]).clip(lower=0)
    return round((lost_units * stockout_days["unit_price"]).sum(), 2)


def inventory_turnover(df: pd.DataFrame) -> float:
    avg_inventory = df["inventory_on_hand"].mean()
    return round(df["units_sold"].sum() / avg_inventory, 2) if avg_inventory else 0.0