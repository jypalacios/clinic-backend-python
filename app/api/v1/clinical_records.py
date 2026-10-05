from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.clinical_record_schema import ClinicalEntryCreate, ClinicalRecordCreate, ClinicalRecordOut
from app.services.clinical_record_service import ClinicalRecordService

router = APIRouter(prefix="/clinical-records", tags=["clinical-records"])


@router.get("/", response_model=list[ClinicalRecordOut])
def list_clinical_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.view")),
):
    return ClinicalRecordService(db).list_records(current_user)


@router.post("/", response_model=ClinicalRecordOut, status_code=status.HTTP_201_CREATED)
def create_clinical_record(
    data: ClinicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.manage")),
):
    try:
        return ClinicalRecordService(db).create_record(data, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put(
    "/{record_id}/entries/{entry_id}",
    response_model=ClinicalRecordOut,
    status_code=status.HTTP_201_CREATED,
)
def correct_clinical_entry(
    record_id: int,
    entry_id: int,
    data: ClinicalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.manage")),
):
    try:
        return ClinicalRecordService(db).append_entry(record_id, data, entry_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/{record_id}/entries",
    response_model=ClinicalRecordOut,
    status_code=status.HTTP_201_CREATED,
)
def add_clinical_entry(
    record_id: int,
    data: ClinicalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.manage")),
):
    try:
        return ClinicalRecordService(db).append_entry(record_id, data, None, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def archive_clinical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.delete")),
):
    try:
        ClinicalRecordService(db).archive_record(record_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{record_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles("admin"))],
)
def restore_clinical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("medical_history.delete")),
):
    try:
        ClinicalRecordService(db).restore_record(record_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
