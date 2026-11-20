from pydantic import BaseModel, Field, field_validator


class RevisionSystemCreate(BaseModel):
    det_revision_sistemas: str = Field(min_length=1, max_length=255)

    @field_validator("det_revision_sistemas")
    @classmethod
    def strip_detail(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La descripción no puede estar vacía.")
        return value


class RevisionSystemOut(BaseModel):
    id_revision_sistema: int
    det_revision_sistemas: str
    usuario_creacion: str
    usuario_modificacion: str | None
