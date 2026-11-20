import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.clinical_records import list_revision_system_types, router
from app.repositories.clinical_record_repository import ClinicalRecordRepository
from app.schemas.clinical_record_schema import ClinicalEntryCreate, ClinicalRevisionSystemIn
from app.services.clinical_record_service import ClinicalRecordService


class ClinicalRecordRevisionSystemTests(unittest.TestCase):
    def test_revision_system_input_requires_positive_id_and_limited_measure(self):
        for values in (
            {"id_revision_sistema": 0, "checked": True},
            {"id_revision_sistema": 1, "checked": True, "medida_revision": "x" * 256},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                ClinicalRevisionSystemIn(**values)

    def test_catalog_uses_revision_system_view(self):
        db = Mock()
        db.execute.return_value.mappings.return_value = [
            {"id_revision_sistema": 1, "det_revision_sistemas": "Fiebre"},
        ]
        result = ClinicalRecordRepository(db).list_revision_system_types()
        self.assertEqual(result[0]["det_revision_sistemas"], "Fiebre")
        self.assertIn("public.v_cli_revision_sistemas", str(db.execute.call_args.args[0]))

    def test_existing_revisions_are_read_from_entries_view(self):
        db = Mock()
        db.execute.return_value.mappings.return_value = [
            {
                "id_entries": 20,
                "id_revision_sistema": 1,
                "det_revision_sistemas": "Fiebre",
                "checked": True,
                "medida_revision": "Leve",
            },
            {
                "id_entries": 21,
                "id_revision_sistema": 1,
                "det_revision_sistemas": "Fiebre",
                "checked": False,
                "medida_revision": "",
            },
        ]
        result = ClinicalRecordRepository(db).revision_systems_by_entry([20, 21])
        self.assertTrue(result[20][0]["checked"])
        self.assertFalse(result[21][0]["checked"])
        self.assertIn("public.v_cli_entries_revision", str(db.execute.call_args.args[0]))

    def test_empty_entry_ids_skip_database_query(self):
        db = Mock()
        self.assertEqual(ClinicalRecordRepository(db).revision_systems_by_entry([]), {})
        db.execute.assert_not_called()

    def test_create_procedure_receives_checked_and_unchecked_values(self):
        db = Mock()
        repo = ClinicalRecordRepository(db)
        repo.assign_revision_systems(42, [
            {"id_revision_sistema": 1, "checked": True, "medida_revision": "Leve"},
            {"id_revision_sistema": 2, "checked": False, "medida_revision": ""},
        ], 9)
        self.assertEqual(db.execute.call_count, 2)
        statement, params = db.execute.call_args_list[0].args
        self.assertIn("sp_crear_cli_entries_revision", str(statement))
        self.assertEqual(params, {
            "entry": 42,
            "revision_system": 1,
            "checked": True,
            "value": "Leve",
            "user_id": 9,
        })
        self.assertFalse(db.execute.call_args_list[1].args[1]["checked"])

    def test_revision_values_are_validated_and_unchecked_text_is_cleared(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        service.repo.list_revision_system_types.return_value = [
            {"id_revision_sistema": 1},
            {"id_revision_sistema": 2},
        ]
        data = ClinicalEntryCreate(
            motivo_consulta="Consulta",
            revision_sistemas=[
                {"id_revision_sistema": 1, "checked": True, "medida_revision": " Leve "},
                {"id_revision_sistema": 2, "checked": False, "medida_revision": "Ignorar"},
            ],
        )
        self.assertEqual(service._validate_revision_systems(data), [
            {"id_revision_sistema": 1, "checked": True, "medida_revision": "Leve"},
            {"id_revision_sistema": 2, "checked": False, "medida_revision": ""},
        ])
        for items in (
            [
                {"id_revision_sistema": 1, "checked": True},
                {"id_revision_sistema": 1, "checked": False},
            ],
            [{"id_revision_sistema": 99, "checked": True}],
        ):
            with self.subTest(items=items), self.assertRaises(ValueError):
                service._validate_revision_systems(
                    ClinicalEntryCreate(motivo_consulta="Consulta", revision_sistemas=items)
                )

    def test_rectification_creates_revision_rows_on_the_new_entry(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        service.repo.get_doctor_for_user.return_value = SimpleNamespace(id_doctors=4)
        service.repo.get_record.return_value = SimpleNamespace(
            id_doctors=4, id_patients=5, activo=True,
        )
        service.repo.get_entry.return_value = SimpleNamespace(id_clinics=3)
        service.repo.insert_entry.return_value = 42
        service.repo.list_revision_system_types.return_value = [
            {"id_revision_sistema": 1, "det_revision_sistemas": "Fiebre"},
        ]
        service._audit = Mock()
        service._serialize_record = Mock(return_value={})
        data = ClinicalEntryCreate(
            motivo_consulta="Consulta",
            revision_sistemas=[
                {"id_revision_sistema": 1, "checked": True, "medida_revision": "Leve"},
            ],
        )

        service.append_entry(3, data, 20, SimpleNamespace(id=9))

        self.assertEqual(service.repo.insert_entry.call_args.args[2], 20)
        service.repo.assign_revision_systems.assert_called_once_with(42, [
            {"id_revision_sistema": 1, "checked": True, "medida_revision": "Leve"},
        ], 9)

    def test_revision_rows_for_each_entry_are_serialized(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        entry_data = {
            "id_entries": 20,
            "id_clinics": 3,
            "id_doctors": 4,
            "id_entries_rectifica": None,
            "fec_entrada": "2026-01-01T00:00:00",
            "motivo_consulta": "Consulta",
            "examen_fisico": None,
            "diagnostico": None,
            "plan": None,
            "formulacion": None,
            "notas": None,
            "peso": None,
            "talle": None,
            "medico": "Médico",
            "nom_espect": "Visual",
        }
        service.repo.entries_by_id.return_value = {20: entry_data}
        service.repo.diagnoses_by_entry.return_value = {}
        service.repo.measures_by_entry.return_value = {}
        service.repo.antecedents_by_entry.return_value = {}
        service.repo.revision_systems_by_entry.return_value = {
            20: [{
                "id_revision_sistema": 1,
                "det_revision_sistemas": "Fiebre",
                "checked": True,
                "medida_revision": "Leve",
            }],
        }
        patient = SimpleNamespace(
            id_patients=5,
            ced_patients="123",
            nom_patients="Paciente",
            ape_patients="Prueba",
            edad=30,
            sexo=SimpleNamespace(nom_sexo="F"),
        )
        doctor = SimpleNamespace(id_doctors=4, nom_doctors="Doctor", ape_doctors="Prueba")
        record = SimpleNamespace(
            id_clinic=3,
            id_patients=5,
            patient=patient,
            id_doctors=4,
            doctor=doctor,
            fec_creacion="2026-01-01T00:00:00",
            activo=True,
            entries=[SimpleNamespace(id_entries=20)],
        )
        result = service._serialize_record(record, include_entries=True)
        self.assertEqual(result["entries"][0]["revision_sistemas"][0]["medida_revision"], "Leve")

    def test_catalog_endpoint_uses_service(self):
        with patch("app.api.v1.clinical_records.ClinicalRecordService") as service_class:
            service_class.return_value.list_revision_system_types.return_value = [
                {"id_revision_sistema": 1, "det_revision_sistemas": "Fiebre"},
            ]
            self.assertEqual(list_revision_system_types(Mock(), SimpleNamespace(id=9))[0]["id_revision_sistema"], 1)

    def test_catalog_route_requires_clinical_write_access(self):
        route = next(route for route in router.routes if route.path.endswith("/revision-sistemas"))
        dependency = next(
            dep.call
            for dep in route.dependant.dependencies
            if getattr(dep.call, "__name__", "") == "dependency"
        )
        doctor = SimpleNamespace(role=SimpleNamespace(permisos=["consultations.create"]))
        no_access = SimpleNamespace(role=SimpleNamespace(permisos=[]))
        self.assertIs(dependency(doctor), doctor)
        with self.assertRaises(HTTPException):
            dependency(no_access)


if __name__ == "__main__":
    unittest.main()
