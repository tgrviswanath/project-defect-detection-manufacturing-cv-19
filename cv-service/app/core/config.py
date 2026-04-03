from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "Defect Detection CV Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    MAX_IMAGE_SIZE: int = 1280
    CONFIDENCE_THRESHOLD: float = 0.35

    class Config:
        env_file = ".env"

settings = Settings()
