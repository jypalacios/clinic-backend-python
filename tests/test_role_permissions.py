import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.permissions import permission_key_for_name
from app.core.deps import _has_permission
from app.models.permission import Permission
from app.models.role import Role
from app.services.role_service import RoleService


class RolePermissionTests(unittest.TestCase):
    def test_role_permissions_are_derived_from_the_permission_relationship(self):
        role = Role(
            permissions=[
                Permission(nom_permiso="users.view"),
                Permission(nom_permiso="PERMISO_DESCONOCIDO"),
            ]
        )

        self.assertNotIn("permisos", Role.__table__.columns)
        self.assertEqual(role.permisos, ["users.view"])

    def test_permission_names_resolve_to_authorization_keys(self):
        self.assertEqual(permission_key_for_name("users.manage"), "users.manage")
        self.assertEqual(permission_key_for_name("EDICION_USUARIOS"), "users.manage")
        self.assertEqual(permission_key_for_name("CREACION_PACIENTES"), "patients.manage")
        self.assertEqual(permission_key_for_name("patients.manage"), "patients.manage")
        self.assertEqual(permission_key_for_name("EDICION_PACIENTES"), "patients.edit")
        self.assertEqual(permission_key_for_name("ELIMINACION_PACIENTES"), "patients.delete")
        self.assertEqual(permission_key_for_name("VISUALIZACION_PACIENTES"), "patients.view")
        self.assertIsNone(permission_key_for_name("PERMISO_DESCONOCIDO"))

    def test_patient_create_permission_does_not_grant_edit_or_delete(self):
        self.assertFalse(_has_permission({"patients.manage"}, "patients.edit"))
        self.assertFalse(_has_permission({"patients.manage"}, "patients.delete"))
        self.assertTrue(_has_permission({"patients.edit"}, "patients.edit"))
        self.assertTrue(_has_permission({"patients.delete"}, "patients.delete"))

    def test_permission_output_uses_normalized_view_metadata(self):
        self.assertEqual(
            RoleService._permission_out(
                {
                    "id_permiso": 7,
                    "nom_permiso": "CREACION_PACIENTES",
                    "permiso_key": "patients.manage",
                    "etiqueta": "Registrar pacientes",
                    "nom_grupo": "Pacientes",
                    "activo": True,
                }
            ),
            {
                "id_permiso": 7,
                "nom_permiso": "CREACION_PACIENTES",
                "permiso_key": "patients.manage",
                "etiqueta": "Registrar pacientes",
                "nom_grupo": "Pacientes",
                "activo": True,
            },
        )

    def test_assignment_sync_updates_and_inserts_matrix_grants(self):
        db = Mock()
        service = RoleService.__new__(RoleService)
        service.repo = SimpleNamespace(
            db=db,
            get_role_assignments=Mock(return_value=[
                {"id_permiso": 10, "activo": True, "permiso_activo": True},
                {"id_permiso": 11, "activo": False, "permiso_activo": True},
                {"id_permiso": 12, "activo": True, "permiso_activo": False},
            ]),
        )

        service._synchronize_assignments(3, {11, 13}, updated_by=7)

        statements = [call.args[0].text for call in db.execute.call_args_list]
        self.assertEqual(
            sum("UPDATE matriz_permisos" in statement for statement in statements),
            3,
        )
        self.assertEqual(
            sum("INSERT INTO matriz_permisos" in statement for statement in statements),
            1,
        )


if __name__ == "__main__":
    unittest.main()
