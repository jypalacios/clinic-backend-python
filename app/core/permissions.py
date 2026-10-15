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

LEGACY_PERMISSION_KEYS: dict[str, str] = {
    "CREACION_USUARIOS": "users.create",
    "EDICION_USUARIOS": "users.manage",
    "ELIMINACION_USUARIOS": "users.manage",
    "VISUALIZACION_USUARIOS": "users.view",
    "CREACION_PACIENTES": "patients.manage",
    "EDICION_PACIENTES": "patients.manage",
    "ELIMINACION_PACIENTES": "patients.manage",
    "VISUALIZACION_PACIENTES": "patients.view",
    "CREACION_DOCTORES": "doctors.manage",
    "EDICION_DOCTORES": "doctors.manage",
    "ELIMINACION_DOCTORES": "doctors.manage",
    "VISUALIZACION_DOCTORES": "doctors.view",
    "CREACION_CITAS": "appointments.manage",
    "EDICION_CITAS": "appointments.manage",
    "ELIMINACION_CITAS": "appointments.manage",
    "VISUALIZACION_CITAS": "appointments.view",
    "CREACION_HISTORIAS": "medical_history.manage",
    "EDICION_HISTORIAS": "medical_history.manage",
    "ELIMINACION_HISTORIAS": "medical_history.delete",
    "VISUALIZACION_HISTORIAS": "medical_history.view",
    "CREACION_PERMISOS": "roles.manage",
    "EDICION_PERMISOS": "roles.manage",
    "ELIMINACION_PERMISOS": "roles.manage",
    "VISUALIZACION_PERMISOS": "roles.manage",
    "CREACION_ROLES": "roles.manage",
    "EDICION_ROLES": "roles.manage",
    "ELIMINACION_ROLES": "roles.manage",
    "VISUALIZACION_ROLES": "roles.manage",
}

CANONICAL_PERMISSION_NAMES: dict[str, str] = {
    "users.view": "VISUALIZACION_USUARIOS",
    "users.create": "CREACION_USUARIOS",
    "users.manage": "EDICION_USUARIOS",
    "roles.manage": "CREACION_ROLES",
    "doctors.view": "VISUALIZACION_DOCTORES",
    "doctors.manage": "EDICION_DOCTORES",
    "specialties.view": "specialties.view",
    "specialties.manage": "specialties.manage",
    "patients.view": "VISUALIZACION_PACIENTES",
    "patients.manage": "EDICION_PACIENTES",
    "appointments.view": "VISUALIZACION_CITAS",
    "appointments.manage": "EDICION_CITAS",
    "audit.view": "audit.view",
    "my_patients.view": "my_patients.view",
    "medical_history.view": "VISUALIZACION_HISTORIAS",
    "medical_history.manage": "EDICION_HISTORIAS",
    "medical_history.delete": "ELIMINACION_HISTORIAS",
}


def permission_key_for_name(name: str) -> str | None:
    """Translate persisted legacy permission names to API authorization keys."""
    normalized = name.strip()
    if "." in normalized:
        return normalized.lower()
    return LEGACY_PERMISSION_KEYS.get(normalized.upper())
