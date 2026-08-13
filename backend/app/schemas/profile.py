from typing import Any

from pydantic import BaseModel

class NumericStatistics(BaseModel):
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float
    first_quartile: float
    third_quartile: float

class ColumnProfile(BaseModel):
    name: str
    data_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    numeric_statistics: NumericStatistics | None = None


class DatasetProfile(BaseModel):
    dataset_id: int
    original_filename: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: list[ColumnProfile]
    preview: list[dict[str, Any]]

