from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from app.core.config import settings
from app.schemas.cleaned_dataset import CleaningRequest
from app.services.data_profiler import InvalidCSVError, load_csv
from app.services.outlier_detection import calculate_iqr_statistics


class DatasetCleaningError(ValueError):
    pass


def delete_cleaned_file(stored_filename: str) -> None:
    safe_filename = Path(stored_filename).name
    file_path = settings.cleaned_dir / safe_filename
    file_path.unlink(missing_ok=True)


def clean_dataset_file(
    source_path: Path,
    original_filename: str,
    cleaning_request: CleaningRequest,
) -> tuple[str, str, dict[str, int]]:
    try:
        dataframe = load_csv(source_path)
    except InvalidCSVError as exc:
        raise DatasetCleaningError(str(exc)) from exc

    original_row_count = len(dataframe)
    duplicate_rows_removed = 0
    missing_values_filled = 0
    outlier_values_clipped = 0
    outlier_values_removed = 0
    outlier_rows_removed = 0

    if cleaning_request.remove_duplicate_rows:
        duplicate_rows_removed = int(dataframe.duplicated().sum())
        dataframe = dataframe.drop_duplicates().reset_index(drop=True)

    for column_name in dataframe.columns:
        series = dataframe[column_name]

        if pd.api.types.is_numeric_dtype(series):
            if cleaning_request.numeric_missing_strategy != "keep":
                fill_value = getattr(series, cleaning_request.numeric_missing_strategy)()
                if pd.notna(fill_value):
                    missing_values_filled += int(series.isna().sum())
                    dataframe[column_name] = series.fillna(fill_value)
        elif cleaning_request.text_missing_strategy == "mode":
            modes = series.mode(dropna=True)
            if not modes.empty:
                missing_values_filled += int(series.isna().sum())
                dataframe[column_name] = series.fillna(modes.iloc[0])

    outlier_masks: dict[Any, pd.Series] = {}
    for column_name in dataframe.select_dtypes(include="number").columns:
        statistics = calculate_iqr_statistics(dataframe[column_name])
        if statistics is None:
            continue

        series = dataframe[column_name]
        outlier_mask = (series < statistics["lower_bound"]) | (
            series > statistics["upper_bound"]
        )
        outlier_masks[column_name] = outlier_mask

        if cleaning_request.numeric_outlier_strategy == "clip_iqr":
            outlier_values_clipped += int(outlier_mask.sum())
            dataframe[column_name] = series.clip(
                lower=statistics["lower_bound"],
                upper=statistics["upper_bound"],
            )

    if cleaning_request.numeric_outlier_strategy == "remove" and outlier_masks:
        outlier_frame = pd.DataFrame(outlier_masks)
        rows_to_remove = outlier_frame.any(axis=1)
        outlier_rows_removed = int(rows_to_remove.sum())
        outlier_values_removed = int(outlier_frame[rows_to_remove].sum().sum())
        dataframe = dataframe.loc[~rows_to_remove].reset_index(drop=True)

    stored_filename = f"{uuid4().hex}.csv"
    output_filename = f"cleaned_{Path(original_filename).name}"
    settings.cleaned_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.cleaned_dir / stored_filename
    try:
        dataframe.to_csv(output_path, index=False)
    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    summary = {
        "duplicate_rows_removed": duplicate_rows_removed,
        "missing_values_filled": missing_values_filled,
        "outlier_values_clipped": outlier_values_clipped,
        "outlier_values_removed": outlier_values_removed,
        "outlier_rows_removed": outlier_rows_removed,
        "original_row_count": int(original_row_count),
        "cleaned_row_count": int(len(dataframe)),
    }
    return output_filename, stored_filename, summary