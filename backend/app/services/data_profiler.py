import json
from typing import Any

from pathlib import Path

import pandas as pd


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
    }

def profile_csv(file_path: Path) -> dict[str, Any]:
    dataframe = load_csv(file_path)
    return profile_dataframe(dataframe)