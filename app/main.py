import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.core.permissions import (
    CANONICAL_PERMISSION_NAMES,
    DEFAULT_ROLE_PERMISSIONS,
    permission_key_for_name,
)
from app.db.session import engine
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.clinical_record import ClinicalEntry, ClinicalRecord
from app.models.document import Document
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.models.sexo import Sexo
from app.models.specialty import Specialty
from app.models.user import User
from app.api.v1 import appointments, auth, clinical_records, doctors, documents, health, patients, roles, sexos, specialties, users

settings = get_settings()
USER_CREATION_PERMISSION_MIGRATION = "20261005_assistant_user_creation"
CLINICAL_HISTORY_MIGRATION = "20261005_clinical_history_access"
PATIENT_DOCUMENTS_MIGRATION = "20261008_patient_documents"
PATIENT_AGE_MIGRATION = "20261009_patient_age"
ROLE_PERMISSION_MATRIX_MIGRATION = "20261014_role_permission_matrix"

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

        permission_columns = {
            column["name"] for column in inspect(conn).get_columns("permisos")
        }
        if "activo" not in permission_columns:
            conn.execute(
                text("ALTER TABLE permisos ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE")
            )
        else:
            conn.execute(text("UPDATE permisos SET activo = TRUE WHERE activo IS NULL"))
            conn.execute(
                text(
                    "ALTER TABLE permisos ALTER COLUMN activo SET DEFAULT TRUE, "
                    "ALTER COLUMN activo SET NOT NULL"
                )
            )

        matrix_columns = {
            column["name"] for column in inspect(conn).get_columns("matriz_permisos")
        }
        if "activo" not in matrix_columns:
            conn.execute(
                text("ALTER TABLE matriz_permisos ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE")
            )
        else:
            conn.execute(
                text("UPDATE matriz_permisos SET activo = TRUE WHERE activo IS NULL")
            )
            conn.execute(
                text(
                    "ALTER TABLE matriz_permisos ALTER COLUMN activo SET DEFAULT TRUE, "
                    "ALTER COLUMN activo SET NOT NULL"
                )
            )

        conn.execute(
            text(
                "CREATE OR REPLACE VIEW v_permisos AS "
                "SELECT id_permiso, nom_permiso, activo FROM permisos"
            )
        )
        conn.execute(
            text(
                "CREATE OR REPLACE VIEW v_permisos_roles AS "
                "SELECT mp.id_permiso, p.nom_permiso, mp.id_role, r.nom_role, "
                "mp.activo, p.activo AS permiso_activo "
                "FROM matriz_permisos mp "
                "JOIN permisos p ON p.id_permiso = mp.id_permiso "
                "JOIN roles r ON r.id_role = mp.id_role"
            )
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

        role_permission_matrix_applied = conn.execute(
            text("SELECT 1 FROM app_schema_migrations WHERE version = :version"),
            {"version": ROLE_PERMISSION_MATRIX_MIGRATION},
        ).first()
        if not role_permission_matrix_applied:
            role_columns = {
                column["name"] for column in inspect(conn).get_columns("roles")
            }
            if "permisos" in role_columns:
                role_permissions = conn.execute(
                    text("SELECT id_role, permisos FROM roles")
                ).mappings()
                stored_permissions = conn.execute(
                    text("SELECT id_permiso, nom_permiso, activo FROM permisos")
                ).mappings().all()
                for role in role_permissions:
                    for permission_name in role["permisos"] or []:
                        permission_key = permission_key_for_name(permission_name)
                        if permission_key is None:
                            continue
                        matching_permissions = [
                            permission["id_permiso"]
                            for permission in stored_permissions
                            if permission["activo"]
                            and permission_key_for_name(permission["nom_permiso"])
                            == permission_key
                        ]
                        if not matching_permissions:
                            permission_name = CANONICAL_PERMISSION_NAMES.get(
                                permission_key, permission_key
                            )
                            permission_id = conn.execute(
                                text(
                                    "INSERT INTO permisos (nom_permiso) VALUES (:name) "
                                    "ON CONFLICT (nom_permiso) DO UPDATE "
                                    "SET nom_permiso = EXCLUDED.nom_permiso "
                                    "RETURNING id_permiso"
                                ),
                                {"name": permission_name},
                            ).scalar_one()
                            matching_permissions = [permission_id]
                            stored_permissions = [
                                *stored_permissions,
                                {
                                    "id_permiso": permission_id,
                                    "nom_permiso": permission_name,
                                    "activo": True,
                                },
                            ]
                        for permission_id in matching_permissions:
                            conn.execute(
                                text(
                                    "INSERT INTO matriz_permisos (id_role, id_permiso) "
                                    "VALUES (:role_id, :permission_id) "
                                    "ON CONFLICT (id_role, id_permiso) DO NOTHING"
                                ),
                                {
                                    "role_id": role["id_role"],
                                    "permission_id": permission_id,
                                },
                            )
            conn.execute(
                text("INSERT INTO app_schema_migrations (version) VALUES (:version)"),
                {"version": ROLE_PERMISSION_MATRIX_MIGRATION},
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

        patient_age_applied = conn.execute(
            text("SELECT 1 FROM app_schema_migrations WHERE version = :version"),
            {"version": PATIENT_AGE_MIGRATION},
        ).first()
        if not patient_age_applied:
            patient_columns = {
                column["name"] for column in inspect(conn).get_columns("patients")
            }
            if "edad" not in patient_columns:
                conn.execute(text("ALTER TABLE patients ADD COLUMN edad INTEGER"))

            conn.execute(
                text(
                    "UPDATE patients "
                    "SET edad = EXTRACT( "
                    "YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, "
                    "fec_nacimiento) "
                    ")::INTEGER "
                    "WHERE edad IS DISTINCT FROM EXTRACT( "
                    "YEAR FROM age((CURRENT_TIMESTAMP AT TIME ZONE 'America/Bogota')::DATE, "
                    "fec_nacimiento) "
                    ")::INTEGER"
                )
            )
            conn.execute(text("ALTER TABLE patients ALTER COLUMN edad SET NOT NULL"))
            conn.execute(
                text("INSERT INTO app_schema_migrations (version) VALUES (:version)"),
                {"version": PATIENT_AGE_MIGRATION},
            )
