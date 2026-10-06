from datetime import datetime

from typing import Literal

from pydantic import BaseModel, field_validator


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
    fecha_hora: datetime
    estado: Literal["PROGRAMADA"] = "PROGRAMADA"


class AppointmentUpdate(AppointmentTimeMixin):
    id_doctors: int
    fecha_hora: datetime


class AppointmentOut(BaseModel):
    id_appointments: int
    id_patients: int
    id_doctors: int
    fecha_hora: datetime
    estado: str
    fec_creacion: datetime

    class Config:
        from_attributes = True
