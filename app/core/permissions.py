from typing import Literal

Permission = Literal[
    "users.view",
    "users.create",
    "users.manage",
    "roles.manage",
    "doctors.view",
    "doctors.manage",
    "doctors.link_user",
    "specialties.view",
    "specialties.manage",
    "patients.view",
    "patients.manage",
    "appointments.view",
    "appointments.manage",
    "audit.view",
    "my_patients.view",
    "medical_history.view",
    "medical_history.manage",
    "medical_history.delete",
]

ALL_PERMISSIONS: tuple[str, ...] = (
    "users.view",
    "users.create",
    "users.manage",
    "roles.manage",
    "doctors.view",
    "doctors.manage",
    "doctors.link_user",
    "specialties.view",
    "specialties.manage",
    "patients.view",
    "patients.manage",
    "appointments.view",
    "appointments.manage",
    "audit.view",
    "my_patients.view",
    "medical_history.view",
    "medical_history.manage",
    "medical_history.delete",
)

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "ADMINISTRADOR": list(ALL_PERMISSIONS),
    "ASISTENTE": [
        "users.view",
        "users.create",
        "doctors.view",
        "doctors.manage",
        "specialties.view",
        "specialties.manage",
        "patients.view",
        "patients.manage",
        "appointments.view",
        "appointments.manage",
    ],
    "MEDICO": [
        "my_patients.view",
        "medical_history.view",
        "medical_history.manage",
    ],
}
