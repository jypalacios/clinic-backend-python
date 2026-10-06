from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClinicalEntryCreate(BaseModel):
    motivo_consulta: str = Field(min_length=1, max_length=10000)
    examen_fisico: str | None = Field(default=None, max_length=20000)
    diagnostico: str | None = Field(default=None, max_length=20000)
    plan: str | None = Field(default=None, max_length=20000)
    formulacion: str | None = Field(default=None, max_length=20000)
    notas: str | None = Field(default=None, max_length=20000)


class ClinicalEntryCorrection(ClinicalEntryCreate):
    id_entries_rectifica: int


class ClinicalRecordCreate(ClinicalEntryCreate):
    id_patients: int


class ClinicalPatientOut(BaseModel):
    id_patients: int
    ced_patients: str
    nom_patients: str
    ape_patients: str


class ClinicalDoctorOut(BaseModel):
    id_doctors: int
    nom_doctors: str
    ape_doctors: str


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
    medico: str


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
