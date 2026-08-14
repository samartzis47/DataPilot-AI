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
    }