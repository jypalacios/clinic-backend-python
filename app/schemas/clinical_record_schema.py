from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClinicalMeasureIn(BaseModel):
    id_hc_detalle: int
    derecho: str | None = Field(default=None, max_length=20)
    izquierdo: str | None = Field(default=None, max_length=20)
    detalle: str | None = Field(default=None, max_length=255)


class ClinicalMeasureOut(ClinicalMeasureIn):
    id_hc_medida: int
    detalle_medida: str | None = None
    general: str | None = None
    det_derecho: str | None = None
    det_izquierdo: str | None = None


class ClinicalEntryCreate(BaseModel):
    motivo_consulta: str = Field(min_length=1, max_length=10000)
    examen_fisico: str | None = Field(default=None, max_length=20000)
    diagnostico: str | None = Field(default=None, max_length=20000)
    plan: str | None = Field(default=None, max_length=20000)
    formulacion: str | None = Field(default=None, max_length=20000)
    notas: str | None = Field(default=None, max_length=20000)
    peso: float | None = Field(default=None, gt=0, le=1000)
    talle: float | None = Field(default=None, gt=0, le=300)
    id_cups: list[int] = Field(default_factory=list)
    id_diags: list[int] = Field(default_factory=list)
    medidas: list[ClinicalMeasureIn] = Field(default_factory=list)

class ClinicalEntryCorrection(ClinicalEntryCreate):
    id_entries_rectifica: int


class ClinicalRecordCreate(ClinicalEntryCreate):
    id_patients: int


class ClinicalPatientOut(BaseModel):
    id_patients: int
    ced_patients: str
    nom_patients: str
    ape_patients: str
    edad: int
    nom_sexo: str


class ClinicalDoctorOut(BaseModel):
    id_doctors: int
    nom_doctors: str
    ape_doctors: str


class ClinicalEntryDiagnosisOut(BaseModel):
    id_diag: int
    codigo: str
    diagnostico: str


class ClinicalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_entries: int
    id_clinics: int
    id_doctors: int
    id_entries_rectifica: int | None
    fec_entrada: datetime
    motivo_consulta: str
    examen_fisico: str | None
    diagnostico: str | None
    plan: str | None
    formulacion: str | None
    notas: str | None
    peso: float | None = None
    talle: float | None = None
    medidas: list[ClinicalMeasureOut] = Field(default_factory=list)
    medico: str
    nom_espect: str
    measure_mode: Literal["detalle", "ojos"]
    diagnosticos: list[ClinicalEntryDiagnosisOut] = Field(default_factory=list)

class ClinicalRecordOut(BaseModel):
    id_clinic: int
    id_patients: int
    patient: ClinicalPatientOut
    id_doctors: int
    doctor: ClinicalDoctorOut
    fec_creacion: datetime
    activo: bool
    total_entradas: int
    entries: list[ClinicalEntryOut] = Field(default_factory=list)
