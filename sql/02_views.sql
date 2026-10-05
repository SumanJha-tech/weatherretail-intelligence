CREATE OR REPLACE VIEW vw_sales_weather AS
SELECT
    s.date,
    s.store_id,
    st.city,
    st.region,
    s.product_category,
    p.department,
    p.primary_weather_driver,
    s.units_sold,
    s.unit_price,
    s.revenue,
    s.stockout_flag,
    s.inventory_on_hand,
    s.units_replenished,
    d.day_of_week,
    d.is_weekend,
    d.season,
    w.temp_max_c,
    w.temp_min_c,
    w.precipitation_mm,
    w.snowfall_cm,
    w.windspeed_max_kmh
FROM fact_sales s
JOIN dim_store   st ON s.store_id = st.store_id
JOIN dim_product p  ON s.product_category = p.product_category
JOIN dim_date    d  ON s.date = d.date
JOIN fact_weather_daily w ON s.date = w.date AND st.city = w.city;