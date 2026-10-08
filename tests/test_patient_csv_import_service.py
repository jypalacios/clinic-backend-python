import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError
from app.main import app as api_app
from app.repositories.patient_repository import PatientRepository
from app.services.patient_csv_import_service import MAX_CSV_BYTES, MAX_CSV_ROWS, PatientCSVImportService


class FakePatientRepository:
    def __init__(self, existing: set[tuple[int, str]] | None = None):
        self.existing = existing or set()
        self.imported = None
        self.imported_by = None
        self.sexos = [
            SimpleNamespace(id_sexo=1, nom_sexo="Masculino"),
            SimpleNamespace(id_sexo=2, nom_sexo="Femenino"),
        ]
        self.documents = [
            SimpleNamespace(
                id_documents=1,
                desc_tipo="CC",
                desc_documents="Cédula de ciudadanía",
            ),
            SimpleNamespace(
                id_documents=2,
                desc_tipo="CE",
                desc_documents="Cédula de extranjería",
            ),
        ]

    def list_sexos(self):
        return self.sexos

    def list_documents(self):
        return self.documents

    def existing_identifications(self, identifications: set[tuple[int, str]]):
        return self.existing.intersection(identifications)

    def import_many(self, patients, user_id: int):
        self.imported = patients
        self.imported_by = user_id
        return len(patients)


def make_service(existing: set[tuple[int, str]] | None = None) -> PatientCSVImportService:
    service = PatientCSVImportService.__new__(PatientCSVImportService)
    service.repo = FakePatientRepository(existing)
    return service


