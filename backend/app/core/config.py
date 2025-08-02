from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "land-saas"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "land_saas"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60   # one hour
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    AUTO_MIGRATE: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()  # singleton
