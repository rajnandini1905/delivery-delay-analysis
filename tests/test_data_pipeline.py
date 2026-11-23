import pytest
import pandas as pd
import numpy as np
from src.data_pipeline import generate_synthetic_orders, clean_orders, load_or_generate_data


def test_generate_synthetic_orders_structure():
    raw_df = generate_synthetic_orders(n=500, seed=123)
    # Due to duplicate injection (+120 on full N or proportional), rows >= 500
    assert len(raw_df) >= 500
    expected_cols = {
        "order_id", "order_ts", "hour", "dow", "zone", "restaurant_id",
        "rider_id", "rider_tenure_m", "distance_km", "weather",
        "order_value", "prep_min", "wait_min", "travel_min",
        "promised_min", "delivered_min", "sla_breach", "cancelled"
    }
    assert expected_cols.issubset(set(raw_df.columns))
    # Verify injected mess
    assert raw_df["weather"].isnull().any()
    assert (raw_df["zone"].str.isupper()).any()


def test_clean_orders_cleans_imperfections():
    raw_df = generate_synthetic_orders(n=500, seed=123)
    clean_df = clean_orders(raw_df)

    # 1. No duplicate order IDs
    assert clean_df["order_id"].is_unique

    # 2. No null weather
    assert not clean_df["weather"].isnull().any()
    assert (clean_df["weather"] == "Unknown").sum() > 0

    # 3. Zone normalized
    assert "HSR Layout" in clean_df["zone"].values
    assert not (clean_df["zone"] == "HSR LAYOUT").any()
    assert not (clean_df["zone"] == "KORAMANGALA").any()

    # 4. Valid delivery and distance
    assert (clean_df["delivered_min"] > 0).all()
    assert (clean_df["distance_km"] > 0).all()


def test_load_or_generate_data(tmp_path):
    raw_df, clean_df = load_or_generate_data(str(tmp_path), n=200)
    assert len(clean_df) <= len(raw_df)
    assert (tmp_path / "orders_raw.csv").exists()
    assert (tmp_path / "orders_clean.csv").exists()
