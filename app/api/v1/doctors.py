from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.doctor_schema import DoctorCreate, DoctorOut, DoctorUserLink
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/", response_model=list[DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("doctors.view")),
):
    service = DoctorService(db)
    return service.list_doctors()


@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("doctors.manage")),
):
    service = DoctorService(db)
    try:
        return service.create_doctor(data, created_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("doctors.view")),
):
    service = DoctorService(db)
    doctor = service.get_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Médico no encontrado")
    return doctor


@router.put(
    "/{doctor_id}/user",
    response_model=DoctorOut,
    dependencies=[Depends(require_roles("admin"))],
)
def link_doctor_user(
    doctor_id: int,
    data: DoctorUserLink,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("doctors.link_user")),
):
    try:
        return DoctorService(db).link_user(doctor_id, data.id_user, updated_by=current_user.id)
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if str(exc) == "Médico no encontrado" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
