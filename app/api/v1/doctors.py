from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.schemas.doctor_schema import DoctorCreate, DoctorOut
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/", response_model=list[DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = DoctorService(db)
    return service.list_doctors()


@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    service = DoctorService(db)
    try:
        return service.create_doctor(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = DoctorService(db)
    doctor = service.get_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Médico no encontrado")
    return doctor
