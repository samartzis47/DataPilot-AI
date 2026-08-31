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

def test_evaluate_data_quality_detects_numeric_outliers():
    dataframe = pd.DataFrame(
        {
            "value": [10, 11, 12, 13, 1000],
        }
    )

    quality = evaluate_data_quality(dataframe)

    outlier_issues = [
        issue
        for issue in quality["issues"]
        if issue["code"] == "numeric_outliers"
    ]

    assert len(outlier_issues) == 1

    outlier_issue = outlier_issues[0]

    assert outlier_issue["severity"] == "high"
    assert outlier_issue["column"] == "value"