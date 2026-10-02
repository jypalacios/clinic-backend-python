from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    cedula: str
    nombre: str
    apellido: str
    usuario: str
    email: EmailStr
    password: str
    id_role: int
    id_estado: int = 1


class UserUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    usuario: str | None = None
    email: EmailStr | None = None
    id_role: int | None = None
    id_estado: int | None = None


class UserOut(BaseModel):
    id: int
    cedula: str
    nombre: str
    apellido: str
    usuario: str
    email: EmailStr
    id_role: int
    id_estado: int

    class Config:
        from_attributes = True
