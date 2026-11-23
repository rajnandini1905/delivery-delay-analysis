"""Analytical Engine: SQL Analysis, KPI Aggregations, and OLS Driver Modeling.

Aligned with Core Competencies:
- Proficient in SQL and Python with hands-on analytical rigor.
- Write queries, perform ad hoc analysis and create reporting to drive smarter decisions.
- Perform analytical deep dives to drive the product/strategy roadmap.
- Translate analytical solutions into actionable insights for technical and business audiences.
"""
import time
import sqlite3
import re
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd


def create_sqlite_db(df: pd.DataFrame) -> sqlite3.Connection:
    """Initialize an in-memory SQLite analytical database populated with orders."""
    con = sqlite3.connect(":memory:", check_same_thread=False)
    # Mirror datetime as string for SQLite compatibility
    db_df = df.copy()
    if "order_ts" in db_df.columns:
        db_df["order_ts"] = db_df["order_ts"].astype(str)
    db_df.to_sql("orders", con, index=False, if_exists="replace")
    return con


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Compute high-level operational and financial KPIs."""
    if df.empty:
        return {
            "orders": 0,
            "breach_pct": 0.0,
            "avg_min": 0.0,
            "cancel_pct": 0.0,
            "lost_rev": 0.0,
            "gmv": 0.0,
            "breach_count": 0,
            "cancel_count": 0
        }

    total_orders = len(df)
    breach_count = int(df["sla_breach"].sum())
    cancel_count = int(df["cancelled"].sum())
    breach_pct = round(100.0 * breach_count / total_orders, 1)
    cancel_pct = round(100.0 * cancel_count / total_orders, 2)
    avg_min = round(float(df["delivered_min"].mean()), 1)
    lost_rev = round(float(df.loc[df["cancelled"] == 1, "order_value"].sum()), 0)
    gmv = round(float(df["order_value"].sum()), 0)

    return {
        "orders": total_orders,
        "breach_pct": breach_pct,
        "avg_min": avg_min,
        "cancel_pct": cancel_pct,
        "lost_rev": lost_rev,
        "gmv": gmv,
        "breach_count": breach_count,
        "cancel_count": cancel_count
    }


def fit_driver_model(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """Perform standardised Ordinary Least Squares (OLS) regression to identify root-cause delay drivers.
    
    Standardising variables allows direct comparison of beta coefficients to rank effect sizes.
    """
    if len(df) < 30:
        # Fallback for very small datasets
        empty_drivers = pd.DataFrame(columns=["label", "v", "sign", "controllability", "recommendation"])
        return empty_drivers, 0.0

    peak_hours = [12, 13, 14, 19, 20, 21, 22]
    X = pd.DataFrame({
        "Distance (km)": df["distance_km"],
        "Restaurant Prep Time": df["prep_min"],
        "Rider Tenure (months)": df["rider_tenure_m"],
        "Peak Rush Hour": df["hour"].isin(peak_hours).astype(int),
        "Rain": (df["weather"] == "Rain").astype(int),
        "Heavy Rain": (df["weather"] == "Heavy Rain").astype(int)
    })

    # Standardize predictors and target to mean 0, variance 1
    std_X = X.std()
    std_X[std_X == 0] = 1.0  # Prevent division by zero
    Z = (X - X.mean()) / std_X

    y_series = df["delivered_min"]
    y_std = y_series.std() if y_series.std() != 0 else 1.0
    y = (y_series - y_series.mean()) / y_std

    # Add intercept column
    A = np.c_[np.ones(len(Z)), Z.values]
    try:
        sol, residuals, rank, s = np.linalg.lstsq(A, y.values, rcond=None)
        beta = sol[1:]
        pred = A @ sol
        ss_res = np.sum((y.values - pred) ** 2)
        ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
        r2 = max(0.0, 1.0 - (ss_res / max(ss_tot, 1e-9)))
    except Exception:
        beta = np.zeros(X.shape[1])
        r2 = 0.0

    controllability_map = {
        "Distance (km)": ("Fixed / Structural", "Route optimization & cluster-based kitchen allocation."),
        "Restaurant Prep Time": ("High Operational Control", "Partner kitchen SLAs, dispatch delay offset, surge throttling."),
        "Rider Tenure (months)": ("High Operational Control", "Onboarding mentorship & routing new riders to low-complexity clusters."),
        "Peak Rush Hour": ("Medium Operational Control", "Dynamic batching & pre-positioning fleet ahead of meal rush."),
        "Rain": ("High Operational Control", "Dynamic weather ETA buffer (+10 min) & rider rain bonus."),
        "Heavy Rain": ("High Operational Control", "Protective delivery buffers (+18 min) & selective radius capping.")
    }

    labels = list(X.columns)
    abs_betas = np.abs(beta).round(3)
    signs = np.sign(beta)

    records = []
    for lbl, b_val, sign in zip(labels, abs_betas, signs):
        control, rec = controllability_map.get(lbl, ("Operational", "Monitor closely."))
        direction = "Increases Delay" if sign >= 0 else "Decreases Delay"
        records.append({
            "label": lbl,
            "v": float(b_val),
            "sign": int(sign),
            "direction": direction,
            "controllability": control,
            "recommendation": rec
        })

    drivers_df = pd.DataFrame(records).sort_values("v", ascending=False).reset_index(drop=True)
    return drivers_df, round(float(r2), 3)


def run_safe_sql(con: sqlite3.Connection, query: str) -> pd.DataFrame:
    """Execute read-only SQL queries with syntax safety checks and performance benchmarking."""
    clean_query = query.strip()
    # Security check: Ensure only SELECT / WITH statements are executed
    first_token = clean_query.split()[0].upper() if clean_query else ""
    if first_token not in ("SELECT", "WITH", "EXPLAIN"):
        raise ValueError("Security Violation: Only read-only queries (SELECT, WITH) are permitted.")

    # Guard against destructive keywords embedded in query
    destructive_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE"]
    for kw in destructive_keywords:
        if re.search(r"\b" + kw + r"\b", clean_query, re.IGNORECASE):
            raise ValueError(f"Security Violation: Destructive statement '{kw}' detected.")

    return pd.read_sql_query(clean_query, con)


def get_breakdown(con: sqlite3.Connection, dimension: str) -> pd.DataFrame:
    """Generate business dimensional aggregations via SQL."""
    queries = {
        "zone": """
            SELECT zone AS label, 
                   ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                   COUNT(*) AS n,
                   ROUND(AVG(delivered_min), 1) AS avg_delivery_min,
                   ROUND(AVG(distance_km), 2) AS avg_dist_km
            FROM orders 
            GROUP BY zone 
            ORDER BY v DESC
        """,
        "weather": """
            SELECT weather AS label, 
                   ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                   COUNT(*) AS n,
                   ROUND(AVG(delivered_min), 1) AS avg_delivery_min
            FROM orders 
            GROUP BY weather 
            ORDER BY v DESC
        """,
        "hour": """
            SELECT hour AS label, 
                   ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                   COUNT(*) AS n
            FROM orders 
            GROUP BY hour 
            ORDER BY hour ASC
        """,
        "rider_tenure": """
            SELECT 
                CASE 
                    WHEN rider_tenure_m < 3 THEN '1. <3 months (New Rider)'
                    WHEN rider_tenure_m < 12 THEN '2. 3-12 months (Intermediate)'
                    ELSE '3. 12+ months (Veteran)'
                END AS label,
                ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                COUNT(*) AS n
            FROM orders 
            GROUP BY 1 
            ORDER BY 1 ASC
        """,
        "prep_time": """
            SELECT 
                CASE 
                    WHEN prep_min < 12 THEN '1. Fast (<12 min)'
                    WHEN prep_min < 20 THEN '2. Moderate (12-20 min)'
                    ELSE '3. Slow (20+ min)'
                END AS label,
                ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                COUNT(*) AS n
            FROM orders 
            GROUP BY 1 
            ORDER BY 1 ASC
        """,
        "worst_restaurants": """
            SELECT 'Rest #' || restaurant_id AS label, 
                   ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                   COUNT(*) AS n,
                   ROUND(AVG(prep_min), 1) AS avg_prep_min
            FROM orders 
            GROUP BY restaurant_id 
            HAVING n >= 80 
            ORDER BY v DESC 
            LIMIT 10
        """,
        "peak_hotspots": """
            SELECT zone || ' | ' || weather AS label, 
                   ROUND(100.0 * AVG(sla_breach), 1) AS v, 
                   COUNT(*) AS n
            FROM orders 
            WHERE hour IN (12, 13, 14, 19, 20, 21, 22)
            GROUP BY zone, weather 
            HAVING n >= 30 
            ORDER BY v DESC 
            LIMIT 8
        """
    }

    q = queries.get(dimension)
    if not q:
        raise ValueError(f"Unknown breakdown dimension: {dimension}")
    return pd.read_sql_query(q, con)


def get_preset_queries() -> List[Dict[str, str]]:
    """Return preloaded operational SQL queries aligned with standard business questions."""
    return [
        {
            "title": "1. Zone-wise SLA Breach & Volume Analysis",
            "desc": "Identifies which geographic zones account for the highest SLA failure rates and operational strain.",
            "sql": """SELECT 
    zone,
    COUNT(*) AS total_orders,
    ROUND(AVG(distance_km), 2) AS avg_distance_km,
    ROUND(AVG(delivered_min), 1) AS avg_delivered_min,
    ROUND(100.0 * AVG(sla_breach), 1) AS breach_rate_pct,
    ROUND(100.0 * AVG(cancelled), 2) AS cancel_rate_pct
