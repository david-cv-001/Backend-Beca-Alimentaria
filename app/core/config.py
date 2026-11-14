from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "backend-beca-alimentaria"
    environment: str = "dev"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/beca_alimentaria"
    database_echo: bool = False

    jwt_secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    cors_origins: str = "http://localhost:4200"

    face_model_name: str = "Facenet512"
    face_detector_backend: str = "retinaface"
    face_distance_metric: str = "cosine"
    face_threshold: float = 0.32
    face_enforce_detection: bool = True
    face_align: bool = True

    first_superadmin_username: str = "superadmin"
    first_superadmin_email: str = "superadmin@beca.com"
    first_superadmin_password: str = "admin123"


settings = Settings()
