# Delivery Delay Root-Cause Analysis - Streamlit Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the delivery delay data project into a modular, production-ready, interactive Streamlit application with multi-tab dashboarding, data pipeline inspection, OLS driver model analysis, live SQL sandbox, and an A/B rain incentive simulator.

**Architecture:** A modular Python package where `app.py` handles layout and reactive filters, delegating data caching to `src/data_pipeline.py`, analytical metrics & OLS regressions to `src/analytics.py`, scenario simulation to `src/simulation.py`, and rendering to modular view components under `src/views/`.

**Tech Stack:** Python 3.12, Streamlit, Pandas, NumPy, Plotly, SQLite3, Pytest.

**Spec:** `/Users/vemulasaiharshil/Downloads/files2/docs/specs/2026-11-23-delivery-delay-streamlit-app-design.md`

## Global Constraints
- Target directory: `/Users/vemulasaiharshil/Downloads/files2`
- Python runtime: `/Users/vemulasaiharshil/Downloads/files2/.venv/bin/python`
- Clean modular design with strict separation of backend business logic from Streamlit UI calls.
- Automated tests written before or alongside implementation with `pytest`.

---

### Task 1: Environment & Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/views/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**
Define dependencies: `streamlit>=1.40.0`, `pandas>=2.2.0`, `numpy>=1.26.0`, `plotly>=5.24.0`, `pytest>=8.0.0`.

- [ ] **Step 2: Install dependencies into .venv**
Run `/Users/vemulasaiharshil/Downloads/files2/.venv/bin/pip install -r /Users/vemulasaiharshil/Downloads/files2/requirements.txt`.

- [ ] **Step 3: Create package skeleton directories**
Ensure `src/`, `src/views/`, and `tests/` exist with `__init__.py`.

---

### Task 2: Data Pipeline Engine (`src/data_pipeline.py`)

**Files:**
- Create: `src/data_pipeline.py`
- Test: `tests/test_data_pipeline.py`

**Interfaces:**
- Produces:
  - `generate_synthetic_orders(n=20000, seed=42) -> pd.DataFrame`
  - `clean_orders(raw_df: pd.DataFrame) -> pd.DataFrame`
  - `load_or_generate_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]`

- [ ] **Step 1: Write test for data generation and cleaning**
Test `generate_synthetic_orders` produces 20,000 rows with required columns; test `clean_orders` deduplicates rows, standardizes zone casing ("HSR Layout"), and fills missing weather.

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_data_pipeline.py`
Expected: FAIL (ModuleNotFoundError: No module named 'src.data_pipeline')

- [ ] **Step 3: Implement data_pipeline.py**
Implement `generate_synthetic_orders`, `clean_orders`, and `load_or_generate_data`.

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_data_pipeline.py`
Expected: PASS

---

### Task 3: SQLite Analytics & OLS Driver Model (`src/analytics.py`)

**Files:**
- Create: `src/analytics.py`
- Test: `tests/test_analytics.py`

**Interfaces:**
- Produces:
  - `create_sqlite_db(df: pd.DataFrame) -> sqlite3.Connection`
  - `compute_kpis(df: pd.DataFrame) -> dict`
  - `fit_driver_model(df: pd.DataFrame) -> tuple[pd.DataFrame, float]`
  - `run_safe_sql(con: sqlite3.Connection, query: str) -> pd.DataFrame`
  - `get_breakdown(con: sqlite3.Connection, dimension: str) -> pd.DataFrame`

- [ ] **Step 1: Write tests for analytics functions**
Test KPI calculations (breach rate, avg delivery, cancel rate, lost revenue), OLS driver model ($R^2 \ge 0.85$, top driver Distance), and SQL execution safety (blocking destructive SQL).

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_analytics.py`
Expected: FAIL

- [ ] **Step 3: Implement analytics.py**
Implement `create_sqlite_db`, `compute_kpis`, `fit_driver_model`, `run_safe_sql`, and `get_breakdown`.

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_analytics.py`
Expected: PASS

---

### Task 4: Scenario Simulation Engine (`src/simulation.py`)

**Files:**
- Create: `src/simulation.py`
- Test: `tests/test_simulation.py`

**Interfaces:**
- Produces:
  - `simulate_rain_intervention(df: pd.DataFrame, buffer_min: float, surge_incentive: float, supply_boost_pct: float) -> dict`

- [ ] **Step 1: Write test for simulation calculations**
Test that adding rain ETA buffer reduces SLA breach rate on rain orders, calculates orders saved, and computes net financial ROI.

- [ ] **Step 2: Run test to verify it fails**
Run: `.venv/bin/pytest tests/test_simulation.py`
Expected: FAIL

- [ ] **Step 3: Implement simulation.py**
Implement `simulate_rain_intervention`.

- [ ] **Step 4: Run test to verify it passes**
Run: `.venv/bin/pytest tests/test_simulation.py`
Expected: PASS

---

### Task 5: UI View Modules (`src/views/`)

**Files:**
- Create: `src/views/overview.py`
- Create: `src/views/data_cleaning.py`
- Create: `src/views/driver_model.py`
- Create: `src/views/sql_console.py`
- Create: `src/views/simulation_view.py`

- [ ] **Step 1: Implement overview.py**
Render KPI cards with target delta metrics, Plotly bar/line charts for SLA breach by Zone, Weather, Hour, and Hotspot matrix.

- [ ] **Step 2: Implement data_cleaning.py**
Render Raw vs Cleaned reconciliation metrics, interactive sample dataframe with search, and data dictionary.

- [ ] **Step 3: Implement driver_model.py**
Render horizontal Plotly bar chart for standardized OLS coefficients, $R^2$ indicator, and tactical operational insights.

- [ ] **Step 4: Implement sql_console.py**
Render SQL query selector with preloaded queries, text area editor, execution button, execution duration card, and CSV download.

- [ ] **Step 5: Implement simulation_view.py**
Render sliders for weather buffer, surge incentive, and rider supply boost, alongside projected breach reduction and ROI impact cards.

---

### Task 6: Main Entrypoint & App Assembly (`app.py`)

**Files:**
- Create: `app.py`

- [ ] **Step 1: Build sidebar filters**
Add sidebar controls: Zone multi-select, Weather multi-select, Hour range slider, and Rider tenure filter.

- [ ] **Step 2: Connect tabs to views**
Create 5 tabs (`📊 Executive Overview`, `🧹 Data Quality & Pipeline`, `🔍 Driver Model (OLS)`, `💻 SQL Console`, `🧪 A/B Simulator`) and mount the view functions.

- [ ] **Step 3: Add empty-filter guard**
Ensure graceful notification when filters return 0 rows.

---

### Task 7: End-to-End Verification & Launch

- [ ] **Step 1: Run full pytest suite**
Run: `.venv/bin/pytest tests/ -v`
Ensure all unit tests pass with 100% success.

- [ ] **Step 2: Verify Streamlit app runs**
Launch Streamlit headless smoke test: `.venv/bin/streamlit run app.py --server.headless true --server.port 8501`.
Verify healthy startup and responsiveness.
