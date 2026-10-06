-- Rebuilds the star schema. Drop order follows foreign keys so the script can be re-run.

DROP TABLE IF EXISTS fact_risk_forecast;
DROP TABLE IF EXISTS fact_weather_daily;
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_date;

-- Calendar attributes. Precomputed so analysis queries do not repeat date logic.
CREATE TABLE dim_date (
    date            DATE PRIMARY KEY,
    day_of_week     TEXT NOT NULL,
    month           INT NOT NULL,
    year            INT NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    season          TEXT NOT NULL
);

-- One store per city. Coordinates are the Open-Meteo request point for that city.
CREATE TABLE dim_store (
    store_id        TEXT PRIMARY KEY,
    store_name      TEXT NOT NULL,
    city            TEXT NOT NULL,
    region          TEXT NOT NULL,
    latitude        NUMERIC(8, 4) NOT NULL,
    longitude       NUMERIC(8, 4) NOT NULL
);

-- Category is the product grain.
-- primary_weather_driver is null for Household Staples (the control).
-- expected_direction is up_when_hot_or_wet, up_when_cold, or none.
CREATE TABLE dim_product (
    product_category        TEXT PRIMARY KEY,
    department               TEXT NOT NULL,
    avg_unit_price            NUMERIC(10, 2) NOT NULL,
    primary_weather_driver    TEXT,
    expected_direction        TEXT NOT NULL
);

-- One row per store, category, and day. Revenue is units × price, recomputed during cleaning.
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

-- Daily weather for a store city. History is what load_to_db writes.
-- The live forecast can be appended here; risk scoring reads rows dated today or later.
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

-- Output of src/analysis/risk_scoring.py, stored so SQL and the dashboard read it like any other table.
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
