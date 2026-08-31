import pandas as pd

from app.services.outlier_detection import calculate_iqr_statistics


def test_iqr_excludes_missing_values_from_percentage():
    series = pd.Series([10, 11, 12, 13, 1000, None])

    statistics = calculate_iqr_statistics(series)

    assert statistics is not None
    assert statistics["outlier_count"] == 1
    assert statistics["outlier_percentage"] == 20.0


def test_iqr_returns_none_for_all_missing_values():
    series = pd.Series([None, None], dtype="float64")

    statistics = calculate_iqr_statistics(series)

    assert statistics is None