FROM orders
GROUP BY zone
ORDER BY breach_rate_pct DESC;"""
        },
        {
            "title": "2. Rider Experience Impact: New vs Veteran Fleet",
            "desc": "Evaluates delivery duration and SLA breach disparities between junior (<3 months) and experienced delivery partners.",
            "sql": """SELECT 
    CASE 
        WHEN rider_tenure_m < 3 THEN 'New Riders (<3 months)'
        WHEN rider_tenure_m < 12 THEN 'Mid-Tenure (3-12 months)'
        ELSE 'Veterans (12+ months)'
    END AS rider_cohort,
    COUNT(*) AS orders_delivered,
    ROUND(AVG(travel_min), 1) AS avg_travel_min,
    ROUND(100.0 * AVG(sla_breach), 1) AS sla_breach_pct
FROM orders
GROUP BY 1
ORDER BY sla_breach_pct DESC;"""
        },
        {
            "title": "3. Peak-Hour Weather Hotspots",
            "desc": "Isolates outer zone deliveries during meal peak hours under adverse weather to flag critical failure clusters.",
            "sql": """SELECT 
    zone,
    weather,
    COUNT(*) AS order_volume,
    ROUND(AVG(delivered_min), 1) AS avg_delivery_time,
    ROUND(100.0 * AVG(sla_breach), 1) AS breach_pct
FROM orders
WHERE hour IN (12, 13, 14, 19, 20, 21, 22)
GROUP BY zone, weather
HAVING order_volume >= 40
ORDER BY breach_pct DESC
LIMIT 10;"""
        },
        {
            "title": "4. Merchant Bottlenecks: Slowest Prep Times & Revenue at Risk",
            "desc": "Identifies kitchen partners causing handoff delays, correlating high prep times with cancellation losses.",
            "sql": """SELECT 
    restaurant_id,
    COUNT(*) AS orders_fulfilled,
    ROUND(AVG(prep_min), 1) AS avg_prep_time_min,
    ROUND(100.0 * AVG(sla_breach), 1) AS breach_pct,
    ROUND(SUM(CASE WHEN cancelled = 1 THEN order_value ELSE 0 END)) AS cancelled_gmv_loss
FROM orders
GROUP BY restaurant_id
HAVING orders_fulfilled >= 60
ORDER BY avg_prep_time_min DESC
LIMIT 10;"""
        }
    ]
