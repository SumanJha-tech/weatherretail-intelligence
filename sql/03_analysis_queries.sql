-- Monthly revenue and units.
SELECT date_trunc('month', date) AS month,
       SUM(revenue) AS monthly_revenue,
       SUM(units_sold) AS monthly_units
FROM vw_sales_weather
GROUP BY 1
ORDER BY 1;

-- Mean units by temperature band. The numeric prefix keeps bands in climate order.
SELECT
    product_category,
    CASE
        WHEN temp_max_c < 5  THEN '1. Freezing (<5C)'
        WHEN temp_max_c < 15 THEN '2. Cool (5-15C)'
        WHEN temp_max_c < 25 THEN '3. Mild (15-25C)'
        ELSE '4. Hot (25C+)'
    END AS temp_bucket,
    ROUND(AVG(units_sold), 1) AS avg_units_sold
FROM vw_sales_weather
GROUP BY 1, 2
ORDER BY 1, 2;

-- Stockout rate: stockout days divided by observed days, by store and category.
SELECT
    store_id,
    product_category,
    ROUND(100.0 * SUM(CASE WHEN stockout_flag THEN 1 ELSE 0 END) / COUNT(*), 2) AS stockout_rate_pct
FROM vw_sales_weather
GROUP BY 1, 2
ORDER BY stockout_rate_pct DESC;

-- Month-over-month revenue growth. The first month has no prior period.
WITH monthly AS (
    SELECT date_trunc('month', date) AS month, SUM(revenue) AS revenue
    FROM vw_sales_weather GROUP BY 1
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- Seven-day moving average within each store and category.
-- The first six days of each series are a partial window.
SELECT
    date, store_id, product_category, units_sold,
    ROUND(AVG(units_sold) OVER (
        PARTITION BY store_id, product_category
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS units_sold_7d_avg
FROM vw_sales_weather
ORDER BY store_id, product_category, date;

-- Days of supply above 14. Cover uses that store-category's own average daily units.
WITH avg_demand AS (
    SELECT store_id, product_category, AVG(units_sold) AS avg_daily_units
    FROM vw_sales_weather GROUP BY 1, 2
)
SELECT
    v.store_id, v.product_category, v.date, v.inventory_on_hand,
    ROUND(v.inventory_on_hand / NULLIF(a.avg_daily_units, 0), 1) AS days_of_supply
FROM vw_sales_weather v
JOIN avg_demand a USING (store_id, product_category)
WHERE v.inventory_on_hand / NULLIF(a.avg_daily_units, 0) > 14
ORDER BY days_of_supply DESC;