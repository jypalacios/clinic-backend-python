import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.clinical_record_repository import ClinicalRecordRepository
from app.schemas.clinical_record_schema import ClinicalEntryCreate, ClinicalRecordCreate
from app.services.clinical_record_service import ClinicalRecordService


class ClinicalRecordAntecedentTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id=9)
        self.doctor = SimpleNamespace(id_doctors=2, id_espect=10, specialty=SimpleNamespace(nom_espect="Visual"))
        self.service = ClinicalRecordService(Mock())
        self.service.repo = Mock()
        self.service.repo.get_doctor_for_user.return_value = self.doctor
        self.service.repo.appointment_specialty.return_value = {
            "id_patients": 3, "id_espect": 10, "nom_estado": "PROGRAMADA",
        }
        self.service.repo.list_antecedent_types.return_value = [
            {"id_sub_antecedente": 4, "id_cli_antecedente": 5,
             "det_sub_antecedente": "Detalle", "det_cli_antecedente": "Grupo"},
        ]
        self.data = ClinicalEntryCreate(
            motivo_consulta="Consulta", id_appointment=7,
            antecedentes=[{"id_sub_antecedente": 4, "medida_cli_antecedente": " valor "}],
        )

    def test_catalog_uses_appointment_specialty_and_rejects_other_doctor(self):
        self.service.appointment_antecedents(7, self.user)
        self.service.repo.appointment_specialty.assert_called_once_with(7, 2)
        self.service.repo.list_antecedent_types.assert_called_once_with(10)
        self.service.repo.appointment_specialty.return_value = None
        with self.assertRaises(HTTPException) as exc:
            self.service.appointment_antecedents(7, self.user)
        self.assertEqual(exc.exception.status_code, 404)

    def test_rejects_wrong_patient_state_specialty_and_duplicates(self):
        for appointment in (
            None,
            {"id_patients": 8, "id_espect": 10, "nom_estado": "PROGRAMADA"},
            {"id_patients": 3, "id_espect": 10, "nom_estado": "ATENDIDA"},
        ):
            self.service.repo.appointment_specialty.return_value = appointment
            with self.subTest(appointment=appointment), self.assertRaises(ValueError):
                self.service._validate_antecedents(self.data, self.doctor, 3)
        self.service.repo.appointment_specialty.return_value = {
            "id_patients": 3, "id_espect": 10, "nom_estado": "PROGRAMADA",
        }
        for items in (
            [{"id_sub_antecedente": 99}],
            [{"id_sub_antecedente": 4}, {"id_sub_antecedente": 4}],
        ):
            with self.subTest(items=items), self.assertRaises(ValueError):
                self.service._validate_antecedents(
                    ClinicalEntryCreate(motivo_consulta="Consulta", id_appointment=7, antecedentes=items),
                    self.doctor, 3,
                )
        with self.assertRaises(ValueError):
            self.service._validate_antecedents(
                ClinicalEntryCreate(motivo_consulta="Consulta", antecedentes=[{"id_sub_antecedente": 4}]),
                self.doctor, 3,
            )

    def test_create_and_correction_attach_new_values_to_new_entry(self):
        repo = self.service.repo
        repo.get_patient.return_value = SimpleNamespace(activo=True)
        repo.doctor_has_patient_appointment.return_value = True
        self.service.db.scalars.return_value.one_or_none.return_value = None
        repo.insert_entry.return_value = 40
        repo.get_record.return_value = SimpleNamespace(activo=True, id_doctors=2, id_patients=3)
        self.service._serialize_record = Mock(return_value={})
        self.service._audit = Mock()
        with patch("app.services.clinical_record_service.ClinicalRecord") as record, \
             patch("app.services.clinical_record_service.select"):
            record.return_value.id_clinic = 12
            self.service.create_record(ClinicalRecordCreate(id_patients=3, **self.data.model_dump()), self.user)
        self.assertEqual(repo.assign_antecedents.call_args.args[0], 40)
        self.assertEqual(repo.assign_antecedents.call_args.args[1][0]["medida_cli_antecedente"], "valor")
        repo.get_entry.return_value = SimpleNamespace(id_clinics=12)
        repo.insert_entry.return_value = 41
        self.service.append_entry(12, self.data, 20, self.user)
        self.assertEqual(repo.insert_entry.call_args.args[2], 20)
        self.assertEqual(repo.assign_antecedents.call_args.args[0], 41)
        self.assertEqual(repo.commit.call_count, 2)

    def test_procedure_uses_new_entry_and_errors_roll_back(self):
        db = Mock()
        repo = ClinicalRecordRepository(db)
        repo.assign_antecedents(42, [{"id_cli_antecedente": 5, "id_sub_antecedente": 4,
                                     "medida_cli_antecedente": "valor"}], 9)
        statement, params = db.execute.call_args.args
        self.assertIn("sp_crear_cli_entries_antecedentes", str(statement))
        self.assertEqual(params, {"entry": 42, "antecedent": 5, "sub_antecedent": 4,
                                  "value": "valor", "checked": True, "user_id": 9})
        self.service.repo.get_record.return_value = SimpleNamespace(activo=True, id_doctors=2, id_patients=3)
        self.service.repo.assign_antecedents.side_effect = RuntimeError("error de base de datos")
        with self.assertRaisesRegex(RuntimeError, "base de datos"):
            self.service.append_entry(12, self.data, None, self.user)
        self.service.repo.rollback.assert_called_once()
        self.service.repo.commit.assert_not_called()

    def test_reads_antecedents_for_each_entry_including_unchecked(self):
        engine = create_engine("sqlite://")
        with Session(engine) as db:
            db.execute(text("CREATE TABLE cli_antecedentes (id_cli_antecedente integer, det_cli_antecedente text)"))
            db.execute(text("CREATE TABLE cli_sub_antecedentes (id_sub_antecedente integer, det_sub_antecedente text)"))
            db.execute(text(
                "CREATE TABLE cli_entries_antecedentes (id_entries integer, id_cli_entries_antecedente integer, "
                "id_cli_antecedente integer, id_sub_antecedente integer, medida_cli_antecedente text, checked boolean)"
            ))
            db.execute(text("INSERT INTO cli_antecedentes VALUES (5, 'Grupo ')"))
            db.execute(text("INSERT INTO cli_sub_antecedentes VALUES (4, 'Detalle ')"))
            db.execute(text(
                "INSERT INTO cli_entries_antecedentes VALUES (20, 1, 5, 4, 'Original', true), "
                "(21, 2, 5, 4, 'Actual', false)"
            ))
            adapter = Mock()
            def execute_sqlite(statement, params):
                query = str(statement).replace("public.", "").replace("e.id_entries = ANY(:ids)", "e.id_entries IN (20, 21)")
                self.assertEqual(params, {"ids": [20, 21]})
                return db.execute(text(query))
            adapter.execute.side_effect = execute_sqlite
            result = ClinicalRecordRepository(adapter).antecedents_by_entry([20, 21])
            self.assertEqual(result[20][0]["medida_cli_antecedente"], "Original")
            self.assertEqual(result[21][0]["checked"], 0)
            self.assertEqual(result[20][0]["det_cli_antecedente"], "Grupo")
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
