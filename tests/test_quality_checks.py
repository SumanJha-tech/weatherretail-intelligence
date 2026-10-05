import pandas as pd
from src.quality.data_quality_checks import check_weather


def test_out_of_range_temperature_is_flagged():
    df = pd.DataFrame({
        "date": ["2024-01-01"], "city": ["Chicago"],
        "temp_max_c": [200.0], "temp_min_c": [10.0],
        "precipitation_mm": [0.0], "snowfall_cm": [0.0], "windspeed_max_kmh": [5.0],
    })
    report = check_weather(df)
    assert report["errors_found"] >= 1


def test_clean_weather_data_passes():
    df = pd.DataFrame({
        "date": ["2024-01-01"], "city": ["Chicago"],
        "temp_max_c": [10.0], "temp_min_c": [2.0],
        "precipitation_mm": [1.0], "snowfall_cm": [0.0], "windspeed_max_kmh": [12.0],
    })
    report = check_weather(df)
    assert report["errors_found"] == 0