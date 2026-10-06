from pydantic import BaseModel, ConfigDict, Field

from app.core.permissions import Permission


class RoleCreate(BaseModel):
    nom_role: str = Field(min_length=2, max_length=50)
    permisos: list[Permission] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    nom_role: str | None = Field(default=None, min_length=2, max_length=50)
    permisos: list[Permission] | None = None


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_role: int
    nom_role: str
    permisos: list[str]
