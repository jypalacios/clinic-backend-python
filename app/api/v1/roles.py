from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.schemas.role_schema import (
    PermissionCreate,
    PermissionOut,
    PermissionUpdate,
    RoleCreate,
    RoleOut,
    RoleUpdate,
)
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _current_user=Depends(require_any_permission("users.view", "roles.manage")),
):
    return RoleService(db).list_roles()


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _current_user=Depends(require_any_permission("users.view", "roles.manage")),
):
    return RoleService(db).list_permissions()


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).create_role(
            data,
            created_by=current_user.id,
            ip=_client_ip(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    data: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).update_role(
            role_id,
            data,
            updated_by=current_user.id,
            ip=_client_ip(request),
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if str(exc) == "Rol no encontrado" else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/permissions",
    response_model=PermissionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).create_permission(
            data,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/permissions/{permission_id}", response_model=PermissionOut)
def update_permission(
    permission_id: int,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("roles.manage")),
):
    try:
        return RoleService(db).update_permission(
            permission_id,
            data,
            updated_by=current_user.id,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "Permiso no encontrado"
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
