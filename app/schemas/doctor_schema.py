from pydantic import BaseModel, EmailStr


class DoctorCreate(BaseModel):
    ape_doctors: str
    nom_doctors: str
    id_espect: int
    id_sexo: int
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None


class DoctorOut(BaseModel):
    id_doctors: int
    ape_doctors: str
    nom_doctors: str
    id_espect: int
    id_sexo: int
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None

    class Config:
        from_attributes = True
