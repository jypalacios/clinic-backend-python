from pydantic import BaseModel, Field, field_validator


class SubAntecedentInput(BaseModel):
    id_cli_antecedente: int = Field(gt=0)
    det_sub_antecedente: str = Field(min_length=1)
    id_espect: int = Field(gt=0)

    @field_validator("det_sub_antecedente")
    @classmethod
    def strip_detail(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El detalle no puede estar vacío.")
        return value


class AntecedentOut(BaseModel):
    id_cli_antecedente: int
    det_cli_antecedente: str


class AntecedentSpecialtyOut(BaseModel):
    id_espect: int
    nom_espect: str


class SubAntecedentOut(SubAntecedentInput):
    id_sub_antecedente: int
    det_cli_antecedente: str
    nom_espect: str
