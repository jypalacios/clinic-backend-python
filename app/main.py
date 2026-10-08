import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.session import engine
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.clinical_record import ClinicalEntry, ClinicalRecord
from app.models.document import Document
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.role import Role
from app.models.sexo import Sexo
from app.models.specialty import Specialty
from app.models.user import User
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.api.v1 import appointments, auth, clinical_records, doctors, documents, health, patients, roles, sexos, specialties, users

settings = get_settings()
USER_CREATION_PERMISSION_MIGRATION = "20261005_assistant_user_creation"
CLINICAL_HISTORY_MIGRATION = "20261005_clinical_history_access"
PATIENT_DOCUMENTS_MIGRATION = "20261008_patient_documents"

app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["users"])
app.include_router(roles.router, prefix=settings.API_V1_PREFIX, tags=["roles"])
app.include_router(patients.router, prefix=settings.API_V1_PREFIX, tags=["patients"])
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(sexos.router, prefix=settings.API_V1_PREFIX)
app.include_router(specialties.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctors.router, prefix=settings.API_V1_PREFIX, tags=["doctors"])
app.include_router(appointments.router, prefix=settings.API_V1_PREFIX, tags=["appointments"])
app.include_router(clinical_records.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def verificar_conexion_bd() -> None:
    """Falla rápido si la BD no está disponible al iniciar el contenedor."""
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
        role_columns = {column["name"] for column in inspect(conn).get_columns("roles")}
        if "permisos" not in role_columns:
            conn.execute(
                text("ALTER TABLE roles ADD COLUMN permisos JSONB NOT NULL DEFAULT '[]'::jsonb")
            )
            for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
                conn.execute(
                    text(
                        "UPDATE roles SET permisos = CAST(:permissions AS JSONB) "
                        "WHERE upper(trim(nom_role)) = :role_name"
                    ),
                    {"permissions": json.dumps(permissions), "role_name": role_name},
                )

        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS app_schema_migrations "
                "(version VARCHAR(100) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        )
        migration_applied = conn.execute(
            text("SELECT 1 FROM app_schema_migrations WHERE version = :version"),
            {"version": USER_CREATION_PERMISSION_MIGRATION},
        ).first()
        if not migration_applied:
            assistant_roles = conn.execute(
                text(
                    "SELECT id_role, permisos FROM roles "
                    "WHERE upper(trim(nom_role)) = 'ASISTENTE' FOR UPDATE"
                )
            ).mappings()
            for assistant in assistant_roles:
                permissions = set(assistant["permisos"] or [])
                permissions.update(("users.view", "users.create"))
                conn.execute(
                    text("UPDATE roles SET permisos = CAST(:permissions AS JSONB) WHERE id_role = :role_id"),
                    {
                        "permissions": json.dumps(sorted(permissions)),
                        "role_id": assistant["id_role"],
                    },
                )
            conn.execute(
                text("INSERT INTO app_schema_migrations (version) VALUES (:version)"),
                {"version": USER_CREATION_PERMISSION_MIGRATION},
            )

        clinical_columns = {
            column["name"] for column in inspect(conn).get_columns("clinical_records")
        }
        if "activo" not in clinical_columns:
            conn.execute(
                text("ALTER TABLE clinical_records ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE")
            )
        entry_columns = {
            column["name"] for column in inspect(conn).get_columns("clinical_entries")
        }
        if "id_entries_rectifica" not in entry_columns:
            conn.execute(
                text(
                    "ALTER TABLE clinical_entries ADD COLUMN id_entries_rectifica BIGINT "
                    "REFERENCES clinical_entries(id_entries)"
                )
            )

        clinical_permissions_applied = conn.execute(
            text("SELECT 1 FROM app_schema_migrations WHERE version = :version"),
            {"version": CLINICAL_HISTORY_MIGRATION},
        ).first()
        if not clinical_permissions_applied:
            role_permissions = {
                "ADMINISTRADOR": ["doctors.link_user", "medical_history.delete"],
                "MEDICO": ["medical_history.view", "medical_history.manage"],
            }
            for role_name, permissions in role_permissions.items():
                roles = conn.execute(
                    text("SELECT id_role, permisos FROM roles WHERE upper(trim(nom_role)) = :role_name FOR UPDATE"),
                    {"role_name": role_name},
                ).mappings()
                for role in roles:
                    granted = set(role["permisos"] or [])
                    granted.update(permissions)
                    conn.execute(
                        text("UPDATE roles SET permisos = CAST(:permissions AS JSONB) WHERE id_role = :role_id"),
                        {"permissions": json.dumps(sorted(granted)), "role_id": role["id_role"]},
                    )
            conn.execute(
                text("INSERT INTO app_schema_migrations (version) VALUES (:version)"),
                {"version": CLINICAL_HISTORY_MIGRATION},
            )

        patient_documents_applied = conn.execute(
            text("SELECT 1 FROM app_schema_migrations WHERE version = :version"),
            {"version": PATIENT_DOCUMENTS_MIGRATION},
        ).first()
        if not patient_documents_applied:
            patient_columns = {
                column["name"] for column in inspect(conn).get_columns("patients")
            }
            if "id_documents" not in patient_columns:
                conn.execute(text("ALTER TABLE patients ADD COLUMN id_documents BIGINT"))

            default_document_id = conn.execute(
                text("SELECT id_documents FROM v_documents WHERE desc_tipo = 'CC'")
            ).scalar_one_or_none()
            if default_document_id is None:
                raise RuntimeError("El catálogo v_documents no contiene el tipo de documento CC")

            conn.execute(
                text(
                    "UPDATE patients SET id_documents = :document_id "
                    "WHERE id_documents IS NULL"
                ),
                {"document_id": default_document_id},
            )
            conn.execute(text("ALTER TABLE patients ALTER COLUMN id_documents SET NOT NULL"))

            unique_constraints = inspect(conn).get_unique_constraints("patients")
            for constraint in unique_constraints:
                if constraint.get("column_names") == ["ced_patients"]:
                    quoted_name = conn.dialect.identifier_preparer.quote(constraint["name"])
                    conn.exec_driver_sql(
                        f"ALTER TABLE patients DROP CONSTRAINT {quoted_name}"
                    )

            foreign_keys = inspect(conn).get_foreign_keys("patients")
            has_document_foreign_key = any(
                foreign_key.get("constrained_columns") == ["id_documents"]
                and foreign_key.get("referred_table") == "documents"
                for foreign_key in foreign_keys
            )
            if not has_document_foreign_key:
                conn.execute(
                    text(
                        "ALTER TABLE patients ADD CONSTRAINT fk_patients_documents "
                        "FOREIGN KEY (id_documents) REFERENCES documents(id_documents)"
                    )
                )

            unique_constraints = inspect(conn).get_unique_constraints("patients")
            has_composite_unique = any(
                constraint.get("column_names") == ["id_documents", "ced_patients"]
                for constraint in unique_constraints
            )
            if not has_composite_unique:
                conn.execute(
                    text(
                        "ALTER TABLE patients ADD CONSTRAINT uq_patients_document_identification "
                        "UNIQUE (id_documents, ced_patients)"
                    )
                )

            conn.execute(
                text("INSERT INTO app_schema_migrations (version) VALUES (:version)"),
                {"version": PATIENT_DOCUMENTS_MIGRATION},
            )
