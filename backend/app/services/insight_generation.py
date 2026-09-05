import json
from typing import Any, Protocol

from app.core.config import settings
from app.schemas.dataset_insight import (
    GeneratedInsightPayload,
    InsightItem,
    RecommendationItem,
)


class InsightGenerationError(Exception):
    pass


class InsightProviderNotConfiguredError(InsightGenerationError):
    pass


class InsightProvider(Protocol):
    model: str | None

    def generate(self, report: dict[str, Any]) -> GeneratedInsightPayload:
        ...


def _severity(value: Any) -> str:
    return value if value in {"low", "medium", "high"} else "low"


def _rules_payload(report: dict[str, Any]) -> GeneratedInsightPayload:
    quality = report.get("quality") or {}
    score = quality.get("score")
    issues = quality.get("issues") or []
    columns = report.get("columns") or []
    insights: list[InsightItem] = []
    recommendations: list[RecommendationItem] = []

    if isinstance(score, (int, float)):
        quality_severity = "high" if score < 60 else "medium" if score < 85 else "low"
        insights.append(InsightItem(
            category="quality", severity=quality_severity,
            title="Overall data quality",
            description=f"The persisted quality score is {score:.2f} out of 100.",
            evidence=[f"Quality score: {score:.2f}"], confidence=1.0,
        ))
        if score < 85:
            recommendations.append(RecommendationItem(
                priority="high" if score < 60 else "medium",
                action="Review and clean the highest-impact quality issues first.",
                reason=f"The overall quality score is {score:.2f} out of 100.",
            ))

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        code = issue.get("code")
        severity = _severity(issue.get("severity"))
        message = str(issue.get("message") or "A data quality issue was detected.")
        if code == "missing_values":
            category, title = "missing_values", "Missing values need attention"
            action = "Impute, remove, or investigate missing values before modeling."
        elif code == "duplicate_rows":
            category, title = "duplicates", "Duplicate rows detected"
            action = "Deduplicate rows after confirming which records are canonical."
        elif code == "numeric_outliers":
            category, title = "outliers", "Numeric outliers detected"
            column = issue.get("column")
            action = f"Review outliers in {column or 'numeric columns'} and validate their source."
        else:
            continue
        insights.append(InsightItem(
            category=category, severity=severity, title=title,
            description=message, evidence=[message], confidence=0.95,
        ))
        recommendations.append(RecommendationItem(
            priority=severity, action=action, reason=message,
        ))

    for column in columns:
        if not isinstance(column, dict):
            continue
        name = str(column.get("name") or "column")
        missing = column.get("missing_percentage")
        statistics = column.get("numeric_statistics") or {}
        if isinstance(missing, (int, float)) and missing >= 20 and not any(
            item.title == f"High missingness in {name}" for item in insights
        ):
            insights.append(InsightItem(
                category="missing_values", severity="high",
                title=f"High missingness in {name}",
                description=f"Column {name} is missing {missing:.2f}% of its values.",
                evidence=[f"Missing percentage: {missing:.2f}%"], confidence=0.98,
            ))
        if isinstance(statistics, dict):
            outlier_percentage = statistics.get("outlier_percentage")
            if isinstance(outlier_percentage, (int, float)) and outlier_percentage >= 20:
                insights.append(InsightItem(
                    category="outliers", severity="high",
                    title=f"Outlier-heavy column {name}",
                    description=f"Column {name} has {outlier_percentage:.2f}% potential outliers.",
                    evidence=[f"Outlier percentage: {outlier_percentage:.2f}%"], confidence=0.95,
                ))
        if column.get("unique_count") == 1:
            insights.append(InsightItem(
                category="columns", severity="low", title=f"Constant column {name}",
                description=f"Column {name} has only one unique value.",
                evidence=["Unique values: 1"], confidence=0.99,
            ))

    row_count = report.get("row_count", "an unknown number of")
    column_count = report.get("column_count", "an unknown number of")
    filename = report.get("original_filename", "the dataset")
    summary = f"{filename} contains {row_count} rows and {column_count} columns."
    if isinstance(score, (int, float)):
        summary += f" Its persisted data-quality score is {score:.2f}/100."
    return GeneratedInsightPayload(
        summary=summary,
        insights=insights,
        recommendations=recommendations,
    )


class RulesInsightProvider:
    model = None

    def generate(self, report: dict[str, Any]) -> GeneratedInsightPayload:
        return _rules_payload(report)


class OpenAIInsightProvider:
    def __init__(self) -> None:
        api_key = settings.openai_api_key
        api_key_value = (
            api_key.get_secret_value() if hasattr(api_key, "get_secret_value") else str(api_key or "")
        )
        if not api_key_value.strip():
            raise InsightProviderNotConfiguredError
        self.model = settings.openai_model

    def generate(self, report: dict[str, Any]) -> GeneratedInsightPayload:
        try:
            from openai import OpenAI

            provider_report = {
                key: value for key, value in report.items() if key != "preview"
            }
            api_key = settings.openai_api_key
            api_key_value = (
                api_key.get_secret_value()
                if hasattr(api_key, "get_secret_value")
                else str(api_key)
            )
            client = OpenAI(
                api_key=api_key_value,
                timeout=settings.openai_timeout_seconds,
                max_retries=settings.openai_max_retries,
            )
            response = client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": "Generate concise, actionable data insights from this statistical report. Do not infer raw rows."},
                    {"role": "user", "content": json.dumps(provider_report)},
                ],
                text_format=GeneratedInsightPayload,
            )
            payload = response.output_parsed
            if not isinstance(payload, GeneratedInsightPayload):
                raise ValueError("Structured response was not parsed")
            return payload
        except InsightGenerationError:
            raise
        except Exception as exc:
            raise InsightGenerationError from exc


def get_insight_provider(provider: str) -> InsightProvider:
    if provider == "rules":
        return RulesInsightProvider()
    if provider == "openai":
        return OpenAIInsightProvider()
    raise InsightGenerationError


def generate_insight(
    report: dict[str, Any], *, provider: str
) -> tuple[GeneratedInsightPayload, str | None]:
    try:
        selected_provider = get_insight_provider(provider)
        payload = selected_provider.generate(report)
        return GeneratedInsightPayload.model_validate(payload), selected_provider.model
    except InsightGenerationError:
        raise
    except Exception as exc:
        raise InsightGenerationError from exc