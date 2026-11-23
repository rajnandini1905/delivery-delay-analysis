"""Delivery Delay Root-Cause Analysis - Interactive Portfolio Web Application.

Aligned with Core Competencies:
- Proficient in SQL and Python with hands-on dashboarding experience.
- Deep dive into historical data to understand its sources, feature sets, and identify patterns.
- Write queries, perform ad hoc analysis and create reporting to ensure the team is moving towards smarter decisions.
- Perform analytical deep dives to drive the product/strategy roadmap.
- Ability to drive automation and process improvement.
- Translate analytical solutions into useful insights and recommendations for technical and non-technical audiences.
- Streamline the data cleaning process to enhance the effectiveness of data analysis.
- Demonstrate good documentation practices and meet deadlines.
"""
import os
import streamlit as st
import pandas as pd
from src.data_pipeline import load_or_generate_data
from src.analytics import create_sqlite_db
from src.views.overview import render_overview
from src.views.data_cleaning import render_data_cleaning
from src.views.driver_model import render_driver_model
from src.views.sql_console import render_sql_console
from src.views.simulation_view import render_simulation_view

# Page Configuration
st.set_page_config(
    page_title="Delivery Delay Root-Cause Analytics",
    page_icon="🛵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f766e;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #0f766e;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_cached_datasets():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return load_or_generate_data(current_dir, n=20000)


def main():
    st.markdown('<div class="main-title">🛵 Delivery Delay Root-Cause Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Food Delivery Operations · Bangalore Fulfillment Network · 20,000 Historical Transactions</div>', unsafe_allow_html=True)

    # Ingest / Load Data
    raw_df, clean_df = get_cached_datasets()

    # Sidebar: Global Filters & JD Alignment
    st.sidebar.title("🎛️ Operational Filters")
    st.sidebar.caption("Filter real-time data across delivery zones, weather conditions, and operating hours.")

    # Zone Multi-Select
    all_zones = sorted(clean_df["zone"].unique().tolist())
    selected_zones = st.sidebar.multiselect(
        "Fulfillment Zone",
        options=all_zones,
        default=all_zones
    )

    # Weather Multi-Select
    all_weather = sorted(clean_df["weather"].unique().tolist())
    selected_weather = st.sidebar.multiselect(
        "Weather Condition",
        options=all_weather,
        default=all_weather
    )

    # Hour Range Slider
    hour_range = st.sidebar.slider(
        "Operating Hours (0-23)",
        min_value=0,
        max_value=23,
        value=(0, 23)
    )

    # Rider Tenure Slider
    max_tenure = float(clean_df["rider_tenure_m"].max())
    tenure_range = st.sidebar.slider(
        "Rider Platform Tenure (Months)",
        min_value=0.0,
        max_value=max_tenure,
        value=(0.0, max_tenure)
    )

    # Dynamic In-Memory Filtering
    filtered_df = clean_df[
        (clean_df["zone"].isin(selected_zones)) &
        (clean_df["weather"].isin(selected_weather)) &
        (clean_df["hour"].between(hour_range[0], hour_range[1])) &
        (clean_df["rider_tenure_m"].between(tenure_range[0], tenure_range[1]))
    ]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Filtered Dataset Scope:** `{len(filtered_df):,}` / `{len(clean_df):,}` orders ({len(filtered_df)/len(clean_df)*100:.1f}%)")



    # Populate in-memory SQLite store for active session
    con = create_sqlite_db(filtered_df if not filtered_df.empty else clean_df.head(0))

    # Main Tabs Layout
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executive Overview",
        "🧹 Data Pipeline & Deep Dive",
        "🔍 Root-Cause Driver Model (OLS)",
        "💻 Interactive SQL Studio",
        "🧪 A/B Scenario Simulator"
    ])

    with tab1:
        render_overview(filtered_df, con)

    with tab2:
        render_data_cleaning(raw_df, clean_df)

    with tab3:
        render_driver_model(filtered_df)

    with tab4:
        render_sql_console(con)

    with tab5:
        render_simulation_view(filtered_df)


if __name__ == "__main__":
    main()
