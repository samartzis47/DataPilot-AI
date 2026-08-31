import json
from typing import Any

from pathlib import Path

import pandas as pd
from app.services.data_quality import evaluate_data_quality
from app.services.outlier_detection import calculate_iqr_statistics


class InvalidCSVError(ValueError):
    pass


def load_csv(file_path: Path) -> pd.DataFrame:
    try:
        dataframe = pd.read_csv(file_path)
    except pd.errors.EmptyDataError as exc:
        raise InvalidCSVError("CSV file contains no data") from exc
    except pd.errors.ParserError as exc:
        raise InvalidCSVError("CSV file could not be parsed") from exc
    except UnicodeDecodeError as exc:
        raise InvalidCSVError("CSV file must use UTF-8 encoding") from exc

    return dataframe

def profile_dataframe(dataframe: pd.DataFrame) -> dict[str, Any]:
    row_count = len(dataframe)
    column_profiles = []

    for column_name in dataframe.columns:
        series = dataframe[column_name]
        missing_count = int(series.isna().sum())


        numeric_statistics = None

        if pd.api.types.is_numeric_dtype(series):
            non_null_series = series.dropna()

            iqr_statistics = calculate_iqr_statistics(non_null_series)

            if iqr_statistics is not None:
                first_quartile = iqr_statistics["first_quartile"]
                third_quartile = iqr_statistics["third_quartile"]
                outlier_count = iqr_statistics["outlier_count"]
                outlier_percentage = iqr_statistics["outlier_percentage"]
                numeric_statistics = {
                    "minimum": float(non_null_series.min()),
                    "maximum": float(non_null_series.max()),
                    "mean": round(float(non_null_series.mean()), 2),
                    "median": round(float(non_null_series.median()), 2),
                    "standard_deviation": round(
                        float(non_null_series.std(ddof=0)),
                        2,
                    ),
                    "first_quartile": round(first_quartile, 2),
                    "third_quartile": round(third_quartile, 2),
                    "outlier_count": outlier_count,
                    "outlier_percentage": outlier_percentage,
                }

        column_profiles.append(
            {
                "name": str(column_name),
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": (
                    round((missing_count / row_count) * 100, 2)
                    if row_count
                    else 0.0
                ),
                "unique_count": int(series.nunique(dropna=True)),
                "numeric_statistics": numeric_statistics,
            }
        )
    

    preview = json.loads(
        dataframe.head(5).to_json(
            orient="records",
            date_format="iso",
        )
    )

    return {
        "row_count": int(row_count),
        "column_count": int(len(dataframe.columns)),
        "duplicate_row_count": int(dataframe.duplicated().sum()),
        "columns": column_profiles,
        "preview": preview,
        "quality": evaluate_data_quality(dataframe),
    }

def profile_csv(file_path: Path) -> dict[str, Any]:
    dataframe = load_csv(file_path)
    return profile_dataframe(dataframe)