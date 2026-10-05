from pydantic import BaseModel


class SexoOut(BaseModel):
    id_sexo: int
    nom_sexo: str

    class Config:
        from_attributes = True
