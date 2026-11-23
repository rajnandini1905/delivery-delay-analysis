"""Data Pipeline & Data Hygiene Engine.

Aligned with Core Competencies:
- Streamline the data cleaning process to enhance the effectiveness of data analysis.
- Deep dive into historical data to understand its sources, feature sets, and identify patterns.
- Demonstrate good documentation practices and maintain repeatable automated pipelines.
"""
import os
import datetime as dt
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def generate_synthetic_orders(n: int = 20000, seed: int = 42) -> pd.DataFrame:
    """Generate historical delivery orders with realistic operational variations and injected anomalies.
    
    Data Source Assumptions:
    - Bangalore food delivery network across 7 key fulfillment zones.
    - Realistic distributions for restaurant preparation, rider tenure, distance, and weather multiplier.
    - Injected realistic data-entry errors: missing weather, non-standard casing, duplicate transmissions.
    """
    rng = np.random.default_rng(seed)

    zones = {
        "Koramangala": (3.0, 0.25),
        "Indiranagar": (3.2, 0.30),
        "Whitefield": (6.5, 0.45),
        "HSR Layout": (3.5, 0.20),
        "Electronic City": (7.0, 0.40),
        "Jayanagar": (4.0, 0.15),
        "Hebbal": (5.5, 0.35)
    }

    zn = rng.choice(list(zones), n, p=[0.20, 0.17, 0.14, 0.16, 0.09, 0.14, 0.10])
    dist = np.array([max(0.5, rng.normal(zones[z][0], 1.2)) for z in zn])
    cong = np.array([zones[z][1] for z in zn])
    start = dt.datetime(2026, 6, 1)

    minute_probs = np.repeat([0.004, 0.006, 0.012, 0.03, 0.045, 0.05, 0.04, 0.035, 0.03, 0.025, 0.03, 0.045], 120)
    minute_probs = minute_probs / minute_probs.sum()

    ts = [
        start + dt.timedelta(days=int(d), minutes=int(m))
        for d, m in zip(rng.integers(0, 90, n), rng.choice(1440, n, p=minute_probs))
    ]
    hour = np.array([t.hour for t in ts])
    dow = np.array([t.weekday() for t in ts])
    weather = rng.choice(["Clear", "Rain", "Heavy Rain"], n, p=[0.62, 0.28, 0.10])

    rest = rng.integers(1, 121, n)
    rest_prep = rng.normal(16, 5, 120).clip(6, 35)
    prep = (rest_prep[rest - 1] + rng.normal(0, 3, n) + np.where(np.isin(hour, [13, 14, 20, 21]), 3, 0)).clip(4, None)

    rider = rng.integers(1, 301, n)
    tenure = rng.gamma(2.2, 5, 300).clip(0.5, 48)[rider - 1]
    peak = np.isin(hour, [12, 13, 14, 19, 20, 21, 22]).astype(int)

    wmult = pd.Series(weather).map({"Clear": 1.0, "Rain": 1.25, "Heavy Rain": 1.65}).values
    travel = dist * 3.6 * (1 + cong) * wmult * (1 + 0.18 * peak) * (1.25 - 0.25 * np.minimum(tenure, 24) / 24) + rng.normal(0, 2.5, n)
    wait = rng.exponential(2, n) * (1 + peak)

    total = (prep + wait + travel.clip(2, None)).round(1)
    promised = (32 + 4.6 * dist).round(0)
    breach = (total > promised).astype(int)
    cancel = (rng.random(n) < (0.012 + 0.03 * np.clip((total - promised) / 15, 0, 3))).astype(int)
    value = rng.lognormal(5.6, 0.5, n).round(0)

    df = pd.DataFrame({
        "order_id": range(1, n + 1),
        "order_ts": ts,
        "hour": hour,
        "dow": dow,
        "zone": zn,
        "restaurant_id": rest,
        "rider_id": rider,
        "rider_tenure_m": tenure.round(1),
        "distance_km": dist.round(2),
        "weather": weather,
        "order_value": value,
        "prep_min": prep.round(1),
        "wait_min": wait.round(1),
        "travel_min": travel.clip(2, None).round(1),
        "promised_min": promised,
        "delivered_min": total,
        "sla_breach": breach,
        "cancelled": cancel
    })

    # Realistic data flaws injected for cleaning audit showcase
    dirty = df.copy()
    n_null = min(300, max(1, int(0.015 * n)))
    n_case = min(150, max(1, int(0.0075 * n)))
    n_dup = min(120, max(1, int(0.006 * n)))

    dirty.loc[rng.choice(n, n_null, replace=False), "weather"] = None
    dirty.loc[rng.choice(n, n_case, replace=False), "zone"] = dirty["zone"].str.upper()
    dirty = pd.concat([dirty, dirty.sample(n_dup, random_state=1)])
    return dirty


