<div align="center">

# 🌦️ WeatherRetail Intelligence

**Which products does the weather actually move, what does a wrong stock decision cost, and what should we reorder this week?**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://weatherretail-intelligence.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-star%20schema-336791?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/tests-10%20passing-brightgreen)
![License](https://img.shields.io/badge/use-demo%20%26%20portfolio-lightgrey)

**[▶ Open the live dashboard](https://weatherretail-intelligence.streamlit.app/)**

</div>

---

A decision pipeline for a six-store chain. It measures which categories actually move with weather, prices the cost of stocking them wrong, and turns the next seven days of forecast into a store-and-category action list.

NorthStar Mart operates one store in each of six climates. Merchandising already knew that heat, rain, and snow change what sells. The chain had not measured which categories move, by how much, or which locations are about to stock out. This repository is that measurement: two years of daily sales joined to observed city weather, a one-variable sensitivity model, and a forward risk score.

Sales are synthetic and seeded, so the result can be reproduced. Weather is not. Open-Meteo supplies the daily archive and the forecast for the six store cities. The generator plants a known weather response; the model is then asked to recover it. A control category with no planted effect is scored with the same method.

| | |
|---|---|
| Chain | NorthStar Mart — 6 stores, 6 climates |
| Window | 1 January 2023 – 31 December 2024 (731 days) |
| Grain | Store × product category × day |
| Scale | 35,088 sales facts · 4,386 city-day weather rows · **$13.48M** revenue · **1.02M** units |
| Output | Sensitivity by category, demand slope, and a 0–100 risk score with an action |

---

## Live demo

**https://weatherretail-intelligence.streamlit.app/**

| Page | What to look at |
|---|---|
| [Overview](https://weatherretail-intelligence.streamlit.app/) | Filter by date, store, and category. KPIs and the revenue-versus-temperature chart recompute for the slice |
| Weather sensitivity | Pick a category and see units plotted against its driver, with the fitted slope |
| Risk and forecast | Seven-day forecast per city and the reorder list, colored by the 60 / 30 score bands |
| [Store deep dive](https://weatherretail-intelligence.streamlit.app/store) | One store: revenue, stockout calendar, category contribution |

The hosted app has no database. It reads a frozen CSV snapshot of the warehouse in `data/snapshot/`, so it works anywhere. Run locally against PostgreSQL and the same code reads live tables. See [Deployment](#deployment).

---

## What a reader should take from the numbers

These figures come from the cleaned 2023–2024 sales fact and from the sensitivity model on `vw_sales_weather`.

| Measure | Result |
|---|---|
| Revenue | **$13,482,567** |
| Units sold | 1,017,267 |
| Stockout rate | **0.49%** of store–category–days (173 days) |
| Where stockouts sit | Almost entirely **Outerwear & Jackets** and **Hot Beverages & Soup** (about 2% of each category's days) |
| Quality gate | 35,088 sales rows and 4,386 weather rows checked, **0 issues** |

Revenue by store is a tight band: Seattle $2.48M, Chicago $2.43M, New York $2.37M, Denver $2.33M, Miami $2.00M, Phoenix $1.86M. Climate, not store size, is what separates their demand.

| Category | Driver | r | Units per 1-unit change | Label |
|---|---|---:|---:|---|
| Bottled Water & Sports Drinks | Daily high (°C) | +0.895 | +1.24 | High |
| Ice Cream & Frozen Treats | Daily high (°C) | +0.891 | +1.24 | High |
| Sunscreen & Summer Essentials | Daily high (°C) | +0.891 | +1.24 | High |
| Hot Beverages & Soup | Daily high (°C) | −0.705 | −0.60 | High |
| Outerwear & Jackets | Daily high (°C) | −0.703 | −0.61 | High |
| Umbrellas & Rain Gear | Precipitation (mm) | +0.658 | +0.86 | High |
| Household Staples (control) | Daily high (°C) | +0.464 | +0.33 | Medium |
| Snow Removal & Winter Gear | Snowfall (cm) | +0.078 | +0.76 | Low |

How to use the table in a buy meeting:

- Six categories clear High (|r| ≥ 0.50). The signs match the commercial story: heat lifts water, ice cream, and sunscreen; cold lifts soup and outerwear; rain lifts umbrellas.
- Outerwear is both highly weather-sensitive and one of the two categories that stocked out. That is the expensive pair: demand spikes on empty-shelf days, at a $65 average unit price and **$5.76M** of category revenue.
- Household Staples were generated with no weather term. The model still returns a moderate temperature correlation (r = 0.46), below every High category, and the pipeline logs it. Temperature and staples both follow the calendar, so a one-variable correlation absorbs part of that shared season. High is the buy signal. Medium on the control is a reason to check seasonality before anyone changes an order.
- Snow gear has a shallow correlation (r = 0.08) and a real slope (+0.76 units per centimetre). Snow days are rare, so most of the two-year series is zeros and Pearson understates the days that matter. Plan snow off event days, not off the full-series correlation alone.

Thresholds: |r| ≥ 0.50 High, 0.25–0.50 Medium, below 0.25 Low.

---

## Who it is for

| Role | Decision |
|---|---|
| VP of Merchandising | Whether weather is a material P&L issue, and which categories justify a weather-aware buy |
| Supply chain | Which store–category pairs to replenish in the next seven days |
| Store management | What the coming week does to that store's assortment |
| Category management | Whether a category is heat-, rain-, or snow-sensitive, and the size of the effect |

| Store | City | Climate the model has to respect |
|---|---|---|
| NM-NYC | New York | Four seasons |
| NM-CHI | Chicago | Cold winters, humid summers |
| NM-MIA | Miami | Hot and wet |
| NM-PHX | Phoenix | Extreme heat, little rain |
| NM-SEA | Seattle | Mild, frequent rain |
| NM-DEN | Denver | Rapid swings, snow |

---

## Architecture

```
  Sales generator                         Open-Meteo
  (seed 42)                               history + 7-day forecast
           │                                      │
           ▼                                      ▼
   data/raw/sales_synthetic/              data/raw/weather_cache/
           │                                      │
           └──────────────┬───────────────────────┘
                          ▼
              Clean  →  quality checks  →  processed CSVs
                          │
                          ▼
                 PostgreSQL (star schema)
                 dim_date · dim_store · dim_product
                 fact_sales · fact_weather_daily
                 fact_risk_forecast
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     SQL analysis views          Python analytics
     trends, stockouts,          correlation, slope,
     days of supply              KPIs, 7-day risk score
                          │
                          ▼
              Streamlit
              Overview · Sensitivity · Risk · Store
                          ▲
                          │  Postgres unreachable?
                 data/snapshot/*.csv   (export_snapshot.py)
```

Sales meet weather on **city + date**. Weather has no `store_id`. `fact_risk_forecast` is model output written back so the dashboard and SQL read it like any other table.

---

## Method

### Sensitivity

For each category, daily units against that category's driver (daily high, precipitation, or snowfall):

- **Correlation (r)** and its p-value, from `scipy.stats.pearsonr`.
- **Slope (β)**, from a one-variable ordinary least-squares fit. Units per degree, millimetre, or centimetre.

The control is scored against temperature on purpose. A buy waits until that score stays below High.

### Risk score

For each store, each High or Medium category, and each forecast day:

```
RiskScore = |z| × |r| × inventory_pressure × (100 / 3)
```

clipped to 0–100. The divisor makes a 3σ forecast, a sensitivity of 1, and an empty shelf equal 100.

| Input | Definition |
|---|---|
| z | Forecast versus that city's historical mean, in standard deviations |
| \|r\| | Absolute correlation for the category |
| Inventory pressure | `1 − (on hand / typical on hand)`, clipped to 0–1 |

| Score | Action |
|---|---|
| 60–100 | Reorder now |
| 30–59 | Watch; consider reordering |
| 0–29 | No action |

Worked example, locked by `tests/test_risk_scoring.py`: a 46°C Phoenix day against a 40°C ± 3°C normal is z = 2.0. Water sensitivity of 0.72 and 2 days of stock against a healthy 14 produces a score of about **41**.

Low-sensitivity categories are left off the list.

### SQL

All six statements read `vw_sales_weather` (`sql/02_views.sql`) and live in `sql/03_analysis_queries.sql`.

| Question | Query |
|---|---|
| How is the business trending? | Monthly revenue and units |
| Does temperature change the sales rate? | Average units by temperature band |
| Where are we losing the sale? | Stockout rate by store and category |
| Is the trend accelerating? | Month-over-month growth with `LAG` |
| What sits under daily noise? | 7-day moving average of units |
| Where is cash sitting on the shelf? | Days of supply above 14 |

### KPI definitions

| KPI | Definition |
|---|---|
| Total revenue | Sum of units × price |
| Stockout rate | Share of store–category–days with a stockout |
| Overstock rate | Share of days with more than 14 days of supply |
| Inventory turnover | Units sold ÷ average units on hand |
| Weather sensitivity | Correlation of units with the category's driver |
| Demand elasticity | Regression slope, units per unit of weather |
| Revenue at risk | On stockout days, (expected units − units sold) × price, floored at zero |

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | One runtime for generation, the API, statistics, and the dashboard |
| Tables | pandas, NumPy | Cleaning, joins, KPI math |
| Warehouse | PostgreSQL 14+ | A real star schema; the SQL moves to Snowflake or BigQuery |
| Access | SQLAlchemy, psycopg2 | Credentials stay in `.env` |
| Weather | Open-Meteo | Public archive and forecast; no key |
| HTTP | requests | Timeouts, three retries, on-disk cache |
| Statistics | SciPy, scikit-learn | Pearson correlation and OLS slope |
| UI | Streamlit, Plotly | Four pages, filterable |
| Hosting | Streamlit Community Cloud | Free, deploys from `main`; reads the CSV snapshot instead of a database |
| Tests | pytest | Known-answer tests for cleaning, checks, KPIs, and the risk formula |

---

## Setup

**Prerequisites:** Python 3.11+, PostgreSQL 14+, Git.

```powershell
git clone https://github.com/SumanJha-tech/weatherretail-intelligence.git
cd weatherretail-intelligence

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env
```

On macOS or Linux, activate with `source venv/bin/activate`.

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weatherretail
DB_USER=weatherretail_app
DB_PASSWORD=your_password_here
```

Create the database and role, then apply the schema as a role that can create tables. If `weatherretail_app` is not the owner, grant it `SELECT, INSERT, UPDATE, DELETE, TRUNCATE` on the tables and `SELECT` on `vw_sales_weather` after the view exists.

```sql
CREATE DATABASE weatherretail;
CREATE USER weatherretail_app WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE weatherretail TO weatherretail_app;
```

```powershell
psql -U postgres -d weatherretail -f sql/01_schema.sql
psql -U postgres -d weatherretail -f sql/02_views.sql
```

---

## Pipeline

Run from the repository root, in order. Each stage logs to `logs/pipeline.log`.

```powershell
python -m src.ingestion.generate_synthetic_sales
python -m src.ingestion.fetch_weather
python -m src.ingestion.load_to_db
python -m src.analysis.correlation_elasticity
python -m src.analysis.risk_scoring
pytest -v
streamlit run dashboard/app.py
```

| Stage | What it does |
|---|---|
| Generate sales | Date, store, and product dimensions, plus a daily fact. Demand is a base rate, a weekend lift (1.15), a seasonal wave (±8 units, peak in late June), a planted weather term from that city's real history, and N(0, 4) noise. Inventory starts at 200 and is replenished on Mondays at 110% of mean weekly demand. Sales cannot exceed on-hand. Seed is 42. |
| Fetch weather | One history call and one forecast call per city. History is cached until deleted. Forecasts are reused for six hours. A failed call retries three times, then reads `data/sample/weather_backup.csv` if it exists. |
| Clean | Parse dates, standardize city and store text, drop duplicate keys, floor negative quantities at zero, recompute revenue, and forward-fill short weather gaps within a city. |
| Quality checks | Unknown keys, negative sales, duplicate grain, missing calendar days, temperatures outside −40°C to 50°C, negative rain or snow. The report does not rewrite rows and does not block the load. |
| Load | Full refresh, dimensions before facts. |
| Sensitivity | One row per category: driver, r, p-value, slope, label. Written to `data/processed/sensitivity_scores.csv`. |
| Risk | One row per store, sensitive category, and forecast day, with the action text. |

**Forecast window.** Sensitivity uses the 2023–2024 history that `load_to_db` writes into `fact_weather_daily`. The live forecast is cached as `all_cities_forecast.csv`. The risk job reads weather rows dated on or after today. If the table only holds history, the job logs that no forecast rows are loaded and the Risk page says the same. Append the cached forecast (date, city, and the five weather measures) before the risk step when you want this week's list.

### Dashboard

```powershell
streamlit run dashboard/app.py
```

| Page | Question |
|---|---|
| Overview | How large is this slice, how often do we stock out, and does revenue move with temperature? |
| Weather sensitivity | Which categories are weather-driven, and what is the slope? |
| Risk and forecast | What is each city forecast to do, and which pairs need a reorder? |
| Store deep dive | For one store: revenue, stockout rate, a calendar of stockout days, and category contribution |

Overview filters recompute the KPIs from the warehouse for the selected slice. Dashboard queries are cached for 10 minutes. Colors, type, and radius live in `.streamlit/config.toml`.

---

## Deployment

The live app runs on Streamlit Community Cloud, which has no PostgreSQL. `src/db/queries.py` tries the database once per process. If the connection fails, every read falls back to the CSV tables in `data/snapshot/`, and `vw_sales_weather` is rebuilt in pandas. The result is the same pages with no code change and no secrets required.

| Environment | Data source |
|---|---|
| Local with PostgreSQL | Live warehouse tables |
| Streamlit Cloud | `data/snapshot/*.csv` (2.7 MB, committed) |

Refresh the snapshot after a pipeline run, then commit it:

```powershell
python -m src.db.export_snapshot
```

The snapshot is frozen, so the Risk page's "seven-day forecast" shows the days captured when it was exported. Python code under `src/` is imported once per process on Streamlit Cloud. After pushing changes there, use **Manage app → Reboot app**.

---

## Repository

```
weather-retail-intelligence/
├── README.md
├── PROJECT_GUIDE.md          # design notes from the build
├── requirements.txt
├── .env.example
├── config/settings.py        # stores, categories, dates, connection
├── data/
│   ├── raw/sales_synthetic/
│   ├── raw/weather_cache/
│   ├── processed/            # sensitivity_scores.csv is tracked
│   ├── snapshot/             # CSV copy of the warehouse for hosting
│   └── sample/
├── sql/
│   ├── 01_schema.sql
│   ├── 02_views.sql
│   └── 03_analysis_queries.sql
├── src/
│   ├── ingestion/
│   ├── cleaning/
│   ├── quality/
│   ├── analysis/
│   ├── db/                   # engine, cached queries, export_snapshot
│   └── utils/
├── .streamlit/config.toml    # dashboard theme
├── dashboard/
│   ├── app.py
│   ├── assets/
│   └── app_pages/
├── tests/
└── logs/pipeline.log
```

Raw extracts, most processed files, logs, the virtual environment, and `.env` are gitignored. Two exceptions are tracked so the hosted app runs: `data/processed/sensitivity_scores.csv` and `data/snapshot/`. Everything else stays on the machine that ran the pipeline.

---

## Tests

```powershell
pytest -v
```

The tests do not need Postgres.

| Suite | Locked behavior |
|---|---|
| `tests/test_cleaning.py` | Duplicate grain is collapsed; negative units are floored; store ids are normalized |
| `tests/test_quality_checks.py` | Out-of-range temperatures are reported; a clean frame passes |
| `tests/test_kpis.py` | Revenue and stockout rate match a hand-computed frame |
| `tests/test_risk_scoring.py` | The Phoenix example scores near 41; a flat forecast scores 0; the score never exceeds 100 |

---

## Boundaries

Deliberate limits, not unfinished chores.

- Sales are a controlled simulation. Swap in retailer POS when it exists; keep the generator as the demo and the regression fixture.
- The sensitivity model is one variable. It does not partial out month, holidays, or price. The control category is the reminder.
- Snow should be read on snow days. A two-year Pearson correlation dilutes a real event effect.
- The warehouse load is a full refresh, which is the right shape while the pipeline is rebuilt often. A production schedule would append new days.
- The risk score is explainable on purpose. A gradient-boosted demand model can follow, after buyers trust the three inputs they can see.
- Quality checks log and continue. They are a gate in the log, not a transaction abort.

Production extensions that fit this design: a daily scheduler, incremental loads, an alert when a score crosses 60, and the same star schema in a cloud warehouse or Power BI.

---

## License

Built by [Suman Jha](https://github.com/SumanJha-tech). Released for demonstration and portfolio use. Weather observations are retrieved from [Open-Meteo](https://open-meteo.com/) under their published terms.
