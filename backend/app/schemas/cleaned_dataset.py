from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CleaningRequest(BaseModel):
    remove_duplicate_rows: bool = False
    numeric_missing_strategy: Literal["keep", "mean", "median"] = "keep"
    text_missing_strategy: Literal["keep", "mode"] = "keep"
    numeric_outlier_strategy: Literal["keep", "remove", "clip_iqr"] = "keep"


class CleanedDatasetRead(BaseModel):
    id: int
    dataset_id: int
    original_filename: str
    stored_filename: str
    cleaning_config: CleaningRequest
    summary: dict[str, int]
    original_row_count: int
    cleaned_row_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)