from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Revenue Agent"
    app_version: str = "1.0.0"

    frontend_url: str = "http://localhost:5173"
    # --------------------------------------------------
    # Database
    # --------------------------------------------------

    database_url: str = "sqlite:///./revenue_agent.db"

    # --------------------------------------------------
    # Razorpay
    # --------------------------------------------------

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    # --------------------------------------------------
    # Gemini
    # --------------------------------------------------

    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"

    # --------------------------------------------------
    # Settings configuration
    # --------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()