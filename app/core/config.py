"""
Configuración de la aplicación.
Todos los valores sensibles / dependientes del entorno se leen de variables
de entorno (inyectadas por docker-compose / .env). Nada queda hardcodeado.
"""
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # --- Conexión a PostgreSQL (obligatorio: .env) --------------------
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int
    DB_ECHO: bool

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.POSTGRES_USER)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Seguridad / JWT ----------------------------------------------
    JWT_SECRET: str = Field(
        default="changeme-in-env",
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "ALGORITHM"),
    )
    JWT_EXPIRE_MINUTES: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "JWT_EXPIRE_MINUTES",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
        ),
    )

    # --- Aplicación ---------------------------------------------------
    PROJECT_NAME: str = "ClinicaApp"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"  # development | production
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost"  # separados por coma

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- Repositorio (metadatos / trazabilidad de despliegue) ---------
    GITHUB_REPO_URL: str = ""
    GITHUB_BRANCH: str = "main"


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado: se lee el entorno una sola vez por proceso."""
    return Settings()
