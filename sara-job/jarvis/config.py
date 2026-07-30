"""Settings loaded from .env — per repo layout in Sara_Job_Arch.docx."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    supabase_url: str = ""

    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    usajobs_api_key: str = ""

    groq_api_key: str = ""
    openai_api_key: str = ""

    tavily_api_key: str = ""


settings = Settings()
