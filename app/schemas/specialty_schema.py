from pydantic import BaseModel, Field


class SpecialtyCreate(BaseModel):
    nom_espect: str = Field(min_length=2, max_length=100)


class SpecialtyOut(BaseModel):
    id_espect: int
    nom_espect: str

    class Config:
        from_attributes = True
