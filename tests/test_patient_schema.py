import unittest
from datetime import date

from app.schemas.patient_schema import PatientOut


def patient_payload(activo):
    return {
        "id_patients": 1,
        "ced_patients": "123",
        "id_documents": 1,
        "document": {
            "id_documents": 1,
            "desc_tipo": "CC",
            "desc_documents": "Cédula",
        },
        "nom_patients": "Ana",
        "ape_patients": "Perez",
        "fec_nacimiento": date(1990, 1, 1),
        "edad": 36,
        "id_sexo": 2,
        "nom_sexo": "Femenino",
        "activo": activo,
    }


class PatientOutTests(unittest.TestCase):
    def test_boolean_database_state_maps_to_requested_numeric_state(self):
        self.assertEqual(PatientOut.model_validate(patient_payload(True)).activo, 0)
        self.assertEqual(PatientOut.model_validate(patient_payload(False)).activo, 1)

    def test_numeric_state_is_preserved(self):
        self.assertEqual(PatientOut.model_validate(patient_payload(0)).activo, 0)
        self.assertEqual(PatientOut.model_validate(patient_payload(1)).activo, 1)

    def test_other_numeric_state_is_rejected(self):
        with self.assertRaises(ValueError):
            PatientOut.model_validate(patient_payload(2))


if __name__ == "__main__":
    unittest.main()
