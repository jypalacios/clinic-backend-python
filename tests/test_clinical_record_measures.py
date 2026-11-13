import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from pydantic import ValidationError

from app.api.v1.clinical_records import get_measure_config, list_measure_types
from app.repositories.clinical_record_repository import ClinicalRecordRepository
from app.schemas.clinical_record_schema import ClinicalEntryCreate, ClinicalRecordCreate, ClinicalRecordOut
from app.services.clinical_record_service import ClinicalRecordService


class ClinicalRecordMeasureTests(unittest.TestCase):
    def test_catalog_filters_specialty_without_changing_admin_catalog(self):
        engine = create_engine("sqlite://")
        with Session(engine) as db:
            db.execute(text("CREATE TABLE cli_hc_general (id_hcgeneral integer, det_hcgeneral text, id_espect integer)"))
            db.execute(text("CREATE TABLE cli_hc_detalle (id_hc_detalle integer, id_hc_general integer, det_hc_general text)"))
            db.execute(text("INSERT INTO cli_hc_general VALUES (1, 'Visual', 10), (2, 'Otro', 20)"))
            db.execute(text("INSERT INTO cli_hc_detalle VALUES (11, 1, 'Detalle A'), (22, 2, 'Detalle B')"))
            repo = ClinicalRecordRepository(db)
            self.assertEqual([item["id_hc_detalle"] for item in repo.list_measure_types(10)], [11])
            self.assertEqual([item["id_hc_detalle"] for item in repo.list_measure_types(20)], [22])
            self.assertEqual(repo.list_measure_types(30), [])
            self.assertEqual(len(repo.list_measure_types()), 2)
        engine.dispose()

    def test_endpoint_uses_authenticated_doctor_specialty(self):
        user = SimpleNamespace(id=1)
        with patch("app.api.v1.clinical_records.ClinicalRecordService") as service:
            list_measure_types(Mock(), user)
            service.return_value.list_measure_types.assert_called_once_with(user)
        clinical = ClinicalRecordService(Mock())
        clinical.repo = Mock()
        clinical.repo.get_doctor_for_user.return_value = SimpleNamespace(id_espect=10)
        clinical.list_measure_types(user)
        clinical.repo.list_measure_types.assert_called_once_with(10)

    def test_measures_use_specialty_view_and_deduplicate_diagnoses(self):
        engine = create_engine("sqlite://")
        with Session(engine) as db:
            db.execute(text(
                "CREATE TABLE v_clinical_entries_espect (id_entries integer, id_hc_medida integer, "
                "id_hc_detalle integer, detalle_medida text, det_hcgeneral text, derecho text, izquierdo text, "
                "det_derecho text, det_izquierdo text, detalle text)"
            ))
            db.execute(text(
                "INSERT INTO v_clinical_entries_espect VALUES "
                "(1, 7, 11, 'Detalle ', 'Visual ', '1 ', NULL, 'OD ', 'OI ', 'Adicional '), "
                "(1, 7, 11, 'Detalle ', 'Visual ', '1 ', NULL, 'OD ', 'OI ', 'Adicional '), "
                "(2, 8, 22, 'Otro', 'Otro', '2', NULL, NULL, NULL, NULL)"
            ))

            def execute_sqlite(statement, params):
                query = str(statement).replace("id_entries = ANY(:ids)", "id_entries = :entry_id")
                return db.execute(text(query), {"entry_id": params["ids"][0]})

            adapter = Mock()
            adapter.execute.side_effect = execute_sqlite
            result = ClinicalRecordRepository(adapter).measures_by_entry([1])
            self.assertEqual(result, {1: [{
                "id_hc_medida": 7, "id_hc_detalle": 11, "general": "Visual",
                "detalle_medida": "Detalle", "derecho": "1", "izquierdo": None,
                "det_derecho": "OD", "det_izquierdo": "OI", "detalle": "Adicional",
            }]})
        engine.dispose()

    def test_entry_view_includes_notes_without_measures_and_deduplicates(self):
        engine = create_engine("sqlite://")
        with Session(engine) as db:
            db.execute(text(
                "CREATE TABLE v_clinical_entries (id_entries integer, id_clinics integer, id_doctors integer, "
                "id_entries_rectifica integer, fec_entrada text, motivo_consulta text, examen_fisico text, "
                "diagnostico_texto text, plan text, formulacion text, notas text, peso real, talle real, "
                "medico text, nom_espect text, codigo text, id_hc_medida integer)"
            ))
            db.execute(text(
                "INSERT INTO v_clinical_entries VALUES "
                "(1, 2, 3, NULL, '2026-01-01', 'Consulta', NULL, 'Texto libre', NULL, NULL, NULL, "
                "NULL, NULL, 'Médico', 'Especialidad ', 'A', 1), "
                "(1, 2, 3, NULL, '2026-01-01', 'Consulta', NULL, 'Texto libre', NULL, NULL, NULL, "
                "NULL, NULL, 'Médico', 'Especialidad ', 'B', 2), "
                "(2, 2, 3, NULL, '2026-01-02', 'Sin medidas', NULL, NULL, NULL, NULL, NULL, "
                "NULL, NULL, 'Médico', 'Especialidad ', NULL, NULL)"
            ))

            def execute_sqlite(statement, params):
                query = str(statement).replace("id_entries = ANY(:ids)", "id_entries IN (1, 2)")
                self.assertEqual(params, {"ids": [1, 2]})
                return db.execute(text(query))

            adapter = Mock()
            adapter.execute.side_effect = execute_sqlite
            result = ClinicalRecordRepository(adapter).entries_by_id([1, 2])
            self.assertEqual(len(result), 2)
            self.assertEqual(result[1]["diagnostico"], "Texto libre")
            self.assertEqual(result[2]["motivo_consulta"], "Sin medidas")
            self.assertEqual(result[2]["nom_espect"], "Especialidad")
        engine.dispose()

    def test_serialization_uses_views_and_preserves_notes_without_measures(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        entry_data = {
            "id_entries": 1, "id_clinics": 2, "id_doctors": 3, "id_entries_rectifica": None,
            "fec_entrada": datetime(2026, 1, 1), "motivo_consulta": "Consulta",
            "examen_fisico": None, "diagnostico": "Texto libre", "plan": None, "formulacion": None,
            "notas": None, "peso": None, "talle": None, "medico": "Médico", "nom_espect": "Visual",
        }
        service.repo.entries_by_id.return_value = {1: entry_data}
        service.repo.diagnoses_by_entry.return_value = {}
        service.repo.measures_by_entry.return_value = {}
        patient = SimpleNamespace(id_patients=4, ced_patients="123", nom_patients="A", ape_patients="B",
                                  edad=30, sexo=SimpleNamespace(nom_sexo="F"))
        doctor = SimpleNamespace(id_doctors=3, nom_doctors="C", ape_doctors="D")
        record = SimpleNamespace(id_clinic=2, id_patients=4, patient=patient, id_doctors=3, doctor=doctor,
                                 fec_creacion=datetime(2026, 1, 1), activo=True,
                                 entries=[SimpleNamespace(id_entries=1)])
        output = ClinicalRecordOut.model_validate(service._serialize_record(record, include_entries=True))
        self.assertEqual(output.entries[0].diagnostico, "Texto libre")
        self.assertEqual(output.entries[0].nom_espect, "Visual")
        self.assertEqual(output.entries[0].medidas, [])
        service.repo.entries_by_id.assert_called_once_with([1])
        service.repo.entries_by_id.return_value = {}
        with self.assertRaisesRegex(RuntimeError, "v_clinical_entries"):
            service._serialize_record(record, include_entries=True)

    def test_rejects_other_specialty_on_create_and_append(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        doctor = SimpleNamespace(id_doctors=2, id_espect=10, specialty=SimpleNamespace(nom_espect="Oftalmología"))
        service.repo.get_doctor_for_user.return_value = doctor
        service.repo.get_patient.return_value = SimpleNamespace(activo=True)
        service.repo.doctor_has_patient_appointment.return_value = True
        service.db.scalars.return_value.one_or_none.return_value = None
        service.repo.get_record.return_value = SimpleNamespace(activo=True, id_doctors=2)
        service.repo.list_measure_types.return_value = [{"id_hc_detalle": 11}]
        user = SimpleNamespace(id=1)
        values = {"motivo_consulta": "Consulta", "medidas": [{"id_hc_detalle": 22, "derecho": "1"}]}
        with self.assertRaisesRegex(ValueError, "especialidad"):
            service.create_record(ClinicalRecordCreate(id_patients=3, **values), user)
        with self.assertRaisesRegex(ValueError, "especialidad"):
            service.append_entry(1, ClinicalEntryCreate(**values), None, user)
        service.repo.insert_entry.assert_not_called()
        service.repo.list_measure_types.assert_called_with(10)

    def test_accepts_matching_and_empty_measures(self):
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        service.repo.list_measure_types.return_value = [{"id_hc_detalle": 11}]
        doctor = SimpleNamespace(id_espect=10, specialty=SimpleNamespace(nom_espect="Oftalmología"))
        service._validate_measures(ClinicalEntryCreate(motivo_consulta="Consulta"), doctor)
        service.repo.list_measure_types.assert_not_called()
        service._validate_measures(
            ClinicalEntryCreate(motivo_consulta="Consulta", medidas=[{"id_hc_detalle": 11, "izquierdo": "2"}]),
            doctor,
        )
        service.repo.list_measure_types.assert_called_once_with(10)

    def test_neurology_config_and_validation(self):
        user = SimpleNamespace(id=1)
        doctor = SimpleNamespace(id_espect=10, specialty=SimpleNamespace(nom_espect="  NEUROLOGÍA  "))
        service = ClinicalRecordService(Mock())
        service.repo = Mock()
        service.repo.get_doctor_for_user.return_value = doctor
        service.repo.list_measure_types.return_value = [{"id_hc_detalle": 11}]
        self.assertEqual(service.measure_config(user)["mode"], "detalle")
        with patch("app.api.v1.clinical_records.ClinicalRecordService") as service_class:
            get_measure_config(Mock(), user)
            service_class.return_value.measure_config.assert_called_once_with(user)
        service._validate_measures(
            ClinicalEntryCreate(motivo_consulta="Consulta", medidas=[{"id_hc_detalle": 11, "detalle": "Hallazgo"}]),
            doctor,
        )
        with self.assertRaisesRegex(ValueError, "neurología"):
            service._validate_measures(
                ClinicalEntryCreate(motivo_consulta="Consulta", medidas=[{"id_hc_detalle": 11, "derecho": "1"}]),
                doctor,
            )
        doctor.specialty.nom_espect = "Oftalmología"
        self.assertEqual(service.measure_config(user)["mode"], "ojos")
        with self.assertRaises(ValidationError):
            ClinicalEntryCreate(motivo_consulta="Consulta", medidas=[{"id_hc_detalle": 11, "detalle": "x" * 256}])

    def test_insert_passes_detail_to_procedure_and_additional_measures(self):
        db = Mock()
        db.execute.return_value.scalar_one.return_value = 19
        repo = ClinicalRecordRepository(db)
        data = {"motivo_consulta": "Consulta", "medidas": [
            {"id_hc_detalle": 1, "detalle": "Primer hallazgo"},
            {"id_hc_detalle": 2, "detalle": "Segundo hallazgo"},
            {"id_hc_detalle": 3},
        ]}
        self.assertEqual(repo.insert_entry(2, 3, 5, data, 4), 19)
        self.assertEqual(db.execute.call_count, 2)
        statement, first = db.execute.call_args_list[0].args
        self.assertIn(":rectifica, NULL::text, NULL::text, :detalle)", str(statement))
        self.assertEqual((first["detalle_id"], first["detalle"], first["derecho"], first["izquierdo"]),
                         (1, "Primer hallazgo", None, None))
        self.assertEqual(first["rectifica"], 5)
        statement, extra = db.execute.call_args_list[1].args
        self.assertIn("id_entries, detalle", str(statement))
        self.assertEqual(extra, {"detalle_id": 2, "detalle": "Segundo hallazgo", "derecho": None,
                                 "izquierdo": None, "entry": 19})

    def test_ocular_measures_continue_to_use_the_procedure(self):
        db = Mock()
        db.execute.return_value.scalar_one.return_value = 19
        ClinicalRecordRepository(db).insert_entry(
            2, 3, None,
            {"motivo_consulta": "Consulta", "medidas": [{"id_hc_detalle": 11, "derecho": "20/20"}]},
            4,
        )
        params = db.execute.call_args.args[1]
        self.assertEqual((params["detalle_id"], params["derecho"], params["detalle"]), (11, "20/20", None))


if __name__ == "__main__":
    unittest.main()
