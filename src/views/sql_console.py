"""SQL Console View: Ad-Hoc Analytics and Business Reporting.

Aligned with Core Competencies:
- Proficient in SQL and Python with hands-on analytical depth.
- Write queries, perform ad hoc analysis and create reporting to ensure the team is moving towards smarter decisions.
"""
import time
import streamlit as st
import pandas as pd
from src.analytics import run_safe_sql, get_preset_queries


def render_sql_console(con):
    st.subheader("💻 Interactive SQL Analytics & Ad-Hoc Reporting Studio")
    st.caption("Demonstrating advanced SQL proficiency: query authoring, ad-hoc data analysis, and instant report generation.")

    presets = get_preset_queries()

    # Preset Selector
    preset_titles = ["-- Select a Preloaded Business Report Query --"] + [p["title"] for p in presets]
    selected_preset_title = st.selectbox("📌 Load Pre-Canned Business Query Template", preset_titles)

    default_query = presets[0]["sql"]
    query_desc = presets[0]["desc"]

    if selected_preset_title != "-- Select a Preloaded Business Report Query --":
        for p in presets:
            if p["title"] == selected_preset_title:
                default_query = p["sql"]
                query_desc = p["desc"]
                break

    st.info(f"**Query Purpose:** {query_desc}")

    # SQL Editor Area
    user_query = st.text_area(
        label="SQL Query Editor (Target table: `orders`)",
        value=default_query,
        height=180,
        help="Execute read-only SQL queries against the in-memory SQLite analytical store."
    )

    c_run, c_schema = st.columns([1, 4])
    with c_run:
        run_btn = st.button("▶️ Execute Query", type="primary")

    if run_btn:
        start_time = time.time()
        try:
            result_df = run_safe_sql(con, user_query)
            duration_ms = round((time.time() - start_time) * 1000, 1)

            st.success(f"✅ Query executed successfully in **{duration_ms} ms** | Returned **{len(result_df):,}** rows.")

            # Display Results Table
            st.dataframe(result_df, use_container_width=True)

            # Export Button
            csv_data = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Report as CSV",
                data=csv_data,
                file_name="sql_adhoc_report.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"❌ SQL Execution Error: {str(e)}")

    st.markdown("---")
    with st.expander("🔍 View `orders` Table Schema & Available Columns"):
        st.code("""
TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    order_ts        DATETIME,
    hour            INTEGER (0-23),
    dow             INTEGER (0-6),
    zone            VARCHAR,
    restaurant_id   INTEGER,
    rider_id        INTEGER,
    rider_tenure_m  FLOAT,
    distance_km     FLOAT,
    weather         VARCHAR,
    order_value     FLOAT,
    prep_min        FLOAT,
    wait_min        FLOAT,
    travel_min      FLOAT,
    promised_min    FLOAT,
    delivered_min   FLOAT,
    sla_breach      INTEGER (0 or 1),
    cancelled       INTEGER (0 or 1)
);
        """, language="sql")