class PatientCSVImportServiceTests(unittest.TestCase):
    header = "tipo_documento,cedula,nombres,apellidos,fecha_nacimiento,sexo,telefono,email,direccion,eps,contacto_emergencia"
    valid_row = "CC,12345,Ana,Perez,1990-01-31,Femenino,,,,,"

    def test_import_endpoints_are_registered(self):
        paths = {route.path for route in api_app.routes if hasattr(route, "path")}

        self.assertIn("/api/v1/patients/import/preview", paths)
        self.assertIn("/api/v1/patients/import", paths)
        self.assertIn("/api/v1/documents/", paths)

    def test_preview_accepts_utf8_bom_and_validates_against_catalog(self):
        service = make_service()
        result = service.preview("patients.csv", f"\ufeff{self.header}\r\n{self.valid_row}".encode("utf-8"))

        self.assertEqual(result.total_rows, 1)
        self.assertEqual(result.valid_rows, 1)
        self.assertEqual(result.invalid_rows, 0)
        self.assertTrue(result.can_import)
        self.assertEqual(result.preview_rows[0].patient.id_sexo, 2)
        self.assertEqual(result.preview_rows[0].patient.id_documents, 1)

    def test_preview_accepts_semicolon_delimiter(self):
        service = make_service()
        header = self.header.replace(",", ";")
        row = self.valid_row.replace(",", ";")

        result = service.preview("patients.csv", f"{header}\n{row}".encode())

        self.assertTrue(result.can_import)

    def test_preview_accepts_document_description_and_same_number_for_other_type(self):
        service = make_service()
        row = self.valid_row.replace("CC", "Cédula de ciudadanía")
        other_type = self.valid_row.replace("CC,12345", "CE,12345")

        result = service.preview("patients.csv", f"{self.header}\n{row}\n{other_type}".encode())

        self.assertTrue(result.can_import)
        self.assertEqual(
            [preview.patient.id_documents for preview in result.preview_rows],
            [1, 2],
        )

    def test_preview_reports_bad_fields_and_existing_identification(self):
        service = make_service({(1, "12345")})
        row = "CC,12345,Ana,Perez,not-a-date,Desconocido,,,,,"

        result = service.preview("patients.csv", f"{self.header}\n{row}".encode())

        self.assertFalse(result.can_import)
        self.assertEqual(result.invalid_rows, 1)
        self.assertEqual(result.errors[0].row_number, 2)
        self.assertTrue(any("Sexo no reconocido" in message for message in result.errors[0].messages))
        self.assertTrue(any("ya está registrada" in message for message in result.errors[0].messages))
        self.assertTrue(any("Fecha de nacimiento" in message for message in result.errors[0].messages))

    def test_preview_marks_both_rows_when_same_document_identification_repeats_in_file(self):
        service = make_service()

        result = service.preview(
            "patients.csv",
            f"{self.header}\n{self.valid_row}\n{self.valid_row.replace('Ana', 'Eva')}".encode(),
        )

        self.assertEqual(result.invalid_rows, 2)
        self.assertEqual({error.row_number for error in result.errors}, {2, 3})
        self.assertFalse(result.can_import)

    def test_preview_rejects_unknown_document_type(self):
        service = make_service()
        row = self.valid_row.replace("CC,", "XX,")

        result = service.preview("patients.csv", f"{self.header}\n{row}".encode())

        self.assertFalse(result.can_import)
        self.assertTrue(any("Tipo de documento no reconocido" in message for message in result.errors[0].messages))

    def test_invalid_file_is_not_imported(self):
        service = make_service()
        user = SimpleNamespace(id=7)

        with self.assertRaisesRegex(ValueError, "no se importó ningún paciente"):
            service.import_file(
                "patients.csv",
                f"{self.header}\n{self.valid_row}\n{self.valid_row}".encode(),
                user,
            )

        self.assertIsNone(service.repo.imported)

    def test_valid_file_is_imported_as_a_single_batch_with_audit_user(self):
        service = make_service()
        user = SimpleNamespace(id=7)

        imported = service.import_file("patients.csv", f"{self.header}\n{self.valid_row}".encode(), user)

        self.assertEqual(imported, 1)
        self.assertEqual(service.repo.imported_by, 7)
        self.assertEqual(service.repo.imported[0].ced_patients, "12345")
        self.assertEqual(service.repo.imported[0].id_documents, 1)

    def test_repository_commits_import_and_audit_together(self):
        db = MagicMock()
        repository = PatientRepository(db)

        imported = repository.import_many([object(), object()], user_id=7)

        self.assertEqual(imported, 2)
        db.add_all.assert_called_once()
        db.flush.assert_called_once()
        db.commit.assert_called_once()
        audit = db.add.call_args.args[0]
        self.assertEqual(audit.accion, "IMPORT_PATIENTS_CSV")
        self.assertEqual(audit.detalle, {"imported_rows": 2, "source": "CSV"})

    def test_repository_rolls_back_on_duplicate_race(self):
        db = MagicMock()
        diagnostic = SimpleNamespace(constraint_name="uq_patients_document_identification")
        error = IntegrityError("INSERT", {}, SimpleNamespace(diag=diagnostic))
        db.flush.side_effect = error
        repository = PatientRepository(db)

        with self.assertRaisesRegex(ValueError, "No se importó ningún paciente"):
            repository.import_many([object()], user_id=7)

        db.rollback.assert_called_once()
        db.commit.assert_not_called()

    def test_patient_create_rolls_back_on_duplicate_race(self):
        db = MagicMock()
        diagnostic = SimpleNamespace(constraint_name="uq_patients_document_identification")
        db.commit.side_effect = IntegrityError("INSERT", {}, SimpleNamespace(diag=diagnostic))
        repository = PatientRepository(db)

        with self.assertRaisesRegex(ValueError, "ya existe para este tipo"):
            repository.create(object())

        db.rollback.assert_called_once()

    def test_document_catalog_is_loaded_from_v_documents(self):
        db = MagicMock()
        db.scalars.return_value.all.return_value = []
        repository = PatientRepository(db)

        self.assertEqual(repository.list_documents(), [])
        self.assertIn("v_documents", str(db.scalars.call_args.args[0]))

    def test_rejects_unknown_headers_and_non_csv_files(self):
        service = make_service()
        with self.assertRaisesRegex(ValueError, "Encabezados CSV inválidos"):
            service.preview("patients.csv", b"cedula,nombres\n12345,Ana")
        with self.assertRaisesRegex(ValueError, r"\.csv"):
            service.preview("patients.txt", f"{self.header}\n{self.valid_row}".encode())

    def test_rejects_non_utf8_and_oversized_files(self):
        service = make_service()
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            service.preview("patients.csv", b"\xff")
        with self.assertRaisesRegex(ValueError, "5 MB"):
            service.preview("patients.csv", b"x" * (MAX_CSV_BYTES + 1))

    def test_enforces_maximum_data_row_count(self):
        service = make_service()
        content = f"{self.header}\n" + f"{self.valid_row}\n" * (MAX_CSV_ROWS + 1)

        with self.assertRaisesRegex(ValueError, "5000 filas"):
            service.preview("patients.csv", content.encode())


if __name__ == "__main__":
    unittest.main()
