import pytest
import pandas as pd
import numpy as np
from src.simulation import simulate_rain_intervention


@pytest.fixture
def rain_orders_df():
    data = {
        "order_id": range(1, 201),
        "weather": ["Rain"] * 100 + ["Heavy Rain"] * 100,
        "order_value": [500] * 200,
        "delivered_min": [50.0] * 100 + [65.0] * 100,
        "promised_min": [45.0] * 200,
        "sla_breach": [1] * 200,
        "cancelled": [0] * 190 + [1] * 10
    }
    return pd.DataFrame(data)


def test_simulate_rain_intervention_buffer_reduces_breach(rain_orders_df):
    # With 0 buffer and 0 incentive, sim matches baseline
    base_res = simulate_rain_intervention(rain_orders_df, buffer_min=0, surge_incentive=0, supply_boost_pct=0)
    assert base_res["baseline_breach_pct"] == 100.0
    assert base_res["sim_breach_pct"] == 100.0
    assert base_res["breach_reduction_pts"] == 0.0

    # With 10 min buffer, deliveries at 50 min are <= 55 promised min -> breaches drop by 50%
    buff_res = simulate_rain_intervention(rain_orders_df, buffer_min=10, surge_incentive=30, supply_boost_pct=15)
    assert buff_res["sim_breach_pct"] < base_res["baseline_breach_pct"]
    assert buff_res["orders_saved_breach"] > 0
    assert buff_res["total_incentive_cost"] > 0
    assert "net_benefit" in buff_res
