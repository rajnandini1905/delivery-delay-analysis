# Delivery Delay Root-Cause Analysis (Interactive Web Application & Portfolio Project)

**Business Question:** Why do food deliveries miss their promised time, and what operational interventions should be deployed first?

---

## 🎯 Job Description Competency Alignment

This project is structured specifically to demonstrate all 8 core Data Analyst responsibilities:

| Job Description Responsibility | How It Is Implemented in This Application | Location |
|---|---|---|
| **Proficient in SQL and Python with hands-on dashboarding** | Interactive Streamlit web app with dynamic Plotly charts, reactive KPI metrics, and live SQLite analytical processing. | `app.py`, `src/views/overview.py` |
| **Deep dive into historical data (sources, features, patterns)** | In-depth analysis of 20,000 orders across 7 Bangalore fulfillment clusters, feature distributions, and peak-hour delay patterns. | `src/views/data_cleaning.py`, `src/data_pipeline.py` |
| **Write queries, perform ad hoc analysis & reporting** | Live in-browser SQL Studio with pre-canned business reports, syntax safety guards, and one-click CSV export. | `src/views/sql_console.py`, `src/analytics.py` |
| **Perform analytical deep dives for strategy/product roadmap** | Standardised OLS regression model ($R^2 = 0.91$) isolating controllable levers (weather buffers, prep SLAs) from fixed physical constraints (distance). | `src/views/driver_model.py` |
| **Drive automation and process improvement** | Automated data hygiene pipeline and A/B scenario simulation testing surge incentives and dynamic ETA buffers to protect GMV. | `src/simulation.py`, `src/views/simulation_view.py` |
| **Translate analytical solutions into clear insights** | Dual-tier executive storytelling: plain-English business summaries and tactical recommendations alongside statistical deep dives. | `src/views/overview.py`, `INSIGHTS.md` |
| **Streamline the data cleaning process** | Automated sanitization: deduplicating 120 transmission drops, standardizing zone casing, and imputing 300 missing environmental fields. | `src/data_pipeline.py` |
| **Good documentation practices & meet deadlines** | Modular architecture, comprehensive data dictionary, full unit test suite with 100% pass rate, and clear execution instructions. | `docs/`, `tests/`, `README.md` |

---

## 🚀 Quick Start (Running the Working Application)

### 1. Launch the Interactive Web Application
Using the pre-configured virtual environment:
```bash
.venv/bin/streamlit run app.py
```
*The app will automatically open in your default browser at `http://localhost:8501`.*

### 2. Run the Automated Test Suite
```bash
.venv/bin/pytest tests/ -v
```
*Runs all 8 unit tests covering data generation, cleaning validation, SQL queries, OLS modeling, and A/B simulation math.*

### 3. Run the Headless Pipeline Script (Optional)
```bash
.venv/bin/python run_project.py
```
*Generates the raw CSVs, summary report `INSIGHTS.md`, and static `dashboard.html`.*

---

## 📂 Project Architecture

```
files2/
├── app.py                      # Streamlit application entrypoint & reactive filters
├── requirements.txt            # streamlit, plotly, pandas, numpy, pytest
├── run_project.py              # CLI batch execution pipeline
├── dashboard.html              # Static HTML dashboard report
├── INSIGHTS.md                 # Executive findings and operational action plan
├── queries.sql                 # Sample analytical queries
├── src/
│   ├── __init__.py
│   ├── data_pipeline.py        # Automated ingestion, flaw injection & cleaning
│   ├── analytics.py            # SQLite analytics, KPI aggregator & OLS regression
│   ├── simulation.py           # Rain incentive & ETA buffer A/B simulation engine
│   └── views/
│       ├── __init__.py
│       ├── overview.py         # Tab 1: Executive KPI overview & Plotly charts
│       ├── data_cleaning.py    # Tab 2: Raw vs clean reconciliation & feature dictionary
│       ├── driver_model.py     # Tab 3: Standardised OLS driver model
│       ├── sql_console.py      # Tab 4: Interactive SQL studio & ad-hoc runner
│       └── simulation_view.py  # Tab 5: Operational A/B scenario simulator
├── docs/
│   ├── specs/                  # Architecture & design specifications
│   └── plans/                  # Implementation plans
└── tests/
    ├── __init__.py
    ├── test_data_pipeline.py   # Unit tests for data generation and cleaning
    ├── test_analytics.py       # Unit tests for KPIs, SQLite & regression
    └── test_simulation.py      # Unit tests for A/B testing logic
```

---

## 💡 Key Analytical Findings
1. **Weather is the Primary Actionable Lever**: Clear weather SLA breach rate is 17.4%, but surges to 66.6% in Heavy Rain.
2. **Rider Experience Effect**: Partners with <3 months tenure experience a 36.0% breach rate versus 23.0% for seasoned partners (12+ months).
3. **Hotspot Bottlenecks**: Outer fulfillment zones (Electronic City, Whitefield, Hebbal) during dinner rush (19-22h) in heavy rain encounter up to 100% breach rates without dynamic buffering.
4. **Driver Model ($R^2 = 0.91$)**: Standardized regression proves route distance and restaurant prep time are the largest drivers of delivery delays.
