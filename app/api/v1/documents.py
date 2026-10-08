from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission
from app.db.session import get_db
from app.models.document import DocumentCatalog
from app.schemas.document_schema import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _current_user=Depends(require_any_permission("patients.view", "patients.manage")),
) -> list[DocumentCatalog]:
    statement = select(DocumentCatalog).order_by(DocumentCatalog.id_documents)
    return list(db.scalars(statement).all())
