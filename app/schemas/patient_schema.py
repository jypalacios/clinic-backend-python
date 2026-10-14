from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.document_schema import DocumentOut


class PatientCreate(BaseModel):
    ced_patients: str = Field(min_length=1, max_length=20)
    id_documents: int = Field(gt=0)
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
    id_documents: int
    document: DocumentOut
    nom_patients: str
    ape_patients: str
    fec_nacimiento: date
    edad: int
    id_sexo: int
    nom_sexo: str
    activo: int = 0
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    eps: str | None = None
    contacto_emergencia: str | None = None

    @field_validator("activo", mode="before")
    @classmethod
    def normalize_activo(cls, value: object) -> int:
        if isinstance(value, bool):
            return 0 if value else 1
        if value in (0, 1):
            return int(value)
        raise ValueError("activo debe ser 0 (activo) o 1 (inactivo)")

    class Config:
        from_attributes = True
