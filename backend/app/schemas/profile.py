from typing import Any, Literal

from pydantic import BaseModel


class NumericStatistics(BaseModel):
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float
    first_quartile: float
    third_quartile: float
    outlier_count: int
    outlier_percentage: float

class ColumnProfile(BaseModel):
    name: str
    data_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int
    numeric_statistics: NumericStatistics | None = None

class QualityIssue(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    message: str
    column: str | None = None

class DataQualitySummary(BaseModel):
    score: float
    missing_cell_count: int
    completeness_percentage: float
    duplicate_percentage: float
    issues: list[QualityIssue]

class DatasetProfile(BaseModel):
    dataset_id: int
    original_filename: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    columns: list[ColumnProfile]
    preview: list[dict[str, Any]]
    quality: DataQualitySummary

