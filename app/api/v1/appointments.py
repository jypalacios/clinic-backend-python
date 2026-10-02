from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.schemas.appointment_schema import AppointmentCreate, AppointmentOut
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/", response_model=list[AppointmentOut])
def list_appointments(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = AppointmentService(db)
    return service.list_appointments()


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant")),
):
    service = AppointmentService(db)
    try:
        return service.create_appointment(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "assistant", "doctor")),
):
    service = AppointmentService(db)
    appointment = service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    return appointment
