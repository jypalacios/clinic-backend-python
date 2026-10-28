from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

MAX_NIT = 2_147_483_647


class EntityCreate(BaseModel):
    nit: int = Field(gt=0, le=MAX_NIT)
    nom_entidad: str = Field(min_length=1, max_length=200)
    activo: bool = True


class EntityUpdate(BaseModel):
    nom_entidad: str | None = Field(default=None, min_length=1, max_length=200)
    activo: bool | None = None


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nit: int
    nom_entidad: str
    activo: bool | None = None
    usu_creacion: int | None = None
    usu_creacion_nombre: str | None = None
    fec_creacion: datetime | None = None
    usu_actualizacion: int | None = None
    usu_actualizacion_nombre: str | None = None
    fec_actualizacion: datetime | None = None
