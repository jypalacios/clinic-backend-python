from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis_schema import (
    AnalysisAssignment, AnalysisAssignmentOut, AnalysisDetailOut, AppointmentTypeOut,
)
from app.services.analysis_service import AnalysisNotFoundError, AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/types", response_model=list[AppointmentTypeOut])
def list_types(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("analysis.view")),
):
    return AnalysisService(db).list_types()


@router.get("/details", response_model=list[AnalysisDetailOut])
def list_details(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("analysis.view")),
):
    return AnalysisService(db).list_details()


@router.get("/assignments", response_model=list[AnalysisAssignmentOut])
def list_assignments(
    type_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("analysis.view")),
):
    return AnalysisService(db).list_assignments(type_id)


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AnalysisAssignment,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("analysis.manage")),
):
    try:
        AnalysisService(db).save(data, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Asociación creada correctamente."}


@router.put("/assignments/{assignment_id}")
def update_assignment(
    assignment_id: int,
    data: AnalysisAssignment,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("analysis.manage")),
):
    if assignment_id <= 0:
        raise HTTPException(status_code=422, detail="El identificador debe ser positivo.")
    try:
        AnalysisService(db).save(data, user.id, assignment_id)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Asociación actualizada correctamente."}
