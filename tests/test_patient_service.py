import unittest
from datetime import date
from types import SimpleNamespace

from app.main import app as api_app
from app.schemas.patient_schema import PatientCreate
from app.services.patient_service import PatientService


class FakePatientRepository:
    def __init__(self, patient, duplicate=None):
        self.patient = patient
        self.duplicate = duplicate

    def get_by_id(self, patient_id):
        return self.patient if self.patient and self.patient.id_patients == patient_id else None

    def get_document(self, document_id):
        return SimpleNamespace(id_documents=document_id)

    def get_by_identification(self, document_id, identification):
        return self.duplicate

    def update(self, patient):
        return patient


def make_update_data(identification="12345"):
    return PatientCreate(
        ced_patients=identification,
        id_documents=1,
        nom_patients="Ana",
        ape_patients="Perez",
        fec_nacimiento=date(1990, 1, 31),
        id_sexo=2,
        telefono="3001234567",
        email="ana@example.com",
        direccion="Calle 1",
        eps="EPS",
        contacto_emergencia="Contacto",
    )


class PatientServiceTests(unittest.TestCase):
    def make_service(self, patient, duplicate=None):
        service = PatientService.__new__(PatientService)
        service.repo = FakePatientRepository(patient, duplicate)
        return service

    def test_update_changes_patient_fields_and_allows_its_existing_identification(self):
        patient = SimpleNamespace(id_patients=4)
        service = self.make_service(patient, duplicate=patient)

        result = service.update_patient(4, make_update_data())

        self.assertIs(result, patient)
        self.assertEqual(patient.nom_patients, "Ana")
        self.assertEqual(patient.ced_patients, "12345")
        self.assertEqual(patient.email, "ana@example.com")

    def test_update_rejects_identification_used_by_another_patient(self):
        patient = SimpleNamespace(id_patients=4)
        duplicate = SimpleNamespace(id_patients=5)
        service = self.make_service(patient, duplicate=duplicate)

        with self.assertRaisesRegex(ValueError, "ya existe"):
            service.update_patient(4, make_update_data())

    def test_update_returns_none_when_patient_does_not_exist(self):
        service = self.make_service(None)

        self.assertIsNone(service.update_patient(4, make_update_data()))

    def test_update_endpoint_is_registered(self):
        update_routes = [
            route for route in api_app.routes
            if getattr(route, "path", None) == "/api/v1/patients/{patient_id}"
        ]

        self.assertTrue(any("PUT" in route.methods for route in update_routes))


if __name__ == "__main__":
    unittest.main()
