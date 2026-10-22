import unittest
from datetime import datetime, timezone

from app.models.appointment import Appointment
from app.models.state import State
from app.schemas.appointment_schema import AppointmentOut


class AppointmentSchemaTests(unittest.TestCase):
    def test_output_uses_nom_estado_for_orm_estado_attribute(self):
        self.assertIn("id_estado", Appointment.__table__.columns)
        self.assertNotIn("estado", Appointment.__table__.columns)

        appointment = Appointment(
            id_appointments=1,
            id_patients=2,
            id_doctors=3,
            fecha_hora=datetime(2030, 1, 1, tzinfo=timezone.utc),
            id_estado=4,
            fec_creacion=datetime(2029, 12, 1, tzinfo=timezone.utc),
        )
        appointment.state = State(nom_estado="PROGRAMADA")

        result = AppointmentOut.model_validate(appointment).model_dump()

        self.assertEqual(result["nom_estado"], "PROGRAMADA")
        self.assertNotIn("estado", result)


if __name__ == "__main__":
    unittest.main()
