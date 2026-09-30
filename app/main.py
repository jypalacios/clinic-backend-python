from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.api.v1 import health

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])

# Aquí se agregan los demás routers a medida que se implementen:
# from app.api.v1 import auth, users, patients, doctors, appointments, clinical
# app.include_router(auth.router, prefix=settings.API_V1_PREFIX + "/auth", tags=["auth"])
# app.include_router(patients.router, prefix=settings.API_V1_PREFIX + "/patients", tags=["patients"])


@app.on_event("startup")
def verificar_conexion_bd() -> None:
    """Falla rápido si la BD no está disponible al iniciar el contenedor."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
