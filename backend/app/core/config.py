from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from sqlalchemy.engine import URL
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "DataPilot-AI"
    app_version: str = "0.1.0"
    app_description: str = (
        "DataPilot-AI is a powerful AI-powered data analysis tool "
        "that helps you extract insights from your data."
    )   
    Environment: str = "development"
    upload_dir: Path = BACKEND_DIR / "storage" / "uploads"
    cleaned_dir: Path = BACKEND_DIR / "storage" / "cleaned"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_MODEL",
    )
    openai_timeout_seconds: float = Field(
        default=30.0,
        validation_alias="OPENAI_TIMEOUT_SECONDS",
        gt=0,
    )
    openai_max_retries: int = Field(
        default=2,
        validation_alias="OPENAI_MAX_RETRIES",
        ge=0,
        le=5,
    )

    postgres_db: str = Field(validation_alias="POSTGRES_DB")
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(validation_alias="POSTGRES_PORT",
                               gt=0, le=65535,
    )
    @property
    def database_url(self) -> URL:
        return URL.create(
                   drivername="postgresql+psycopg",
                   username=self.postgres_user,
                   password=self.postgres_password.get_secret_value(),
                   host=self.postgres_host,
                   port=self.postgres_port,
                   database=self.postgres_db,
        )
    

    model_config = SettingsConfigDict(
      env_file = ".env",
      env_file_encoding = "utf-8",
      extra="ignore",
    )

settings = Settings()
    