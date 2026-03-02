from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application
    APP_NAME: str = Field(default="")
    APP_VERSION: str = Field(default="")
    DEBUG: bool = Field(default=True)

    # Database
    DB_HOST: str = Field(default="")
    DB_PORT: int = Field(default=3306)
    DB_NAME: str = Field(default="")
    DB_USER: str = Field(default="")
    DB_PASSWORD: str = Field(default="")
    DB_POOL_MIN: int = Field(default=5)
    DB_POOL_MAX: int = Field(default=20)

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=1440)  # 1 day

    # Bootstrap admin user
    ADMIN_EMAIL: str = Field(default="")
    ADMIN_USERNAME: str = Field(default="")
    ADMIN_PASSWORD: str = Field(default="")

    # CORS
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    # File Upload
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_UPLOAD_SIZE: int = Field(default=0)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # LOG_FILE: str = Field(default="app.log")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
