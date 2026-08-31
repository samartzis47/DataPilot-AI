from typing import Any

import pandas as pd


def evaluate_data_quality(dataframe: pd.DataFrame) -> dict[str, Any]:
    row_count = len(dataframe)
    total_cells = row_count * len(dataframe.columns)

    missing_cell_count = int(dataframe.isna().sum().sum())
    duplicate_row_count = int(dataframe.duplicated().sum())

    completeness_percentage = (
        round((1 - missing_cell_count / total_cells) * 100, 2)
        if total_cells
        else 100.0
    )

    duplicate_percentage = (
        round((duplicate_row_count / row_count) * 100, 2)
        if row_count
        else 0.0
    )

    issues: list[dict[str, Any]] = []

    incomplete_percentage = round(
        100 - completeness_percentage,
        2,
    )

    if missing_cell_count > 0:
        if incomplete_percentage >= 20:
            severity = "high"
        elif incomplete_percentage >= 5:
            severity = "medium"
        else:
            severity = "low"

        issues.append(
            {
                "code": "missing_values",
                "severity": severity,
                "message": (
                    f"Dataset contains {missing_cell_count} missing cells "
                    f"({incomplete_percentage}% incomplete)."
                ),
                "column": None,
            }
        )

    if duplicate_row_count > 0:
        if duplicate_percentage >= 20:
            severity = "high"
        elif duplicate_percentage >= 5:
            severity = "medium"
        else:
            severity = "low"

        issues.append(
            {
                "code": "duplicate_rows",
                "severity": severity,
                "message": (
                    f"Dataset contains {duplicate_row_count} duplicate rows "
                    f"({duplicate_percentage}% of all rows)."
                ),
                "column": None,
            }
        )
    numeric_columns = dataframe.select_dtypes(include="number").columns

    for column_name in numeric_columns:
        non_null_series = dataframe[column_name].dropna()

        if non_null_series.empty:
            continue

        first_quartile = non_null_series.quantile(0.25)
        third_quartile = non_null_series.quantile(0.75)
        interquartile_range = third_quartile - first_quartile

        lower_bound = first_quartile - 1.5 * interquartile_range
        upper_bound = third_quartile + 1.5 * interquartile_range

        outlier_count = int(
            (
                (non_null_series < lower_bound)
                | (non_null_series > upper_bound)
            ).sum()
        )

        if outlier_count == 0:
            continue

        outlier_percentage = round(
            outlier_count / len(non_null_series) * 100,
            2,
        )

        if outlier_percentage >= 20:
            severity = "high"
        elif outlier_percentage >= 5:
            severity = "medium"
        else:
            severity = "low"

        issues.append(
            {
                "code": "numeric_outliers",
                "severity": severity,
                "message": (
                    f"Column '{column_name}' contains {outlier_count} "
                    f"potential outliers "
                    f"({outlier_percentage}% of non-null values)."
                ),
                "column": str(column_name),
            }
        )
    quality_score = round(
        completeness_percentage * 0.7
        + (100 - duplicate_percentage) * 0.3,
        2,
    )

    return {
        "score": quality_score,
        "missing_cell_count": missing_cell_count,
        "completeness_percentage": completeness_percentage,
        "duplicate_percentage": duplicate_percentage,
        "issues": issues,
    }