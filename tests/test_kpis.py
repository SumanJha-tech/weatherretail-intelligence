import pandas as pd
from src.analysis.kpis import total_revenue, stockout_rate_pct


def test_total_revenue_sums_correctly():
    df = pd.DataFrame({"revenue": [100.0, 50.5, 25.25]})
    assert total_revenue(df) == 175.75


def test_stockout_rate_percent():
    df = pd.DataFrame({"stockout_flag": [True, False, False, False]})
    assert stockout_rate_pct(df) == 25.0