from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://trustpay_user:trustpay_password@localhost:5432/trustpay"
    openai_api_key: str = ""
    jwt_secret: str = "trustpay-ai-development-secret-key"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()