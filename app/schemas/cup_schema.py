from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EXTRA_FIELDS = (
    "extra_i",
    "extra_ii",
    "extra_iii",
    "extra_iv",
    "extra_v",
    "extra_vi",
    "extra_vii",
    "extra_viii",
    "extra_ix",
)


class CupBase(BaseModel):
    descripcion: str | None = Field(default=None, max_length=255)
    extra_i: str | None = Field(default=None, max_length=255)
    extra_ii: str | None = Field(default=None, max_length=255)
    extra_iii: str | None = Field(default=None, max_length=255)
    extra_iv: str | None = Field(default=None, max_length=255)
    extra_v: str | None = Field(default=None, max_length=255)
    extra_vi: str | None = Field(default=None, max_length=255)
    extra_vii: str | None = Field(default=None, max_length=255)
    extra_viii: str | None = Field(default=None, max_length=255)
    extra_ix: str | None = Field(default=None, max_length=255)

    @field_validator("descripcion", *EXTRA_FIELDS)
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class CupCreate(CupBase):
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=255)
    habilitado: bool = True
    isstandargel: bool = False
    isstandmsps: bool = False


class CupUpdate(CupBase):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    habilitado: bool | None = None
    isstandargel: bool | None = None
    isstandmsps: bool | None = None


class CupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cup: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    habilitado: bool | None = None
    isstandargel: bool | None = None
    isstandmsps: bool | None = None
    extra_i: str | None = None
    extra_ii: str | None = None
    extra_iii: str | None = None
    extra_iv: str | None = None
    extra_v: str | None = None
    extra_vi: str | None = None
    extra_vii: str | None = None
    extra_viii: str | None = None
    extra_ix: str | None = None
    usu_creacion: int | None = None
    usu_creacion_nombre: str | None = None
    fec_creacion: datetime | None = None
    usu_actualizacion: int | None = None
    usu_actualizacion_nombre: str | None = None
    fec_actualizacion: datetime | None = None
