from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.revision_system_schema import RevisionSystemCreate, RevisionSystemOut
from app.services.revision_system_service import RevisionSystemService

router = APIRouter(prefix="/revision-sistemas", tags=["revision-sistemas"])


@router.get("", response_model=list[RevisionSystemOut])
def list_revision_systems(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permissions("revision_systems.view")),
):
    return RevisionSystemService(db).list_all()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_revision_system(
    data: RevisionSystemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("revision_systems.manage")),
):
    try:
        RevisionSystemService(db).create(data.det_revision_sistemas, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Ítem de revisión por sistemas creado correctamente."}
