from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.patient_import_schema import PatientCSVImportResult, PatientCSVPreview
from app.schemas.patient_schema import PatientCreate, PatientOut
from app.services.patient_csv_import_service import MAX_CSV_BYTES, PatientCSVImportService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


async def _read_csv_upload(file: UploadFile) -> bytes:
    try:
        return await file.read(MAX_CSV_BYTES + 1)
    finally:
        await file.close()


@router.get("/", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("patients.view", "my_patients.view")),
):
    service = PatientService(db)
    return service.list_patients(current_user)


@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("patients.manage")),
):
    service = PatientService(db)
    try:
        return service.create_patient(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/import/preview", response_model=PatientCSVPreview)
async def preview_patient_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _permission=Depends(require_permissions("patients.manage")),
):
    try:
        content = await _read_csv_upload(file)
        return PatientCSVImportService(db).preview(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/import", response_model=PatientCSVImportResult, status_code=status.HTTP_201_CREATED)
async def import_patients_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("patients.manage")),
):
    try:
        content = await _read_csv_upload(file)
        imported_rows = PatientCSVImportService(db).import_file(file.filename, content, current_user)
        return PatientCSVImportResult(imported_rows=imported_rows)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission("patients.view", "my_patients.view")),
):
    service = PatientService(db)
    patient = service.get_patient(patient_id, current_user)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    return patient
