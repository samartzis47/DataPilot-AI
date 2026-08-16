import pandas as pd

from app.services.data_profiler import profile_dataframe


def test_profile_dataframe_detects_numeric_outlier():
    dataframe = pd.DataFrame(
        {
            "value": [10, 11, 12, 13, 1000],
        }
    )

    profile = profile_dataframe(dataframe)
    statistics = profile["columns"][0]["numeric_statistics"]

    assert statistics["outlier_count"] == 1
    assert statistics["outlier_percentage"] == 20.0