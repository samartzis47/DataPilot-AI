from pydantic import BaseModel, ConfigDict

class DatasetCreate(BaseModel):
    original_filename: str
    content_type: str
    size_bytes: int

class DatasetRead(DatasetCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)