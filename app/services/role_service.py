from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.schemas.role_schema import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, db: Session):
        self.repo = RoleRepository(db)

    def list_roles(self) -> list[Role]:
        return self.repo.list_all()

    def create_role(self, data: RoleCreate, created_by: int) -> Role:
        name = data.nom_role.strip().upper()
        if len(name) < 2:
            raise ValueError("El nombre del rol debe tener al menos 2 caracteres")
        if self.repo.get_by_name(name):
            raise ValueError("Ya existe un rol con ese nombre")
        role = Role(nom_role=name, permisos=list(dict.fromkeys(data.permisos)), usu_creacion=created_by)
        return self.repo.create(role)

    def update_role(self, role_id: int, data: RoleUpdate, updated_by: int) -> Role:
        role = self.repo.get_by_id(role_id)
        if not role:
            raise ValueError("Rol no encontrado")

        changes = data.model_dump(exclude_unset=True)
        if "nom_role" in changes and changes["nom_role"] is not None:
            name = changes["nom_role"].strip().upper()
            if len(name) < 2:
                raise ValueError("El nombre del rol debe tener al menos 2 caracteres")
            existing = self.repo.get_by_name(name)
            if existing and existing.id_role != role_id:
                raise ValueError("Ya existe un rol con ese nombre")
            role.nom_role = name
        if "permisos" in changes and changes["permisos"] is not None:
            permissions = list(dict.fromkeys(changes["permisos"]))
            if "roles.manage" not in permissions:
                active_user = (
                    self.repo.db.query(User.id)
                    .filter(User.id_role == role_id, User.id_estado == 1)
                    .first()
                )
                another_manager = (
                    self.repo.db.query(User.id)
                    .join(Role, User.id_role == Role.id_role)
                    .filter(
                        User.id_role != role_id,
                        User.id_estado == 1,
                        Role.permisos.contains(["roles.manage"]),
                    )
                    .first()
                )
                if active_user and not another_manager:
                    raise ValueError("No se pueden retirar los permisos de roles al último administrador activo")
            role.permisos = permissions

        role.usu_actualizacion = updated_by
        role.fec_actualizacion = datetime.now(timezone.utc)
        return self.repo.update(role)
