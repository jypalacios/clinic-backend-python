from sqlalchemy import text
from sqlalchemy.orm import Session


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[dict]:
        roles = list(
            self.db.execute(
                text("SELECT id_role, nom_role FROM v_roles ORDER BY id_role")
            ).mappings()
        )
        assignments = self.db.execute(
            text(
                "SELECT id_role, id_permiso FROM v_permisos_roles "
                "WHERE activo IS TRUE AND permiso_activo IS TRUE ORDER BY id_permiso"
            )
        ).mappings()
        permissions_by_role: dict[int, list[int]] = {}
        for assignment in assignments:
            permissions_by_role.setdefault(assignment["id_role"], []).append(
                assignment["id_permiso"]
            )
        return [
            {
                "id_role": role["id_role"],
                "nom_role": role["nom_role"],
                "permisos": permissions_by_role.get(role["id_role"], []),
            }
            for role in roles
        ]

    def get_by_id(self, role_id: int) -> dict | None:
        return self.db.execute(
            text("SELECT id_role, nom_role FROM v_roles WHERE id_role = :role_id"),
            {"role_id": role_id},
        ).mappings().first()

    def get_by_name(self, name: str) -> dict | None:
        return self.db.execute(
            text("SELECT id_role, nom_role FROM v_roles WHERE lower(nom_role) = lower(:name)"),
            {"name": name},
        ).mappings().first()

    def get_permissions(self, include_inactive: bool = True) -> list[dict]:
        where_clause = "" if include_inactive else "WHERE activo IS TRUE"
        return list(
            self.db.execute(
                text(
                    "SELECT id_permiso, nom_permiso, activo FROM v_permisos "
                    f"{where_clause} ORDER BY id_permiso"
                )
            ).mappings()
        )

    def get_permission(self, permission_id: int) -> dict | None:
        return self.db.execute(
            text(
                "SELECT id_permiso, nom_permiso, activo FROM v_permisos "
                "WHERE id_permiso = :permission_id"
            ),
            {"permission_id": permission_id},
        ).mappings().first()

    def get_permission_by_name(self, name: str) -> dict | None:
        return self.db.execute(
            text(
                "SELECT id_permiso, nom_permiso, activo FROM v_permisos "
                "WHERE lower(nom_permiso) = lower(:name)"
            ),
            {"name": name},
        ).mappings().first()

    def get_role_assignments(self, role_id: int) -> list[dict]:
        return list(
            self.db.execute(
                text(
                    "SELECT id_permiso, activo, permiso_activo FROM v_permisos_roles "
                    "WHERE id_role = :role_id"
                ),
                {"role_id": role_id},
            ).mappings()
        )

    def get_permission_assignments(self, permission_id: int) -> list[dict]:
        return list(
            self.db.execute(
                text(
                    "SELECT id_role, id_permiso, activo, permiso_activo "
                    "FROM v_permisos_roles WHERE id_permiso = :permission_id"
                ),
                {"permission_id": permission_id},
            ).mappings()
        )