def clean_orders(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Streamline data cleaning to ensure reliable, high-integrity downstream analysis.
    
    Cleaning stages:
    1. Deduplication: eliminates duplicate transmissions preserving first order entry.
    2. Casing normalization: standardizes zone labels to Title Case with acronym preservation (e.g., 'HSR Layout').
    3. Missing value treatment: imputes missing weather status as 'Unknown'.
    4. Boundary validation: filters non-positive delivery times and distances.
    """
    c = raw_df.drop_duplicates("order_id").copy()
    c["zone"] = c["zone"].astype(str).str.title().replace({
        "Hsr Layout": "HSR Layout",
        "Hsr layout": "HSR Layout"
    })
    c["weather"] = c["weather"].fillna("Unknown")
    c = c[(c["delivered_min"] > 0) & (c["distance_km"] > 0)]
    return c


def get_data_cleaning_audit(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> Dict[str, Any]:
    """Generate an audit trail quantifying data quality improvements."""
    raw_len = len(raw_df)
    clean_len = len(clean_df)
    duplicates_removed = raw_len - raw_df["order_id"].nunique()
    nulls_detected = int(raw_df.isnull().sum().sum())
    casing_anomalies = int((raw_df["zone"].astype(str).str.isupper()).sum())
    invalid_rows = int(((raw_df["delivered_min"] <= 0) | (raw_df["distance_km"] <= 0)).sum())

    return {
        "raw_records": raw_len,
        "clean_records": clean_len,
        "duplicates_removed": duplicates_removed,
        "nulls_imputed": nulls_detected,
        "casing_anomalies_fixed": casing_anomalies,
        "invalid_records_filtered": invalid_rows,
        "data_retention_rate": round(100.0 * clean_len / max(raw_len, 1), 2)
    }


def get_feature_dictionary() -> pd.DataFrame:
    """Data dictionary documenting historical data sources, feature types, and operational context."""
    features = [
        {"Feature": "order_id", "Type": "Integer", "Category": "Identifier", "Description": "Unique sequential order transaction identifier."},
        {"Feature": "order_ts", "Type": "Datetime", "Category": "Temporal", "Description": "Order placement timestamp across 90-day observation period."},
        {"Feature": "hour", "Type": "Integer (0-23)", "Category": "Temporal", "Description": "Hour of the day order was placed; captures rush-hour dynamics."},
        {"Feature": "dow", "Type": "Integer (0-6)", "Category": "Temporal", "Description": "Day of the week (0 = Monday, 6 = Sunday)."},
        {"Feature": "zone", "Type": "String", "Category": "Spatial", "Description": "Delivery fulfillment cluster (7 zones across Bangalore)."},
        {"Feature": "distance_km", "Type": "Float", "Category": "Spatial", "Description": "Calculated route distance between merchant and customer."},
        {"Feature": "weather", "Type": "Categorical", "Category": "Environmental", "Description": "Weather condition at dispatch: Clear, Rain, Heavy Rain."},
        {"Feature": "restaurant_id", "Type": "Integer", "Category": "Merchant", "Description": "Unique merchant partner ID (120 active kitchens)."},
        {"Feature": "prep_min", "Type": "Float", "Category": "Merchant", "Description": "Kitchen preparation duration before order is packed."},
        {"Feature": "rider_id", "Type": "Integer", "Category": "Fleet", "Description": "Assigned delivery rider partner ID (300 active riders)."},
        {"Feature": "rider_tenure_m", "Type": "Float", "Category": "Fleet", "Description": "Rider experience on the platform measured in months."},
        {"Feature": "wait_min", "Type": "Float", "Category": "Fleet", "Description": "Rider wait time at merchant before handoff."},
        {"Feature": "travel_min", "Type": "Float", "Category": "Fleet", "Description": "Transit time from restaurant pickup to customer doorstep."},
        {"Feature": "promised_min", "Type": "Float", "Category": "KPI / SLA", "Description": "SLA promised delivery estimate communicated at checkout."},
        {"Feature": "delivered_min", "Type": "Float", "Category": "KPI / SLA", "Description": "Actual total delivery time from checkout to doorstep."},
        {"Feature": "sla_breach", "Type": "Binary (0/1)", "Category": "KPI / Target", "Description": "Flag indicating if delivered_min exceeded promised_min."},
        {"Feature": "cancelled", "Type": "Binary (0/1)", "Category": "KPI / Target", "Description": "Flag indicating whether customer cancelled due to extreme delay."},
        {"Feature": "order_value", "Type": "Float (INR)", "Category": "Financial", "Description": "Gross Merchandise Value of the delivery order in ₹."}
    ]
    return pd.DataFrame(features)


def load_or_generate_data(data_dir: str, n: int = 20000) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load raw and clean CSVs from directory or generate them if absent."""
    raw_path = os.path.join(data_dir, "orders_raw.csv")
    clean_path = os.path.join(data_dir, "orders_clean.csv")

    if os.path.exists(raw_path) and os.path.exists(clean_path):
        raw_df = pd.read_csv(raw_path)
        clean_df = pd.read_csv(clean_path)
    else:
        raw_df = generate_synthetic_orders(n=n)
        clean_df = clean_orders(raw_df)
        raw_df.to_csv(raw_path, index=False)
        clean_df.to_csv(clean_path, index=False)

    return raw_df, clean_df
