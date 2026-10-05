from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    cedula: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    usuario: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=150)
    password: str = Field(min_length=8, max_length=128)
    id_role: int
    id_estado: int = 1


class UserUpdate(BaseModel):
    cedula: str | None = Field(default=None, min_length=1, max_length=20)
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    usuario: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=150)
    id_role: int | None = None
    id_estado: int | None = None


class PasswordUpdate(BaseModel):
    password: str = Field(min_length=8, max_length=128)


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
