from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.api.v1 import appointments, auth, doctors, health, patients, users

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
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["users"])
app.include_router(patients.router, prefix=settings.API_V1_PREFIX, tags=["patients"])
app.include_router(doctors.router, prefix=settings.API_V1_PREFIX, tags=["doctors"])
app.include_router(appointments.router, prefix=settings.API_V1_PREFIX, tags=["appointments"])


@app.on_event("startup")
def verificar_conexion_bd() -> None:
    """Falla rápido si la BD no está disponible al iniciar el contenedor."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
