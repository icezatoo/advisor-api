from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    google_api_key: str = ""
    litellm_api_base: str = ""
    litellm_api_key: str = ""
    litellm_model: str = "gemini-2.5-flash"
    allowed_origins: str = "http://localhost:5678,http://localhost:3000"
    log_level: str = "INFO"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
