from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permissions
from app.db.session import get_db
from app.schemas.user_schema import PasswordUpdate, UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("users.view")),
):
    service = UserService(db)
    return service.list_users()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_permission("users.manage", "users.create")),
):
    service = UserService(db)
    try:
        return service.create_user(
            data,
            created_by=current_user.id,
            creator_permissions=current_user.role.permisos if current_user.role else [],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("users.view")),
):
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("users.manage")),
):
    service = UserService(db)
    try:
        return service.update_user(user_id, data, updated_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def update_user_password(
    user_id: int,
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions("users.manage")),
):
    service = UserService(db)
    try:
        service.update_password(user_id, data, updated_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("users.manage")),
):
    service = UserService(db)
    try:
        service.delete_user(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
