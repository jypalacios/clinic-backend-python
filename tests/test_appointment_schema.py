import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.models.appointment import Appointment
from app.models.doctor import Doctor as _Doctor
from app.models.patient import Patient as _Patient
from app.models.sexo import Sexo as _Sexo
from app.models.specialty import Specialty as _Specialty
from app.models.state import State
from app.schemas.appointment_schema import AppointmentCreate, AppointmentOut


class AppointmentSchemaTests(unittest.TestCase):
    def test_output_uses_nom_estado_for_orm_estado_attribute(self):
        self.assertIn("id_estado", Appointment.__table__.columns)
        self.assertNotIn("estado", Appointment.__table__.columns)
        self.assertIn("tipo_appointment", Appointment.__table__.columns)

        appointment = Appointment(
            id_appointments=1,
            id_patients=2,
            id_doctors=3,
            tipo_appointment=5,
            fecha_hora=datetime(2030, 1, 1, tzinfo=timezone.utc),
            id_estado=4,
            fec_creacion=datetime(2029, 12, 1, tzinfo=timezone.utc),
        )
        appointment.state = State(nom_estado="PROGRAMADA")

        result = AppointmentOut.model_validate(appointment).model_dump()

        self.assertEqual(result["nom_estado"], "PROGRAMADA")
        self.assertEqual(result["tipo_appointment"], 5)
        self.assertNotIn("estado", result)

    def test_create_requires_positive_appointment_type(self):
        appointment_data = {
            "id_patients": 2,
            "id_doctors": 3,
            "fecha_hora": datetime(2030, 1, 1, tzinfo=timezone.utc),
        }
        with self.assertRaises(ValidationError):
            AppointmentCreate.model_validate(appointment_data)

        with self.assertRaises(ValidationError):
            AppointmentCreate.model_validate({**appointment_data, "tipo_appointment": 0})

        result = AppointmentCreate.model_validate({**appointment_data, "tipo_appointment": 5})
        self.assertEqual(result.tipo_appointment, 5)


if __name__ == "__main__":
    unittest.main()
