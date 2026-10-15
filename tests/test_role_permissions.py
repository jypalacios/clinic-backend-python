import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.permissions import permission_key_for_name
from app.services.role_service import RoleService


class RolePermissionTests(unittest.TestCase):
    def test_permission_names_resolve_to_authorization_keys(self):
        self.assertEqual(permission_key_for_name("users.manage"), "users.manage")
        self.assertEqual(permission_key_for_name("EDICION_USUARIOS"), "users.manage")
        self.assertEqual(permission_key_for_name("VISUALIZACION_PACIENTES"), "patients.view")
        self.assertIsNone(permission_key_for_name("PERMISO_DESCONOCIDO"))

    def test_assignment_sync_uses_procedures_and_revokes_inactive_grants(self):
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
            sum("sp_actualizar_matriz_permisos" in statement for statement in statements),
            3,
        )
        self.assertEqual(
            sum("sp_insertar_matriz_permiso(" in statement for statement in statements),
            1,
        )


if __name__ == "__main__":
    unittest.main()
