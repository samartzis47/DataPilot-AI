from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InsightGenerationRequest(BaseModel):
    provider: Literal["rules", "openai"] = "rules"
    analysis_id: int | None = Field(default=None, gt=0)


class InsightItem(BaseModel):
    category: Literal["quality", "missing_values", "duplicates", "outliers", "columns", "general"]
    severity: Literal["low", "medium", "high"]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    evidence: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(ge=0, le=1)


class RecommendationItem(BaseModel):
    priority: Literal["low", "medium", "high"]
    action: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=2000)


class GeneratedInsightPayload(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)
    insights: list[InsightItem] = Field(max_length=50)
    recommendations: list[RecommendationItem] = Field(max_length=50)


class DatasetInsightRead(GeneratedInsightPayload):
    id: int
    dataset_id: int
    analysis_id: int
    provider: Literal["rules", "openai"]
    model: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)