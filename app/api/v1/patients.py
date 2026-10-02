from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.schemas.patient_schema import PatientCreate, PatientOut
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = PatientService(db)
    return service.list_patients()


@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant")),
):
    service = PatientService(db)
    try:
        return service.create_patient(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    return patient
