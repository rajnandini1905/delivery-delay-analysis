"""Overview View: Executive KPI Dashboard and Operational Breakdowns.

Aligned with Core Competencies:
- Proficient in SQL and Python with hands-on dashboarding experience.
- Translate analytical solutions into useful insights for technical and non-technical audiences.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.analytics import compute_kpis, get_breakdown


def render_overview(df: pd.DataFrame, con):
    st.subheader("📊 Executive Operations & SLA Performance Dashboard")
    st.caption("Demonstrating hands-on Python/SQL dashboarding: monitoring real-time delivery KPIs across Bangalore fulfillment zones.")

    if df.empty:
        st.warning("⚠️ No orders found matching the active sidebar filters. Please broaden your selection.")
        return

    # Top KPI Cards
    kpis = compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)

    target_breach = 20.0
    breach_delta = round(kpis["breach_pct"] - target_breach, 1)

    with c1:
        st.metric(
            label="SLA Breach Rate",
            value=f"{kpis['breach_pct']}%",
            delta=f"{'+' if breach_delta > 0 else ''}{breach_delta}% vs 20% Target",
            delta_color="inverse"
        )
    with c2:
        st.metric(
            label="Avg Delivery Duration",
            value=f"{kpis['avg_min']} min",
            help="Total elapsed time from customer checkout to doorstep handoff."
        )
    with c3:
        st.metric(
            label="Order Cancellation Rate",
            value=f"{kpis['cancel_pct']}%",
            delta=f"{kpis['cancel_count']:,} cancelled orders",
            delta_color="inverse"
        )
    with c4:
        st.metric(
            label="Revenue Lost to Cancels",
            value=f"₹{kpis['lost_rev']:,.0f}",
            delta=f"Total GMV: ₹{kpis['gmv']:,.0f}",
            delta_color="off"
        )

    st.markdown("---")

    # Row 1 Charts: Zone & Weather
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("##### 📍 SLA Breach Rate by Fulfillment Zone")
        zone_df = get_breakdown(con, "zone")
        fig_zone = px.bar(
            zone_df,
            x="label",
            y="v",
            color="v",
            color_continuous_scale="Teal",
            text="v",
            labels={"label": "Fulfillment Zone", "v": "SLA Breach %"},
            title="Breach Rate % by Zone (Outer zones face severe delays)"
        )
        fig_zone.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Target SLA (20%)")
        fig_zone.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20), coloraxis_showscale=False)
        fig_zone.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_zone, use_container_width=True)

    with col_right:
        st.markdown("##### 🌧️ Impact of Weather Severity on SLA Breaches")
        wx_df = get_breakdown(con, "weather")
        fig_wx = px.bar(
            wx_df,
            x="label",
            y="v",
            color="label",
            color_discrete_map={"Clear": "#0f766e", "Rain": "#f59e0b", "Heavy Rain": "#ef4444", "Unknown": "#6b7280"},
            text="v",
            labels={"label": "Weather Condition", "v": "SLA Breach %"},
            title="Heavy Rain escalates breach rates up to ~67%"
        )
        fig_wx.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
        fig_wx.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_wx, use_container_width=True)

    # Row 2 Charts: Rush Hours & Hotspots
    col_hour, col_hot = st.columns(2)

    with col_hour:
        st.markdown("##### ⏰ Hourly SLA Breach Profile Across 24 Hours")
        hour_df = get_breakdown(con, "hour")
        fig_hour = px.line(
            hour_df,
            x="label",
            y="v",
            markers=True,
            labels={"label": "Hour of Day (0-23)", "v": "SLA Breach %"},
            title="Breaches surge during Lunch (12-14h) & Dinner (19-22h) rush"
        )
        fig_hour.add_vrect(x0=12, x1=14.5, fillcolor="orange", opacity=0.15, line_width=0, annotation_text="Lunch Rush")
        fig_hour.add_vrect(x0=19, x1=22.5, fillcolor="red", opacity=0.15, line_width=0, annotation_text="Dinner Rush")
        fig_hour.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_hot:
        st.markdown("##### 🔥 Peak-Hour Hotspot Analysis (Zone × Weather)")
        hot_df = get_breakdown(con, "peak_hotspots")
        fig_hot = px.bar(
            hot_df,
            x="v",
            y="label",
            orientation="h",
            color="v",
            color_continuous_scale="Reds",
            text="v",
            labels={"label": "Hotspot Cluster", "v": "Breach %"},
            title="Critical bottlenecks requiring fleet pre-allocation"
        )
        fig_hot.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20), yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
        fig_hot.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_hot, use_container_width=True)

    # Executive Storytelling & Recommendations
    st.markdown("---")
    st.markdown("### 💡 Executive Insights & Strategic Action Plan")
    st.caption("Translating analytical conclusions into actionable operational decisions for leadership.")

    c_ins, c_rec = st.columns(2)
    with c_ins:
        st.info("""
        **Key Analytical Findings:**
        - **Weather is the Primary Controllable Bottleneck**: Clear weather achieves a 17.4% breach rate, whereas Heavy Rain spikes failures to 66.6%.
        - **Rider Inexperience Penalty**: Partners with <3 months tenure experience a 36.0% breach rate compared to 23.0% for seasoned partners (12+ months).
        - **Outer-Zone Strain**: Electronic City, Whitefield, and Hebbal suffer elevated travel times compounded by traffic congestion.
        """)

    with c_rec:
        st.success("""
        **Operational Recommendations:**
        - **Dynamic Rain Buffers**: Automatically extend promised ETAs by +10 to +18 minutes during adverse weather.
        - **Targeted Surge Incentives**: Deploy ₹30–₹50/order rain bonuses to prevent fleet supply drop-offs.
        - **Cohort-Based Dispatch**: Route junior riders to short-distance, low-complexity clusters during their initial 90 days.
        - **Pre-positioning**: Mobilize fleet capacity in Whitefield and Electronic City 30 minutes prior to lunch (11:30) and dinner (18:30) surges.
        """)
