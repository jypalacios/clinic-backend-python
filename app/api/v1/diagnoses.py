from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.diagnosis_schema import DiagnosisCreate, DiagnosisOut, DiagnosisUpdate
from app.services.diagnosis_service import (
    DiagnosisConflictError,
    DiagnosisNotFoundError,
    DiagnosisService,
)

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DiagnosisNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, DiagnosisConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/", response_model=list[DiagnosisOut])
def list_diagnoses(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permissions("diagnoses.view")),
):
    return DiagnosisService(db).list_diagnoses()


@router.post("/", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    data: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("diagnoses.manage")),
):
    try:
        return DiagnosisService(db).create_diagnosis(data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.put("/{diag_id}", response_model=DiagnosisOut)
def update_diagnosis(
    diag_id: int,
    data: DiagnosisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("diagnoses.manage")),
):
    try:
        return DiagnosisService(db).update_diagnosis(diag_id, data, current_user.id)
    except (LookupError, ValueError) as exc:
        raise _http_error(exc) from exc
