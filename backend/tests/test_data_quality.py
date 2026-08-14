import pandas as pd

from app.services.data_quality import evaluate_data_quality


def test_evaluate_data_quality_detects_issues():
    dataframe = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Bob"],
            "revenue": [100, None, None],
        }
    )

    quality = evaluate_data_quality(dataframe)
    issues_by_code = {
        issue["code"]: issue
        for issue in quality["issues"]
    }

    assert quality["score"] == 66.67
    assert quality["missing_cell_count"] == 2
    assert issues_by_code["missing_values"]["severity"] == "high"
    assert issues_by_code["duplicate_rows"]["severity"] == "high"