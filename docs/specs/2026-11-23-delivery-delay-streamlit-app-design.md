# Delivery Delay Analysis - Interactive Streamlit Application Design

- **Date:** 2026-11-23
- **Status:** Approved
- **Target Folder:** `/Users/vemulasaiharshil/Downloads/files2`

## 1. Overview & Business Objectives
This application transforms the static data analysis pipeline of the "Delivery Delay Root-Cause Analysis" project into a full-featured, interactive Streamlit web application.
The business question addressed: *Why do food deliveries miss their promised time, and what operational interventions should be deployed first?*

The application enables operations leaders and business stakeholders to:
1. Filter orders across Bangalore delivery zones, weather conditions, time of day, and rider tenure.
2. Inspect data hygiene and data quality transformations (null imputation, casing standardization, deduplication).
3. Explore root-cause drivers derived from a standardised Ordinary Least Squares (OLS) regression model ($R^2 = 0.91$).
4. Execute ad-hoc analytical SQL queries directly against an in-memory SQLite database.
5. Simulate the operational and financial impact of rain incentives and dynamic ETA buffers (A/B scenario modeling).

---

## 2. Architecture & Directory Layout

A modular package architecture separating data engineering, analytics, modeling, and presentation:

```
files2/
├── app.py                      # Main entrypoint: layout, sidebar filters, theme & tab router
├── requirements.txt            # streamlit, pandas, numpy, plotly, pytest
├── src/
│   ├── __init__.py
│   ├── data_pipeline.py        # Data generator, CSV loader, cleaner, caching
│   ├── analytics.py            # SQLite engine, KPI aggregator, OLS driver model
│   ├── simulation.py           # A/B test simulation and ROI calculations
│   └── views/
│       ├── __init__.py
│       ├── overview.py         # Tab 1: Executive KPI overview & Plotly charts
│       ├── data_cleaning.py    # Tab 2: Raw vs clean audit & data dictionary
│       ├── driver_model.py     # Tab 3: OLS driver rankings & delay distributions
│       ├── sql_console.py      # Tab 4: Interactive SQL runner with presets
│       └── simulation_view.py  # Tab 5: Dynamic buffer & surge incentive simulator
└── tests/
    ├── __init__.py
    ├── test_data_pipeline.py   # Validation tests for cleaning pipeline
    ├── test_analytics.py       # Unit tests for KPIs, queries, and OLS regression
    └── test_simulation.py      # Unit tests for simulation calculations
```

---

## 3. Data Pipeline & In-Memory Engine (`src/data_pipeline.py`)

### 3.1 Data Loading & Generation
- Checks for existence of `orders_raw.csv` and `orders_clean.csv`.
- If missing, executes the deterministic generation function (20,000 orders across 7 zones, 120 restaurants, 300 riders over 90 days from June 1, 2026).
- Injects 300 null weather values, 150 uppercase zone anomalies, and 120 duplicate order rows to showcase realistic data imperfections.

### 3.2 Cleaning Specifications
- **Deduplication**: Removes duplicates by `order_id` (20,120 -> 20,000 rows).
- **Text Normalization**: `zone` strings normalized to Title Case with explicit acronym preservation (`"HSR Layout"`).
- **Imputation**: Missing weather values tagged as `"Unknown"` (or imputed via mode/clear weather).
- **Range Validation**: Filters invalid deliveries (`delivered_min > 0` and `distance_km > 0`).
- **Caching**: Data loading wrapped in `@st.cache_data` to ensure zero lag on subsequent interactions.

---

## 4. Analytics & Statistical Modeling (`src/analytics.py`)

### 4.1 SQLite Analytical Store
- In-memory SQLite database (`:memory:`) created on startup and registered in `st.session_state`.
- Populated with the active `orders` table.
- Read-only execution guard ensures safety while executing custom user queries.

