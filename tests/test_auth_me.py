import unittest
from types import SimpleNamespace

from app.api.v1.auth import get_me


class AuthMeTests(unittest.TestCase):
    def test_returns_user_name_in_profile(self):
        user = SimpleNamespace(
            id=1,
            nombre="Ana",
            apellido="Pérez",
            usuario="ana",
            email="ana@example.com",
            role=SimpleNamespace(nom_role="ASISTENTE", permisos=["patients.view"]),
            id_role=2,
        )

        profile = get_me(user)

        self.assertEqual(profile["nombre"], "Ana")
        self.assertEqual(profile["apellido"], "Pérez")
        self.assertEqual(profile["usuario"], "ana")
