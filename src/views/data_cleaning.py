"""Data Cleaning & Deep Dive View.

Aligned with Core Competencies:
- Streamline the data cleaning process to enhance the effectiveness of data analysis.
- Deep dive into historical data to understand its sources, feature sets, and identify patterns.
"""
import streamlit as st
import pandas as pd
from src.data_pipeline import get_data_cleaning_audit, get_feature_dictionary


def render_data_cleaning(raw_df: pd.DataFrame, clean_df: pd.DataFrame):
    st.subheader("🧹 Streamlined Data Cleaning & Historical Data Deep Dive")
    st.caption("Demonstrating automated data validation, quality reconciliation, and comprehensive documentation of feature sets.")

    # Data Quality Audit Cards
    audit = get_data_cleaning_audit(raw_df, clean_df)
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Raw Ingested Records", f"{audit['raw_records']:,}")
    with m2:
        st.metric("Duplicates Removed", f"{audit['duplicates_removed']:,}")
    with m3:
        st.metric("Null Values Imputed", f"{audit['nulls_imputed']:,}")
    with m4:
        st.metric("Casing Fixed", f"{audit['casing_anomalies_fixed']:,}")
    with m5:
        st.metric("Clean Data Retention", f"{audit['data_retention_rate']}%")

    st.markdown("---")

    # Deep Dive Tabs: Pipeline Architecture vs Data Dictionary vs Sample Records
    subtab1, subtab2, subtab3 = st.tabs([
        "🔬 Historical Data Deep Dive & Pipeline Steps",
        "📖 Comprehensive Feature Dictionary",
        "📋 Live Data Explorer & Export"
    ])

    with subtab1:
        st.markdown("#### 1. Data Cleaning Pipeline Architecture")
        st.write("""
        Real-world transactional streams contain ingestion artifacts, schema drifts, and transmission dropouts. 
        Our automated data cleaning pipeline enforces four deterministic transformation stages before feeding downstream analytical models:
        """)

        s1, s2 = st.columns(2)
        with s1:
            st.markdown("""
            - **1. Transmission Deduplication**: Drops duplicate order transmissions by unique `order_id`, preserving first arrival timestamp.
            - **2. Text Normalization**: Normalizes string entries to standard Title Case while preserving domain-specific acronyms (`HSR Layout`).
            """)
        with s2:
            st.markdown("""
            - **3. Missing Environmental Data Imputation**: Imputes unrecorded weather conditions to `'Unknown'` or mode fallback to avoid dropping valid transactions.
            - **4. Boundary Validation Rules**: Filters physical anomalies such as negative or zero delivery durations (`delivered_min > 0`) and distances (`distance_km > 0`).
            """)

        st.markdown("#### 2. Raw vs Clean Comparison Preview")
        col_raw, col_clean = st.columns(2)
        with col_raw:
            st.markdown("**Sample Raw Ingested Records (with casing and null anomalies):**")
            st.dataframe(raw_df[["order_id", "zone", "weather", "distance_km", "delivered_min"]].head(6), use_container_width=True)
        with col_clean:
            st.markdown("**Cleaned & Validated Records (normalized and sanitized):**")
            st.dataframe(clean_df[["order_id", "zone", "weather", "distance_km", "delivered_min"]].head(6), use_container_width=True)

    with subtab2:
        st.markdown("#### 📖 Feature Dictionary & Domain Assumptions")
        st.caption("Documenting historical data sources, categories, and business definitions.")
        feat_df = get_feature_dictionary()
        st.dataframe(feat_df, use_container_width=True, hide_index=True)

    with subtab3:
        st.markdown("#### 📋 Interactive Dataset Explorer")
        st.caption("Inspect and download the full sanitized dataset.")

        c_search, c_zone = st.columns([2, 1])
        with c_search:
            search_query = st.text_input("🔍 Search orders by Order ID or Keyword", "")
        with c_zone:
            zone_filter = st.selectbox("Filter Zone", ["All Zones"] + sorted(clean_df["zone"].unique().tolist()))

        filtered_view = clean_df.copy()
        if zone_filter != "All Zones":
            filtered_view = filtered_view[filtered_view["zone"] == zone_filter]
        if search_query:
            filtered_view = filtered_view[
                filtered_view.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            ]

        st.write(f"Showing **{len(filtered_view):,}** matching rows:")
        st.dataframe(filtered_view.head(200), use_container_width=True)

        csv_data = filtered_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Dataset as CSV",
            data=csv_data,
            file_name="delivery_orders_cleaned.csv",
            mime="text/csv"
        )