### 4.2 Standardised OLS Regression Driver Model
- Target: Standardised delivery time $y = \frac{T - \mu_T}{\sigma_T}$.
- Features: Distance, Prep Time, Rider Tenure, Peak Hour flag, Rain flag, Heavy Rain flag.
- Normalization: $Z = \frac{X - \mu_X}{\sigma_X}$.
- Solved via least squares: $\beta = (A^T A)^{-1} A^T y$.
- Explanatory power: $R^2 \ge 0.90$.
- Operational insight: Distinguishes non-controllable factors (Distance) from high-leverage controllable factors (Weather buffer, Restaurant prep time, Rider assignment).

---

## 5. UI Views & Interactive Features

### 5.1 Tab 1: Executive KPI Overview (`src/views/overview.py`)
- **Metric Cards**:
  - SLA Breach Rate (%) with delta vs. target (benchmark: 20.0%).
  - Average Delivery Time (mins).
  - Order Cancellation Rate (%).
  - Total Estimated Revenue Lost to Cancellations (₹).
- **Interactive Charts (Plotly)**:
  - SLA Breach by Zone (bar chart with color-coded risk).
  - SLA Breach by Weather (Clear, Rain, Heavy Rain).
  - Breach Rate across 24 Hours (highlighting lunch and dinner peaks).
  - Hotspot Matrix (Zone $\times$ Weather during peak hours).
  - Top 10 Slowest Restaurants by SLA breach rate.

### 5.2 Tab 2: Data Pipeline & Quality Inspector (`src/views/data_cleaning.py`)
- Visual reconciliation summary (Raw rows vs Clean rows, Nulls detected, Case mismatches resolved).
- Data dictionary table with business meanings, units, and ranges.
- Filterable sample table with instant search and CSV download.

### 5.3 Tab 3: Delay Drivers & OLS Model (`src/views/driver_model.py`)
- Horizontal bar chart of standardized regression coefficients.
- Variance explained ($R^2$) display.
- Narrative summary on tactical levers (why distance cannot be changed, but buffer and prep SLAs can).

### 5.4 Tab 4: Interactive SQL Console (`src/views/sql_console.py`)
- SQL editor with syntax highlighting.
- 4 pre-canned queries:
  1. Breach rate and order volume by zone.
  2. Experience impact: New riders (<3m) vs Veterans (12m+).
  3. Peak hour hotspots by zone and weather.
  4. Cancellation loss by restaurant.
- Query execution metadata: execution time (ms) and row count.
- One-click CSV export of query results.

### 5.5 Tab 5: Rain Incentive & Buffer A/B Simulator (`src/views/simulation.py`)
- Interactive parameter sliders:
  - **Dynamic Weather Buffer**: 0 to +20 minutes added to promised ETA during Rain/Heavy Rain.
  - **Surge Rider Incentive**: ₹0 to ₹100 extra per completed order during rain.
  - **Rider Supply Increase**: 0% to +50% active riders in outer zones.
- Real-time simulation outputs:
  - Projected SLA breach reduction (e.g. 66.6% -> ~34%).
  - Estimated orders saved from cancellation.
  - Financial ROI: Gross GMV saved minus total incentive outlay.

---

## 6. Error Handling & Edge Cases
1. **Empty Filter Results**: If the user applies conflicting sidebar filters yielding 0 rows, display an actionable warning banner: *"No orders match the selected filters. Please broaden your selection."*
2. **SQL Safety & Validation**: Block `DROP`, `DELETE`, `UPDATE`, `INSERT`, and catch `sqlite3.OperationalError` with clean user-friendly alerts.
3. **Missing File Fallback**: Automatically generate clean data if CSVs are removed or corrupted.

---

## 7. Testing Strategy (`tests/`)
- `test_data_pipeline.py`:
  - Verify raw data generation produces expected row count and injected flaws.
  - Verify cleaning removes duplicates, fixes casing, and eliminates nulls.
- `test_analytics.py`:
  - Verify KPI calculations match expected formulas.
  - Verify SQLite connection and query helper.
  - Verify OLS regression returns valid coefficients and $R^2 \ge 0.90$.
- `test_simulation.py`:
  - Verify simulation calculations handle edge inputs (e.g. 0 buffer, max buffer) monotonically.
