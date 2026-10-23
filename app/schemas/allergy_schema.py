from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AllergyTypeCreate(BaseModel):
    nom_tipo_alergia: str = Field(min_length=1, max_length=100)


class AllergyTypeUpdate(BaseModel):
    nom_tipo_alergia: str | None = Field(default=None, min_length=1, max_length=100)
    activo: bool | None = None


class AllergyTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tipo_alergia: int
    nom_tipo_alergia: str
    activo: bool
    usu_creacion: int | None = None
    usuario: str | None = None
    fec_creacion: datetime | None = None
    usu_actualizacion: int | None = None
    fec_actualizacion: datetime | None = None


class AllergyCreate(BaseModel):
    id_patients: int = Field(gt=0)
    id_tipo_alergia: int = Field(gt=0)


class AllergyUpdate(BaseModel):
    id_tipo_alergia: int | None = Field(default=None, gt=0)
    activo: bool | None = None


class AllergyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_alergia: int
    id_patients: int
    ced_patients: str | None = None
    nom_patients: str | None = None
    ape_patients: str | None = None
    id_tipo_alergia: int | None = None
    nom_tipo_alergia: str | None = None
    activo: bool | None = None
    usu_creacion: int | None = None
    fec_creacion: datetime | None = None
    usu_modificacion: int | None = None
    fec_modificacion: datetime | None = None
