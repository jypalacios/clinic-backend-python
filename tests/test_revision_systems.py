import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.api.v1.revision_systems import create_revision_system, list_revision_systems, router
from app.repositories.revision_system_repository import RevisionSystemRepository
from app.schemas.revision_system_schema import RevisionSystemCreate
from app.services.revision_system_service import RevisionSystemService


class RevisionSystemTests(unittest.TestCase):
    def test_create_calls_procedure_with_authenticated_user(self):
        db = Mock()
        RevisionSystemService(db).create("Sensación ojo seco", 12)
        statement, params = db.execute.call_args.args
        self.assertEqual(
            str(statement),
            "CALL public.sp_crear_cli_revision_sistemas(:detail, :user_id)",
        )
        self.assertEqual(params, {"detail": "Sensación ojo seco", "user_id": 12})
        db.commit.assert_called_once()

    def test_database_errors_roll_back(self):
        db = Mock()
        original = Exception("database error")
        original.pgcode = "23503"
        db.execute.side_effect = DBAPIError("CALL", {}, original)
        with self.assertRaisesRegex(ValueError, "usuario de creación"):
            RevisionSystemService(db).create("Detalle", 12)
        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_list_reads_view_columns(self):
        db = Mock()
        db.execute.return_value.mappings.return_value = []
        self.assertEqual(RevisionSystemRepository(db).list_all(), [])
        statement = str(db.execute.call_args.args[0])
        self.assertIn("public.v_cli_revision_sistemas", statement)
        for column in (
            "id_revision_sistema",
            "det_revision_sistemas",
            "usuario_creacion",
            "usuario_modificacion",
        ):
            self.assertIn(column, statement)

    def test_description_is_trimmed_and_validated(self):
        self.assertEqual(
            RevisionSystemCreate(det_revision_sistemas="  Dolor lumbar  ").det_revision_sistemas,
            "Dolor lumbar",
        )
        for description in ("  ", "x" * 256):
            with self.subTest(description=description), self.assertRaises(ValidationError):
                RevisionSystemCreate(det_revision_sistemas=description)

    def test_endpoint_passes_current_user_and_translates_validation_errors(self):
        user = SimpleNamespace(id=12)
        data = RevisionSystemCreate(det_revision_sistemas="Dolor lumbar")
        with patch("app.api.v1.revision_systems.RevisionSystemService") as service_class:
            service = service_class.return_value
            create_revision_system(data, Mock(), user)
            service.create.assert_called_once_with("Dolor lumbar", 12)
            service.create.side_effect = ValueError("Usuario inexistente")
            with self.assertRaises(HTTPException) as exc:
                create_revision_system(data, Mock(), user)
            self.assertEqual(exc.exception.status_code, 400)
            service_class.reset_mock()
            service_class.return_value.list_all.return_value = []
            self.assertEqual(list_revision_systems(Mock(), user), [])

    def test_read_and_manage_permissions_are_separate(self):
        viewer = SimpleNamespace(role=SimpleNamespace(permisos=["revision_systems.view"]))
        manager = SimpleNamespace(role=SimpleNamespace(permisos=["revision_systems.manage"]))
        no_access = SimpleNamespace(role=SimpleNamespace(permisos=[]))
        for route in router.routes:
            dependency = next(
                dep.call
                for dep in route.dependant.dependencies
                if getattr(dep.call, "__name__", "") == "dependency"
            )
            dependency(manager)
            with self.assertRaises(HTTPException):
                dependency(no_access)
            if "GET" in route.methods:
                dependency(viewer)
            else:
                with self.assertRaises(HTTPException):
                    dependency(viewer)


if __name__ == "__main__":
    unittest.main()
