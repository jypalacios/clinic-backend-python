"""
Configuración de la aplicación.
Todos los valores sensibles / dependientes del entorno se leen de variables
de entorno (inyectadas por docker-compose / .env). Nada queda hardcodeado.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Conexión a PostgreSQL -----------------------------------------
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "clinica"
    DB_USER: str = "clinica_app"
    DB_PASSWORD: str = "changeme"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # --- Seguridad / JWT --------------------------------------------------
    JWT_SECRET: str = "changeme-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # --- Aplicación ---------------------------------------------------
    APP_NAME: str = "Clinica API"
    APP_ENV: str = "development"       # development | production
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost"  # separados por coma

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings cacheado: se lee el entorno una sola vez por proceso."""
    return Settings()
