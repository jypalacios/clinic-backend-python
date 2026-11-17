import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.api.v1.antecedents import create_item, router, update_item
from app.core.deps import _has_permission
from app.repositories.antecedent_repository import AntecedentRepository
from app.schemas.antecedent_schema import SubAntecedentInput
from app.services.antecedent_service import AntecedentNotFoundError, AntecedentService


class AntecedentTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.data = SubAntecedentInput(id_cli_antecedente=2, det_sub_antecedente="  Detalle  ", id_espect=3)

    def test_create_and_update_call_procedures_with_authenticated_user(self):
        service = AntecedentService(self.db)
        service.save(self.data, 12)
        statement, params = self.db.execute.call_args.args
        self.assertEqual(str(statement), "CALL public.sp_crear_cli_sub_antecedentes(:antecedent_id, :detail, :specialty_id, :user_id)")
        self.assertEqual(params, {"antecedent_id": 2, "detail": "Detalle", "specialty_id": 3, "user_id": 12})
        self.db.execute.reset_mock()
        self.db.execute.return_value.first.return_value = (1,)
        service.save(self.data, 12, 21)
        lock_statement, lock_params = self.db.execute.call_args_list[0].args
        self.assertIn("FOR UPDATE", str(lock_statement))
        self.assertEqual(lock_params, {"id": 21})
        statement, params = self.db.execute.call_args_list[1].args
        self.assertEqual(str(statement), "CALL public.sp_actualizar_cli_sub_antecedentes(:id, :antecedent_id, :detail, :specialty_id, :user_id)")
        self.assertEqual(params, {"id": 21, "antecedent_id": 2, "detail": "Detalle", "specialty_id": 3, "user_id": 12})
        self.assertEqual(self.db.commit.call_count, 2)

    def test_missing_update_is_not_reported_as_success(self):
        self.db.execute.return_value.first.return_value = None
        with self.assertRaises(AntecedentNotFoundError):
            AntecedentService(self.db).save(self.data, 12, 21)
        self.db.execute.assert_called_once()
        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_database_errors_roll_back(self):
        for state, expected in (("23503", ValueError), ("XX000", DBAPIError)):
            with self.subTest(state=state):
                db = Mock()
                original = Exception("database error")
                original.pgcode = state
                db.execute.side_effect = DBAPIError("CALL", {}, original)
                with self.assertRaises(expected):
                    AntecedentService(db).save(self.data, 12)
                db.rollback.assert_called_once()
                db.commit.assert_not_called()

    def test_catalog_queries_use_requested_objects(self):
        self.db.execute.return_value.mappings.return_value = []
        repo = AntecedentRepository(self.db)
        repo.list_antecedents()
        self.assertIn("public.v_cli_antecedentes", str(self.db.execute.call_args.args[0]))
        repo.list_specialties()
        self.assertIn("public.espect", str(self.db.execute.call_args.args[0]))
        repo.list_sub_antecedents()
        query = str(self.db.execute.call_args.args[0])
        for name in ("public.cli_sub_antecedentes", "public.v_cli_antecedentes", "public.espect"):
            self.assertIn(name, query)

    def test_validation_rejects_empty_detail_and_invalid_ids(self):
        for values in (
            {"id_cli_antecedente": 0, "det_sub_antecedente": "x", "id_espect": 1},
            {"id_cli_antecedente": 1, "det_sub_antecedente": "x", "id_espect": -1},
            {"id_cli_antecedente": 1, "det_sub_antecedente": "  ", "id_espect": 1},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                SubAntecedentInput(**values)

    def test_endpoints_use_user_and_translate_errors(self):
        user = SimpleNamespace(id=12)
        with patch("app.api.v1.antecedents.AntecedentService") as service_class:
            service = service_class.return_value
            create_item(self.data, self.db, user)
            service.save.assert_called_once_with(self.data, 12)
            service.save.reset_mock()
            update_item(self.data, 21, self.db, user)
            service.save.assert_called_once_with(self.data, 12, 21)
            service.save.side_effect = AntecedentNotFoundError("No existe")
            with self.assertRaises(HTTPException) as exc:
                update_item(self.data, 21, self.db, user)
            self.assertEqual(exc.exception.status_code, 404)
            service.save.side_effect = ValueError("Especialidad inexistente")
            with self.assertRaises(HTTPException) as exc:
                create_item(self.data, self.db, user)
            self.assertEqual(exc.exception.status_code, 400)

    def test_read_and_write_permissions_are_separate(self):
        viewer = SimpleNamespace(role=SimpleNamespace(permisos=["antecedents.view"]))
        manager = SimpleNamespace(role=SimpleNamespace(permisos=["antecedents.manage"]))
        no_access = SimpleNamespace(role=SimpleNamespace(permisos=[]))
        for route in router.routes:
            dependency = next(dep.call for dep in route.dependant.dependencies if getattr(dep.call, "__name__", "") == "dependency")
            dependency(manager)
            with self.assertRaises(HTTPException):
                dependency(no_access)
            if "GET" in route.methods:
                dependency(viewer)
            else:
                with self.assertRaises(HTTPException):
                    dependency(viewer)
        self.assertTrue(_has_permission({"antecedents.manage"}, "antecedents.view"))


if __name__ == "__main__":
    unittest.main()
