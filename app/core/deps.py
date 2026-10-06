import unicodedata

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer()


def _normalize_role(role: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", role)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )
    aliases = {
        "administrador": "admin",
        "asistente": "assistant",
        "medico": "doctor",
    }
    return aliases.get(normalized, normalized)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Obtiene el usuario autenticado desde el token JWT."""
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin usuario asociado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: str):
    """Valida que el usuario autenticado tenga uno de los roles permitidos."""
    allowed = {_normalize_role(role) for role in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        role_name = _normalize_role(current_user.role.nom_role) if current_user.role else ""
        if role_name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este recurso",
            )
        return current_user

    return dependency


def require_permissions(*required_permissions: str):
    """Require every permission requested by the endpoint."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted = set(current_user.role.permisos if current_user.role else [])
        if not all(_has_permission(granted, permission) for permission in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este recurso",
            )
        return current_user

    return dependency


def require_any_permission(*permissions: str):
    """Require at least one permission from the supplied set."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        granted = set(current_user.role.permisos if current_user.role else [])
        if not any(_has_permission(granted, permission) for permission in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este recurso",
            )
        return current_user

    return dependency


def _has_permission(granted: set[str], permission: str) -> bool:
    if permission in granted:
        return True
    if permission.endswith(".view"):
        prefix = permission[:-5]
        return f"{prefix}.manage" in granted or f"{prefix}.create" in granted
    return False


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Alias de conveniencia para devolver el usuario autenticado."""
    return current_user
