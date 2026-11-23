import pytest
import sqlite3
import pandas as pd
import numpy as np
from src.analytics import (
    create_sqlite_db,
    compute_kpis,
    fit_driver_model,
    run_safe_sql,
    get_breakdown
)


@pytest.fixture
def sample_orders_df():
    data = {
        "order_id": range(1, 101),
        "hour": [12, 13, 20, 9] * 25,
        "dow": [0, 1, 2, 3] * 25,
        "zone": ["Koramangala", "Indiranagar", "HSR Layout", "Whitefield"] * 25,
        "restaurant_id": [1, 2, 3, 4] * 25,
        "rider_id": [10, 20, 30, 40] * 25,
        "rider_tenure_m": [2.0, 6.0, 15.0, 24.0] * 25,
        "distance_km": [2.5, 4.0, 6.5, 8.0] * 25,
        "weather": ["Clear", "Rain", "Heavy Rain", "Clear"] * 25,
        "order_value": [400, 600, 350, 800] * 25,
        "prep_min": [12.0, 18.0, 25.0, 15.0] * 25,
        "wait_min": [2.0, 4.0, 5.0, 1.0] * 25,
        "travel_min": [15.0, 22.0, 35.0, 40.0] * 25,
        "promised_min": [35.0, 45.0, 50.0, 60.0] * 25,
        "delivered_min": [29.0, 44.0, 65.0, 56.0] * 25,
        "sla_breach": [0, 0, 1, 0] * 25,
        "cancelled": [0, 0, 1, 0] * 25
    }
    return pd.DataFrame(data)


def test_compute_kpis(sample_orders_df):
    kpis = compute_kpis(sample_orders_df)
    assert kpis["orders"] == 100
    assert kpis["breach_pct"] == 25.0
    assert kpis["cancel_pct"] == 25.0
    assert kpis["lost_rev"] > 0
    assert kpis["gmv"] > 0


def test_create_sqlite_db_and_safe_sql(sample_orders_df):
    con = create_sqlite_db(sample_orders_df)
    res = run_safe_sql(con, "SELECT COUNT(*) as cnt FROM orders")
    assert res.iloc[0]["cnt"] == 100

    # Unsafe queries should raise ValueError
    with pytest.raises(ValueError):
        run_safe_sql(con, "DROP TABLE orders")

    with pytest.raises(ValueError):
        run_safe_sql(con, "DELETE FROM orders")


def test_get_breakdown(sample_orders_df):
    con = create_sqlite_db(sample_orders_df)
    zone_df = get_breakdown(con, "zone")
    assert "label" in zone_df.columns
    assert "v" in zone_df.columns
    assert len(zone_df) == 4


def test_fit_driver_model(sample_orders_df):
    drivers, r2 = fit_driver_model(sample_orders_df)
    assert not drivers.empty
    assert "label" in drivers.columns
    assert "v" in drivers.columns
    assert any("Distance" in lbl for lbl in drivers["label"].values)
