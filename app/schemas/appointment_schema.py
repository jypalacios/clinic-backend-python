from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AppointmentTimeMixin(BaseModel):
    @field_validator("fecha_hora", check_fields=False)
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha y hora debe incluir zona horaria")
        return value


class AppointmentCreate(AppointmentTimeMixin):
    id_patients: int
    id_doctors: int
    tipo_appointment: int = Field(gt=0)
    fecha_hora: datetime
    estado: Literal["PROGRAMADA"] = "PROGRAMADA"


class AppointmentUpdate(AppointmentTimeMixin):
    id_doctors: int
    fecha_hora: datetime
    tipo_appointment: int | None = Field(default=None, gt=0)
    estado: str | None = None


class AppointmentIngresoUpdate(AppointmentTimeMixin):
    fec_ingreso: datetime
    fec_dilatacion: datetime | None = None
    prioridad: bool = False

    @field_validator("fec_dilatacion")
    @classmethod
    def require_dilatacion_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("La fecha de dilatación debe incluir zona horaria")
        return value

    @field_validator("fec_ingreso")
    @classmethod
    def require_ingreso_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha de ingreso debe incluir zona horaria")
        return value


class AppointmentOut(BaseModel):
    id_appointments: int
    id_patients: int
    id_doctors: int
    tipo_appointment: int | None = None
    fecha_hora: datetime
    nom_estado: str
    paciente: str | None = None
    medico: str | None = None
    discapacidad: bool = False
    fec_ingreso: datetime | None = None
    fec_dilatacion: datetime | None = None
    fec_finaliza: datetime | None = None
    prioridad: bool | None = None
    fec_creacion: datetime

    class Config:
        from_attributes = True


class AppointmentTypeOut(BaseModel):
    id_tipo_appointment: int
    nom_tipo_appointment: str
    logo: str | None = None
    path: str | None = None
