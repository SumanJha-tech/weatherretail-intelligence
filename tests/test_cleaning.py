import pandas as pd
from src.cleaning.clean_sales import clean_sales


def test_negative_units_sold_becomes_zero():
    df = pd.DataFrame({
        "date": ["2024-01-01"], "store_id": ["nm-nyc"], "product_category": ["Test"],
        "units_sold": [-5], "unit_price": [10.0], "inventory_on_hand": [-2], "units_replenished": [0],
    })
    cleaned = clean_sales(df)
    assert cleaned.loc[0, "units_sold"] == 0
    assert cleaned.loc[0, "inventory_on_hand"] == 0


def test_duplicate_rows_are_removed():
    row = {
        "date": ["2024-01-01", "2024-01-01"], "store_id": ["NM-NYC", "NM-NYC"],
        "product_category": ["Test", "Test"], "units_sold": [5, 5], "unit_price": [10.0, 10.0],
        "inventory_on_hand": [50, 50], "units_replenished": [0, 0],
    }
    cleaned = clean_sales(pd.DataFrame(row))
    assert len(cleaned) == 1


def test_store_id_is_uppercased():
    df = pd.DataFrame({
        "date": ["2024-01-01"], "store_id": [" nm-chi "], "product_category": ["Test"],
        "units_sold": [1], "unit_price": [1.0], "inventory_on_hand": [1], "units_replenished": [0],
    })
    cleaned = clean_sales(df)
    assert cleaned.loc[0, "store_id"] == "NM-CHI"