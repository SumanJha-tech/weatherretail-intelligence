-- Run this once to create all tables. Safe to re-run: it drops old tables first.

DROP TABLE IF EXISTS fact_risk_forecast;
DROP TABLE IF EXISTS fact_weather_daily;
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_date;

-- dim_date: one row per calendar day, with pre-computed helpers so queries
-- don't have to repeat date math every time.
CREATE TABLE dim_date (
    date            DATE PRIMARY KEY,
    day_of_week     TEXT NOT NULL,
    month           INT NOT NULL,
    year            INT NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    season          TEXT NOT NULL
);

-- dim_store: one row per physical store.
CREATE TABLE dim_store (
    store_id        TEXT PRIMARY KEY,
    store_name      TEXT NOT NULL,
    city            TEXT NOT NULL,
    region          TEXT NOT NULL,
    latitude        NUMERIC(8, 4) NOT NULL,
    longitude       NUMERIC(8, 4) NOT NULL
);

-- dim_product: one row per product category.
CREATE TABLE dim_product (
    product_category        TEXT PRIMARY KEY,
    department               TEXT NOT NULL,
    avg_unit_price            NUMERIC(10, 2) NOT NULL,
    primary_weather_driver    TEXT,              -- NULL for the control product
    expected_direction        TEXT NOT NULL       -- 'up_when_hot', 'up_when_cold', 'up_when_rainy', 'up_when_snowy', 'none'
);

-- fact_sales: the center of the whole database. One row per store + product + day.
CREATE TABLE fact_sales (
    date                DATE NOT NULL REFERENCES dim_date(date),
    store_id            TEXT NOT NULL REFERENCES dim_store(store_id),
    product_category    TEXT NOT NULL REFERENCES dim_product(product_category),
    units_sold          INT NOT NULL CHECK (units_sold >= 0),
    unit_price          NUMERIC(10, 2) NOT NULL,
    revenue             NUMERIC(12, 2) NOT NULL,
    inventory_on_hand   INT NOT NULL CHECK (inventory_on_hand >= 0),
    units_replenished   INT NOT NULL DEFAULT 0,
    stockout_flag       BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (date, store_id, product_category)
);
CREATE INDEX idx_fact_sales_store   ON fact_sales(store_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_category);

-- fact_weather_daily: real historical weather, one row per city + day.
CREATE TABLE fact_weather_daily (
    date                DATE NOT NULL,
    city                TEXT NOT NULL,
    temp_max_c          NUMERIC(5, 2),
    temp_min_c          NUMERIC(5, 2),
    precipitation_mm    NUMERIC(6, 2),
    snowfall_cm         NUMERIC(6, 2),
    windspeed_max_kmh   NUMERIC(6, 2),
    PRIMARY KEY (date, city)
);

-- fact_risk_forecast: NOT raw data — this is the OUTPUT of our own Python
-- risk model (src/analysis/risk_scoring.py), saved back so the dashboard
-- can query it like any other table.
CREATE TABLE fact_risk_forecast (
    forecast_date               DATE NOT NULL,
    store_id                    TEXT NOT NULL REFERENCES dim_store(store_id),
    product_category            TEXT NOT NULL REFERENCES dim_product(product_category),
    forecasted_weather_value    NUMERIC(6, 2),
    weather_anomaly_z           NUMERIC(6, 3),
    sensitivity_score           NUMERIC(5, 3),
    inventory_pressure          NUMERIC(5, 3),
    risk_score                  NUMERIC(5, 2),
    recommended_action          TEXT,
    PRIMARY KEY (forecast_date, store_id, product_category)
);