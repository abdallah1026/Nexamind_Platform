from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    
    APP_NAME: str = "NexaMind Auth Service"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/nexamind"    
    
    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    API_KEY_PREFIX: str = "nx"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
