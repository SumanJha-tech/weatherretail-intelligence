from src.analysis.risk_scoring import compute_weather_anomaly_z, compute_inventory_pressure, compute_risk_score


def test_phoenix_heat_example_scores_near_41():
    """46°C against a 40±3°C normal, sensitivity 0.72, and 2 of 14 days of cover.

    z = 2, pressure = 1 - 2/14, score = 2 × 0.72 × pressure × (100/3) ≈ 41.
    """
    z = compute_weather_anomaly_z(46, 40, 3)
    assert round(z, 2) == 2.0

    pressure = compute_inventory_pressure(2, 14)
    assert round(pressure, 2) == 0.86

    score = compute_risk_score(z, 0.72, pressure)
    assert 38 <= score <= 44


def test_zero_anomaly_gives_zero_risk():
    score = compute_risk_score(0, 0.9, 0.9)
    assert score == 0


def test_risk_score_never_exceeds_100():
    score = compute_risk_score(10, 1, 1)
    assert score <= 100