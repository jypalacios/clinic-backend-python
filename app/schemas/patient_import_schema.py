from pydantic import BaseModel

from app.schemas.patient_schema import PatientCreate


class PatientCSVRowError(BaseModel):
    row_number: int
    messages: list[str]


class PatientCSVPreviewRow(BaseModel):
    row_number: int
    patient: PatientCreate


class PatientCSVPreview(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    can_import: bool
    preview_rows: list[PatientCSVPreviewRow]
    errors: list[PatientCSVRowError]


class PatientCSVImportResult(BaseModel):
    imported_rows: int
