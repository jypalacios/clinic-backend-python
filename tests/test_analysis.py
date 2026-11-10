import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.api.v1.analysis import create_assignment, router, update_assignment
from app.core.deps import _has_permission
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis_schema import AnalysisAssignment
from app.services.analysis_service import AnalysisNotFoundError, AnalysisService


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.service = AnalysisService(self.db)
        self.data = AnalysisAssignment(id_tipo_appointment=3, id_hc_detalle=8)

    def test_create_calls_procedure_in_order_with_authenticated_user(self):
        self.service.save(self.data, user_id=12)
        statement, params = self.db.execute.call_args.args
        self.assertEqual(str(statement), "CALL sp_crear_cli_hc_appointment(:type_id, :detail_id, :user_id)")
        self.assertEqual(params, {"type_id": 3, "detail_id": 8, "user_id": 12})
        self.db.commit.assert_called_once()

    def test_update_calls_procedure_in_declared_order(self):
        self.service.save(self.data, user_id=12, assignment_id=21)
        statement, params = self.db.execute.call_args.args
        self.assertEqual(str(statement), "CALL sp_actualizar_cli_hc_appointment(:id, :detail_id, :type_id, :user_id)")
        self.assertEqual(params, {"id": 21, "type_id": 3, "detail_id": 8, "user_id": 12})
        self.db.commit.assert_called_once()

    def test_database_errors_roll_back_and_are_translated(self):
        for state, expected in (("23503", ValueError), ("P0002", AnalysisNotFoundError), ("XX000", DBAPIError)):
            with self.subTest(state=state):
                db = Mock()
                original = Exception("database error")
                original.pgcode = state
                db.execute.side_effect = DBAPIError("CALL", {}, original)
                with self.assertRaises(expected):
                    AnalysisService(db).save(self.data, 12, 21)
                db.rollback.assert_called_once()
                db.commit.assert_not_called()

    def test_assignments_are_filtered_by_selected_type(self):
        db = Mock()
        db.execute.return_value.mappings.return_value = []
        self.assertEqual(AnalysisRepository(db).list_assignments(3), [])
        statement, params = db.execute.call_args.args
        self.assertIn("FROM v_cli_hc_appointment", str(statement))
        self.assertIn("WHERE id_tipo_appointment = :type_id", str(statement))
        self.assertEqual(params, {"type_id": 3})

    def test_invalid_identifiers_are_rejected(self):
        for values in (
            {"id_tipo_appointment": 0, "id_hc_detalle": 1},
            {"id_tipo_appointment": 1, "id_hc_detalle": -1},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                AnalysisAssignment(**values)

    def test_routes_use_authenticated_user_and_translate_errors(self):
        user = SimpleNamespace(id=12)
        with patch("app.api.v1.analysis.AnalysisService") as service_class:
            service = service_class.return_value
            create_assignment(self.data, self.db, user)
            service.save.assert_called_once_with(self.data, 12)
            service.save.reset_mock()
            update_assignment(21, self.data, self.db, user)
            service.save.assert_called_once_with(self.data, 12, 21)
            service.save.side_effect = AnalysisNotFoundError("La asociación no existe.")
            with self.assertRaises(HTTPException) as exc:
                update_assignment(21, self.data, self.db, user)
            self.assertEqual(exc.exception.status_code, 404)
            service.save.side_effect = ValueError("Detalle inexistente")
            with self.assertRaises(HTTPException) as exc:
                create_assignment(self.data, self.db, user)
            self.assertEqual(exc.exception.status_code, 400)

    def test_details_reuse_existing_catalog(self):
        with patch("app.services.analysis_service.ClinicalRecordRepository") as repository:
            repository.return_value.list_measure_types.return_value = [
                {"id_hc_detalle": 8, "id_hc_general": 2, "detalle": "Detalle", "general": "General"},
            ]
            self.assertEqual(self.service.list_details()[0]["id_hc_detalle"], 8)
            repository.assert_called_once_with(self.db)

    def test_route_permissions_enforce_read_and_write_separately(self):
        view_user = SimpleNamespace(role=SimpleNamespace(permisos=["analysis.view"]))
        manage_user = SimpleNamespace(role=SimpleNamespace(permisos=["analysis.manage"]))
        no_user = SimpleNamespace(role=SimpleNamespace(permisos=[]))
        for route in router.routes:
            permission_dependency = next(
                dep.call for dep in route.dependant.dependencies
                if getattr(dep.call, "__name__", "") == "dependency"
            )
            permission_dependency(manage_user)
            with self.assertRaises(HTTPException) as exc:
                permission_dependency(no_user)
            self.assertEqual(exc.exception.status_code, 403)
            if "GET" in route.methods:
                permission_dependency(view_user)
            else:
                with self.assertRaises(HTTPException):
                    permission_dependency(view_user)
        self.assertTrue(_has_permission({"analysis.manage"}, "analysis.view"))


if __name__ == "__main__":
    unittest.main()
