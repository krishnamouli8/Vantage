"""Configuration for the API service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API configuration."""
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    # Database settings
    database_path: str = "/app/data/metrics.db"
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    # Settings
    debug: bool = False
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False


settings = Settings()
