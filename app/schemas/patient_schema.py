from datetime import date

from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    ced_patients: str
    nom_patients: str
    ape_patients: str
    fec_nacimiento: date
    id_sexo: int
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    eps: str | None = None
    contacto_emergencia: str | None = None


class PatientOut(BaseModel):
    id_patients: int
    ced_patients: str
    nom_patients: str
    ape_patients: str
    fec_nacimiento: date
    id_sexo: int
    activo: bool = True
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    eps: str | None = None
    contacto_emergencia: str | None = None

    class Config:
        from_attributes = True
