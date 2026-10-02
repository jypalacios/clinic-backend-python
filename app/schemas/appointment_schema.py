from datetime import datetime

from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    id_patients: int
    id_doctors: int
    fecha_hora: datetime
    estado: str


class AppointmentOut(BaseModel):
    id_appointments: int
    id_patients: int
    id_doctors: int
    fecha_hora: datetime
    estado: str

    class Config:
        from_attributes = True
