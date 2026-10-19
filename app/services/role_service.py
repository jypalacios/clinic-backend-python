from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.permissions import permission_key_for_name
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.schemas.role_schema import (
    PermissionCreate,
    PermissionUpdate,
    RoleCreate,
    RoleUpdate,
)


class RoleService:
    def __init__(self, db: Session):
        self.repo = RoleRepository(db)

    def list_roles(self) -> list[dict]:
        return self.repo.list_all()

    def list_permissions(self) -> list[dict]:
        return [self._permission_out(permission) for permission in self.repo.get_permissions()]

    def create_role(self, data: RoleCreate, created_by: int, ip: str | None = None) -> dict:
        name = self._normalize_role_name(data.nom_role)
        if self.repo.get_by_name(name):
            raise ValueError("Ya existe un rol con ese nombre")

        permission_ids = self._validate_permission_ids(data.permisos)
        self.repo.db.execute(
            text(
                "CALL sp_insertar_role(CAST(NULL AS INTEGER), :name, :user_id, CAST(:ip AS INET))"
            ),
            {"name": name, "user_id": created_by, "ip": ip},
        )
        role = self.repo.get_by_name(name)
        if role is None:
            raise RuntimeError("El procedimiento no devolvió el rol recién creado")

        self._synchronize_assignments(role["id_role"], permission_ids, created_by)
        self.repo.db.commit()
        return self._role_out(role["id_role"])

    def update_role(
        self,
        role_id: int,
        data: RoleUpdate,
        updated_by: int,
        ip: str | None = None,
    ) -> dict:
        role = self.repo.get_by_id(role_id)
        if role is None:
            raise ValueError("Rol no encontrado")

        changes = data.model_dump(exclude_unset=True)
        name = role["nom_role"]
        if changes.get("nom_role") is not None:
            name = self._normalize_role_name(changes["nom_role"])
            existing = self.repo.get_by_name(name)
            if existing and existing["id_role"] != role_id:
                raise ValueError("Ya existe un rol con ese nombre")

        if changes.get("nom_role") is not None or (
            "permisos" in changes and changes["permisos"] is not None
        ):
            self.repo.db.execute(
                text(
                    "CALL sp_actualizar_role(:role_id, :name, :user_id, CAST(:ip AS INET))"
                ),
                {"role_id": role_id, "name": name, "user_id": updated_by, "ip": ip},
            )

        if "permisos" in changes and changes["permisos"] is not None:
            permission_ids = self._validate_permission_ids(changes["permisos"])
            self._ensure_another_role_manager_if_needed(role_id, permission_ids)
            self._synchronize_assignments(role_id, permission_ids, updated_by)

        self.repo.db.commit()
        return self._role_out(role_id)

    def create_permission(
        self,
        data: PermissionCreate,
        created_by: int,
    ) -> dict:
        name = data.nom_permiso.strip().upper()
        if self.repo.get_permission_by_name(name):
            raise ValueError("Ya existe un permiso con ese nombre")
        self.repo.db.execute(
            text(
                "CALL sp_insertar_permiso("
                "CAST(:name AS VARCHAR), :user_id, CAST(now() AS TIMESTAMP), "
                ":user_id, CAST(now() AS TIMESTAMP), TRUE)"
            ),
            {"name": name, "user_id": created_by},
        )
        permission = self.repo.get_permission_by_name(name)
        if permission is None:
            raise RuntimeError("El procedimiento no devolvió el permiso recién creado")
        self.repo.db.commit()
        return self._permission_out(permission)

    def update_permission(
        self,
        permission_id: int,
        data: PermissionUpdate,
        updated_by: int,
    ) -> dict:
        permission = self.repo.get_permission(permission_id)
        if permission is None:
            raise ValueError("Permiso no encontrado")

        changes = data.model_dump(exclude_unset=True)
        name = permission["nom_permiso"]
        if changes.get("nom_permiso") is not None:
            name = changes["nom_permiso"].strip().upper()
            existing = self.repo.get_permission_by_name(name)
            if existing and existing["id_permiso"] != permission_id:
                raise ValueError("Ya existe un permiso con ese nombre")
        active = changes.get("activo")
        if active is None:
            active = permission["activo"]
        if permission_key_for_name(permission["nom_permiso"]) == "roles.manage" and (
            not active or permission_key_for_name(name) != "roles.manage"
        ):
            self._ensure_manager_survives_permission_change(permission_id)

        if not active:
            for assignment in self.repo.get_permission_assignments(permission_id):
                if assignment["activo"]:
                    self._update_assignment(
                        permission_id,
                        assignment["id_role"],
                        updated_by,
                        active=False,
                    )

        self.repo.db.execute(
            text(
                "CALL sp_actualizar_permiso("
                ":permission_id, :name, :user_id, CAST(now() AS TIMESTAMP), :active)"
            ),
            {
                "permission_id": permission_id,
                "name": name,
                "user_id": updated_by,
                "active": active,
            },
        )
        self.repo.db.commit()
        updated = self.repo.get_permission(permission_id)
        if updated is None:
            raise RuntimeError("El permiso dejó de estar disponible después de actualizarlo")
        return self._permission_out(updated)

    def _role_out(self, role_id: int) -> dict:
        role = self.repo.get_by_id(role_id)
        if role is None:
            raise RuntimeError("El rol dejó de estar disponible después de actualizarlo")
        assignments = self.repo.get_role_assignments(role_id)
        return {
            "id_role": role["id_role"],
            "nom_role": role["nom_role"],
            "permisos": sorted(
                {
                    assignment["id_permiso"]
                    for assignment in assignments
                    if assignment["activo"] and assignment["permiso_activo"]
                }
            ),
        }

    @staticmethod
    def _permission_out(permission: dict) -> dict:
        return {
            "id_permiso": permission["id_permiso"],
            "nom_permiso": permission["nom_permiso"],
            "permiso_key": permission["permiso_key"],
            "etiqueta": permission["etiqueta"],
            "nom_grupo": permission["nom_grupo"],
            "activo": permission["activo"],
        }

    @staticmethod
    def _normalize_role_name(name: str) -> str:
        normalized = name.strip().upper()
        if len(normalized) < 2:
            raise ValueError("El nombre del rol debe tener al menos 2 caracteres")
        return normalized

    def _validate_permission_ids(self, permission_ids: list[int]) -> set[int]:
        requested_ids = set(permission_ids)
        active_ids = {
            permission["id_permiso"]
            for permission in self.repo.get_permissions(include_inactive=False)
        }
        unknown_ids = requested_ids - active_ids
        if unknown_ids:
            raise ValueError("Uno o más permisos no existen o están inactivos")
        return requested_ids

    def _synchronize_assignments(
        self,
        role_id: int,
        requested_ids: set[int],
        updated_by: int,
    ) -> None:
        existing = self.repo.get_role_assignments(role_id)
        active_ids = {
            assignment["id_permiso"]
            for assignment in existing
            if assignment["activo"] and assignment["permiso_activo"]
        }
        existing_by_permission = {
            assignment["id_permiso"]: assignment for assignment in existing
        }

        for assignment in existing:
            if assignment["activo"] and not assignment["permiso_activo"]:
                self._update_assignment(
                    assignment["id_permiso"],
                    role_id,
                    updated_by,
                    active=False,
                )

        for permission_id in active_ids - requested_ids:
            self._update_assignment(permission_id, role_id, updated_by, active=False)

        for permission_id in requested_ids - active_ids:
            if permission_id in existing_by_permission:
                self._update_assignment(permission_id, role_id, updated_by, active=True)
            else:
                self.repo.db.execute(
                    text(
                        "INSERT INTO matriz_permisos ("
                        "id_permiso, id_role, usu_creacion, fec_creacion, "
                        "usu_actualizacion, fec_actualizacion, activo"
                        ") VALUES ("
                        ":permission_id, :role_id, :user_id, now(), :user_id, now(), TRUE)"
                    ),
                    {
                        "permission_id": permission_id,
                        "role_id": role_id,
                        "user_id": updated_by,
                    },
                )

    def _update_assignment(
        self,
        permission_id: int,
        role_id: int,
        updated_by: int,
        active: bool,
    ) -> None:
        result = self.repo.db.execute(
            text(
                "UPDATE matriz_permisos "
                "SET usu_actualizacion = :user_id, fec_actualizacion = now(), activo = :active "
                "WHERE id_permiso = :permission_id AND id_role = :role_id"
            ),
            {
                "permission_id": permission_id,
                "role_id": role_id,
                "user_id": updated_by,
                "active": active,
            },
        )
        if result.rowcount == 0:
            raise RuntimeError(
                f"No existe la asignación del permiso {permission_id} al rol {role_id}"
            )

    def _ensure_another_role_manager_if_needed(
        self,
        role_id: int,
        requested_ids: set[int],
    ) -> None:
        requested_manager = {
            permission["id_permiso"]
            for permission in self.repo.get_permissions(include_inactive=False)
            if permission_key_for_name(permission["nom_permiso"]) == "roles.manage"
        }
        if not requested_manager.intersection(requested_ids):
            current_managers = {
                assignment["id_role"]
                for assignment in self.repo.db.execute(
                    text(
                        "SELECT id_role, nom_permiso FROM v_permisos_roles "
                        "WHERE activo IS TRUE AND permiso_activo IS TRUE"
                    )
                ).mappings()
                if permission_key_for_name(assignment["nom_permiso"]) == "roles.manage"
            }
            if role_id in current_managers:
                other_manager_roles = current_managers - {role_id}
                another_manager = (
                    self.repo.db.query(User.id)
                    .filter(User.id_role.in_(other_manager_roles), User.id_estado == 1)
                    .first()
                    if other_manager_roles
                    else None
                )
                active_user = self.repo.db.query(User.id).filter(
                    User.id_role == role_id,
                    User.id_estado == 1,
                ).first()
                if active_user and not another_manager:
                    raise ValueError(
                        "No se pueden retirar los permisos de roles al último administrador activo"
                    )

    def _ensure_manager_survives_permission_change(self, permission_id: int) -> None:
        active_manager_assignments = [
            assignment
            for assignment in self.repo.db.execute(
                text(
                    "SELECT id_role, id_permiso, nom_permiso FROM v_permisos_roles "
                    "WHERE activo IS TRUE AND permiso_activo IS TRUE"
                )
            ).mappings()
            if permission_key_for_name(assignment["nom_permiso"]) == "roles.manage"
        ]
        current_manager_roles = {
            assignment["id_role"] for assignment in active_manager_assignments
        }
        remaining_manager_roles = {
            assignment["id_role"]
            for assignment in active_manager_assignments
            if assignment["id_permiso"] != permission_id
        }
        roles_losing_management = current_manager_roles - remaining_manager_roles
        if not roles_losing_management:
            return

        active_users_losing_management = self.repo.db.query(User.id).filter(
            User.id_role.in_(roles_losing_management),
            User.id_estado == 1,
        ).first()
        active_users_retaining_management = (
            self.repo.db.query(User.id)
            .filter(User.id_role.in_(remaining_manager_roles), User.id_estado == 1)
            .first()
            if remaining_manager_roles
            else None
        )
        if active_users_losing_management and not active_users_retaining_management:
            raise ValueError(
                "No se puede desactivar el último permiso de administración de roles en uso"
            )
