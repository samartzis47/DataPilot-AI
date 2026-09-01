from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.profile import DatasetProfile


class DatasetAnalysisRead(BaseModel):
    id: int
    dataset_id: int
    created_at: datetime
    report: DatasetProfile

    model_config = ConfigDict(from_attributes=True)