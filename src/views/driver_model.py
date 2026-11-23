"""Driver Model View: Standardised OLS Regression and Strategic Deep Dive.

Aligned with Core Competencies:
- Perform analytical deep dives to drive the product/strategy roadmap.
- Translate analytical solutions into useful insights for technical and non-technical audiences.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from src.analytics import fit_driver_model


def render_driver_model(df: pd.DataFrame):
    st.subheader("🔍 Delay Root-Cause Driver Model (Standardised OLS)")
    st.caption("Demonstrating rigorous statistical modeling to prioritize operational levers for product and strategy roadmaps.")

    if len(df) < 50:
        st.warning("⚠️ Insufficient sample size under active filters to fit a reliable regression model. Please expand your selection.")
        return

    drivers_df, r2 = fit_driver_model(df)

    # Top summary metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Model Explanatory Power (R²)", f"{r2:.2f}", help="Proportion of total delivery duration variance explained by model predictors.")
    with m2:
        top_driver = drivers_df.iloc[0]["label"] if not drivers_df.empty else "N/A"
        st.metric("Leading Delay Driver", top_driver)
    with m3:
        st.metric("Statistical Methodology", "Standardised OLS", help="Predictors and target normalized to mean 0, variance 1 for standardized effect comparison.")

    st.markdown("---")

    # Chart & Table
    c_chart, c_table = st.columns([3, 2])

    with c_chart:
        st.markdown("##### 📊 Standardised Factor Effect Sizes (Beta Weights)")
        fig_driver = px.bar(
            drivers_df,
            x="v",
            y="label",
            orientation="h",
            color="direction",
            color_discrete_map={"Increases Delay": "#ef4444", "Decreases Delay": "#0f766e"},
            text="v",
            labels={"v": "Standardised Beta (|β|)", "label": "Operational Factor", "direction": "Impact"},
            title=f"Relative Impact on Total Delivery Time (R² = {r2:.2f})"
        )
        fig_driver.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20), yaxis={"categoryorder": "total ascending"})
        fig_driver.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        st.plotly_chart(fig_driver, use_container_width=True)

    with c_table:
        st.markdown("##### 📋 Controllability & Strategy Matrix")
        st.dataframe(
            drivers_df[["label", "v", "controllability", "recommendation"]].rename(columns={
                "label": "Factor",
                "v": "Beta",
                "controllability": "Operational Levers",
                "recommendation": "Strategic Action"
            }),
            use_container_width=True,
            hide_index=True
        )

    # Strategic Roadmap Breakdown
    st.markdown("---")
    st.markdown("### 🗺️ Strategy & Product Roadmap Translation")
    st.caption("Translating statistical beta weights into product features and operations initiatives.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        **1. Uncontrollable: Route Distance**
        - **Beta**: ~0.81 (Dominant physical determinant).
        - **Reality**: Customer and merchant locations cannot be altered post-checkout.
        - **Strategic Lever**: Implement dynamic delivery radius caps during peak traffic hours to prevent out-of-zone orders.
        """)
    with c2:
        st.markdown("""
        **2. Controllable: Rain Environmental Buffers**
        - **Beta**: ~0.18 (Rain) / ~0.26 (Heavy Rain).
        - **Reality**: Road friction and reduced fleet density create systemic delays.
        - **Strategic Lever**: Deploy automated weather triggers that dynamically increase customer ETAs by +10 to +18 mins upon rainfall detection.
        """)
    with c3:
        st.markdown("""
        **3. Controllable: Merchant Prep Time & SLAs**
        - **Beta**: ~0.31 (Second highest driver).
        - **Reality**: Delayed kitchen prep forces riders to wait, creating delivery cascades.
        - **Strategic Lever**: Stagger rider dispatch notifications by expected prep time; enforce SLA penalties on chronically slow kitchens.
        """)
