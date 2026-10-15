from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    nom_role: str = Field(min_length=2, max_length=50)
    permisos: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    nom_role: str | None = Field(default=None, min_length=2, max_length=50)
    permisos: list[int] | None = None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_role: int
    nom_role: str
    permisos: list[int]


class PermissionCreate(BaseModel):
    nom_permiso: str = Field(min_length=2, max_length=100)


class PermissionUpdate(BaseModel):
    nom_permiso: str | None = Field(default=None, min_length=2, max_length=100)
    activo: bool | None = None


class PermissionOut(BaseModel):
    id_permiso: int
    nom_permiso: str
    permiso_key: str | None
    activo: bool
