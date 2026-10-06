from datetime import date

from pydantic import BaseModel, EmailStr, Field


class PatientCreate(BaseModel):
    ced_patients: str = Field(min_length=1, max_length=20)
    nom_patients: str = Field(min_length=1, max_length=100)
    ape_patients: str = Field(min_length=1, max_length=100)
    fec_nacimiento: date
    id_sexo: int = Field(gt=0)
    telefono: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=150)
    direccion: str | None = Field(default=None, max_length=255)
    eps: str | None = Field(default=None, max_length=100)
    contacto_emergencia: str | None = Field(default=None, max_length=200)


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
