from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from sqlalchemy.engine import URL



class Settings(BaseSettings):
    app_name: str = "DataPilot-AI"
    app_version: str = "0.1.0"
    app_description: str = (
        "DataPilot-AI is a powerful AI-powered data analysis tool "
        "that helps you extract insights from your data."
    )   
    Environment: str = "development"

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
    