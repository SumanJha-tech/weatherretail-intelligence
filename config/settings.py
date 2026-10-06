"""Network, category drivers, date window, and connection settings.

`direction` is the sales response the generator plants: +1 rises with the
driver, -1 falls with it, 0 is Household Staples (no weather term). The
sensitivity job is expected to recover these relationships from sales and
observed weather.
"""
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Shared by the sales generator, the archive pull, and the dashboard filters.
DATE_START = date(2023, 1, 1)
DATE_END = date(2024, 12, 31)

STORES = [
    {"store_id": "NM-NYC", "store_name": "NorthStar Mart - New York",  "city": "New York",  "region": "Northeast", "latitude": 40.7128, "longitude": -74.0060},
    {"store_id": "NM-CHI", "store_name": "NorthStar Mart - Chicago",   "city": "Chicago",   "region": "Midwest",   "latitude": 41.8781, "longitude": -87.6298},
    {"store_id": "NM-MIA", "store_name": "NorthStar Mart - Miami",     "city": "Miami",     "region": "Southeast", "latitude": 25.7617, "longitude": -80.1918},
    {"store_id": "NM-PHX", "store_name": "NorthStar Mart - Phoenix",   "city": "Phoenix",   "region": "Southwest", "latitude": 33.4484, "longitude": -112.0740},
    {"store_id": "NM-SEA", "store_name": "NorthStar Mart - Seattle",   "city": "Seattle",   "region": "Northwest", "latitude": 47.6062, "longitude": -122.3321},
    {"store_id": "NM-DEN", "store_name": "NorthStar Mart - Denver",    "city": "Denver",    "region": "Mountain",  "latitude": 39.7392, "longitude": -104.9903},
]

# weather_driver is the column both the generator and the sensitivity model use.
# None is the control: demand is seasonal and noisy, with no weather coefficient.
PRODUCTS = [
    {"product_category": "Ice Cream & Frozen Treats",       "department": "Grocery",        "avg_unit_price": 4.50,  "weather_driver": "temp_max_c",      "direction": 1},
    {"product_category": "Bottled Water & Sports Drinks",   "department": "Grocery",        "avg_unit_price": 2.00,  "weather_driver": "temp_max_c",      "direction": 1},
    {"product_category": "Hot Beverages & Soup",            "department": "Grocery",        "avg_unit_price": 5.00,  "weather_driver": "temp_max_c",      "direction": -1},
    {"product_category": "Umbrellas & Rain Gear",           "department": "Seasonal",       "avg_unit_price": 12.00, "weather_driver": "precipitation_mm","direction": 1},
    {"product_category": "Outerwear & Jackets",             "department": "Apparel",        "avg_unit_price": 65.00, "weather_driver": "temp_max_c",      "direction": -1},
    {"product_category": "Sunscreen & Summer Essentials",   "department": "Health & Beauty","avg_unit_price": 9.00,  "weather_driver": "temp_max_c",      "direction": 1},
    {"product_category": "Snow Removal & Winter Gear",      "department": "Seasonal",       "avg_unit_price": 22.00, "weather_driver": "snowfall_cm",     "direction": 1},
    {"product_category": "Household Staples (control)",     "department": "Grocery",        "avg_unit_price": 6.00,  "weather_driver": None,              "direction": 0},
]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "weatherretail")
DB_USER = os.getenv("DB_USER", "weatherretail_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SALES_DIR = os.path.join(BASE_DIR, "data", "raw", "sales_synthetic")
WEATHER_CACHE_DIR = os.path.join(BASE_DIR, "data", "raw", "weather_cache")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample")
LOGS_DIR = os.path.join(BASE_DIR, "logs")