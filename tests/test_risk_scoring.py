from src.analysis.risk_scoring import compute_weather_anomaly_z, compute_inventory_pressure, compute_risk_score


def test_worked_example_from_project_guide():
    # Phoenix: forecast 46C, normal 40C +/- 3C -> z = 2.0
    z = compute_weather_anomaly_z(46, 40, 3)
    assert round(z, 2) == 2.0

    # 2 days of stock left out of a healthy 14 -> pressure = 1 - 2/14 = 0.857
    pressure = compute_inventory_pressure(2, 14)
    assert round(pressure, 2) == 0.86

    # RiskScore should land close to 41, per PROJECT_GUIDE.md Section 14
    score = compute_risk_score(z, 0.72, pressure)
    assert 38 <= score <= 44


def test_zero_anomaly_gives_zero_risk():
    score = compute_risk_score(0, 0.9, 0.9)
    assert score == 0


def test_risk_score_never_exceeds_100():
    score = compute_risk_score(10, 1, 1)
    assert score <= 100