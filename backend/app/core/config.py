from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DataPilot-AI"
    app_version: str = "0.1.0"
    app_description: str = (
        "DataPilot-AI is a powerful AI-powered data analysis tool "
        "that helps you extract insights from your data."
    )   
    Environment: str = "development"

    model_config = SettingsConfigDict(
      env_file = ".env",
      env_file_encoding = "utf-8",
      extra="ignore",
    )

settings = Settings()
    