from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str
    fernet_key: str
    default_base_timezone: str = "America/New_York"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
