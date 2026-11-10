from pydantic import BaseModel, Field


class AnalysisAssignment(BaseModel):
    id_tipo_appointment: int = Field(gt=0)
    id_hc_detalle: int = Field(gt=0)


class AppointmentTypeOut(BaseModel):
    id_tipo_appointment: int
    nom_tipo_appointment: str


class AnalysisDetailOut(BaseModel):
    id_hc_detalle: int
    id_hc_general: int
    detalle: str
    general: str


class AnalysisAssignmentOut(BaseModel):
    id_hc_appointment: int
    id_tipo_appointment: int
    nom_tipo_appointment: str
    id_hc_detalle: int
    det_hc_general: str
