"""Simulation Engine: A/B Testing & Operational Process Improvement.

Aligned with Core Competencies:
- Ability to drive automation and process improvement.
- Perform analytical deep dives to drive the product/strategy roadmap.
- Translate analytical solutions into useful insights and recommendations for business ROI.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


def simulate_rain_intervention(
    df: pd.DataFrame,
    buffer_min: float = 10.0,
    surge_incentive: float = 30.0,
    supply_boost_pct: float = 20.0
) -> Dict[str, Any]:
    """Simulate operational interventions for Rain & Heavy Rain conditions.
    
    Models the joint impact of:
    1. Dynamic ETA buffer (increasing customer tolerance and SLA compliance).
    2. Surge rider incentive (driving fleet supply boost, reducing queue & wait times).
    
    Returns quantitative projections: breach rate reduction, cancels prevented, net ROI.
    """
    rain_mask = df["weather"].isin(["Rain", "Heavy Rain"])
    rain_df = df[rain_mask]

    if rain_df.empty:
        return {
            "rain_orders": 0,
            "baseline_breaches": 0,
            "baseline_breach_pct": 0.0,
            "sim_breaches": 0,
            "sim_breach_pct": 0.0,
            "breach_reduction_pts": 0.0,
            "orders_saved_breach": 0,
            "baseline_cancels": 0,
            "sim_cancels": 0,
            "cancels_prevented": 0,
            "avg_order_val": 0.0,
            "gmv_saved": 0.0,
            "total_incentive_cost": 0.0,
            "net_benefit": 0.0,
            "roi_pct": 0.0
        }

    rain_orders = len(rain_df)
    baseline_breaches = int(rain_df["sla_breach"].sum())
    baseline_breach_pct = round(100.0 * baseline_breaches / rain_orders, 1)
    baseline_cancels = int(rain_df["cancelled"].sum())
    avg_val = float(rain_df["order_value"].mean())

    # 1. Supply boost impact: More riders reduce dispatch wait & congestion transit by up to 15%
    speed_factor = 1.0 - (0.15 * min(supply_boost_pct, 50.0) / 50.0)
    sim_delivered = rain_df["delivered_min"] * speed_factor

    # 2. Dynamic buffer impact: Extends SLA threshold communicated to customers
    sim_promised = rain_df["promised_min"] + buffer_min

    # Simulated breaches
    sim_breach_series = (sim_delivered > sim_promised)
    sim_breaches = int(sim_breach_series.sum())
    sim_breach_pct = round(100.0 * sim_breaches / rain_orders, 1)
    breach_reduction_pts = round(baseline_breach_pct - sim_breach_pct, 1)
    orders_saved_breach = max(0, baseline_breaches - sim_breaches)

    # 3. Cancellation mitigation: Lower delays directly suppress cancellation probability
    delay_gap = np.clip(sim_delivered - sim_promised, 0, 45)
    sim_cancel_prob = np.clip(0.012 + 0.03 * (delay_gap / 15.0), 0.008, 0.25)
    sim_cancels = int(np.round(sim_cancel_prob.sum()))
    cancels_prevented = max(0, baseline_cancels - sim_cancels)

    # 4. Financial Calculations
    gmv_saved = round(cancels_prevented * avg_val, 0)
    completed_orders = rain_orders - sim_cancels
    total_incentive_cost = round(completed_orders * surge_incentive, 0)
    net_benefit = round(gmv_saved - total_incentive_cost, 0)
    roi_pct = round((net_benefit / total_incentive_cost * 100.0), 1) if total_incentive_cost > 0 else 0.0

    return {
        "rain_orders": rain_orders,
        "baseline_breaches": baseline_breaches,
        "baseline_breach_pct": baseline_breach_pct,
        "sim_breaches": sim_breaches,
        "sim_breach_pct": sim_breach_pct,
        "breach_reduction_pts": breach_reduction_pts,
        "orders_saved_breach": orders_saved_breach,
        "baseline_cancels": baseline_cancels,
        "sim_cancels": sim_cancels,
        "cancels_prevented": cancels_prevented,
        "avg_order_val": round(avg_val, 1),
        "gmv_saved": gmv_saved,
        "total_incentive_cost": total_incentive_cost,
        "net_benefit": net_benefit,
        "roi_pct": roi_pct
    }
