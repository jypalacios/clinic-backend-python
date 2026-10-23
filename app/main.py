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
from app.models.permission import Permission, RolePermission
from app.models.role import Role
from app.models.sexo import Sexo
from app.models.specialty import Specialty
from app.models.user import User
from app.api.v1 import allergies, appointments, auth, clinical_records, doctors, documents, health, patients, roles, sexos, specialties, users

settings = get_settings()
PATIENT_DOCUMENTS_MIGRATION = "20261008_patient_documents"
PATIENT_AGE_MIGRATION = "20261009_patient_age"

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
app.include_router(allergies.types_router, prefix=settings.API_V1_PREFIX)
app.include_router(allergies.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def verificar_conexion_bd() -> None:
    """Falla rápido si la BD no está disponible al iniciar el contenedor."""
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))

        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS app_schema_migrations "
                "(version VARCHAR(100) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
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

        conn.execute(text("DROP VIEW IF EXISTS v_permisos"))
        conn.execute(
            text(
                "CREATE VIEW v_permisos AS "
                "WITH normalized_permissions AS ("
                "SELECT p.id_permiso, p.nom_permiso, p.usu_creacion, p.fec_creacion, "
                "p.usu_actualizacion, p.fec_actualizacion, p.activo, "
                "CASE upper(trim(p.nom_permiso)) "
                "WHEN 'VISUALIZACION_USUARIOS' THEN 'users.view' "
                "WHEN 'CREACION_USUARIOS' THEN 'users.create' "
                "WHEN 'EDICION_USUARIOS' THEN 'users.manage' "
                "WHEN 'ELIMINACION_USUARIOS' THEN 'users.manage' "
                "WHEN 'VISUALIZACION_ROLES' THEN 'roles.manage' "
                "WHEN 'CREACION_ROLES' THEN 'roles.manage' "
                "WHEN 'EDICION_ROLES' THEN 'roles.manage' "
                "WHEN 'ELIMINACION_ROLES' THEN 'roles.manage' "
                "WHEN 'VISUALIZACION_PERMISOS' THEN 'roles.manage' "
                "WHEN 'CREACION_PERMISOS' THEN 'roles.manage' "
                "WHEN 'EDICION_PERMISOS' THEN 'roles.manage' "
                "WHEN 'ELIMINACION_PERMISOS' THEN 'roles.manage' "
                "WHEN 'VISUALIZACION_DOCTORES' THEN 'doctors.view' "
                "WHEN 'CREACION_DOCTORES' THEN 'doctors.manage' "
                "WHEN 'EDICION_DOCTORES' THEN 'doctors.manage' "
                "WHEN 'ELIMINACION_DOCTORES' THEN 'doctors.manage' "
                "WHEN 'EDICION_PROFESIONALES' THEN 'doctors.manage' "
                "WHEN 'VISUALIZACION_PACIENTES' THEN 'patients.view' "
                "WHEN 'CREACION_PACIENTES' THEN 'patients.manage' "
                "WHEN 'EDICION_PACIENTES' THEN 'patients.edit' "
                "WHEN 'ELIMINACION_PACIENTES' THEN 'patients.delete' "
                "WHEN 'VISUALIZACION_CITAS' THEN 'appointments.view' "
                "WHEN 'CREACION_CITAS' THEN 'appointments.manage' "
                "WHEN 'EDICION_CITAS' THEN 'appointments.manage' "
                "WHEN 'ELIMINACION_CITAS' THEN 'appointments.manage' "
                "WHEN 'VISUALIZACION_HISTORIAS' THEN 'medical_history.view' "
                "WHEN 'CREACION_HISTORIAS' THEN 'medical_history.manage' "
                "WHEN 'EDICION_HISTORIAS' THEN 'medical_history.manage' "
                "WHEN 'ELIMINACION_HISTORIAS' THEN 'medical_history.delete' "
                "WHEN 'VISUALIZACION_ESTADOS' THEN 'states.view' "
                "WHEN 'CREACION_ESTADOS' THEN 'states.manage' "
                "WHEN 'EDICION_ESTADOS' THEN 'states.manage' "
                "WHEN 'ELIMINACION_ESTADOS' THEN 'states.manage' "
                "WHEN 'VISUALIZACION_DOCUMENTOS' THEN 'documents.view' "
                "WHEN 'CREACION_DOCUMENTOS' THEN 'documents.manage' "
                "WHEN 'EDICION_DOCUMENTOS' THEN 'documents.manage' "
                "WHEN 'ELIMINACION_DOCUMENTOS' THEN 'documents.manage' "
                "WHEN 'VISUALIZACION_ESPECIALISTA' THEN 'specialties.view' "
                "WHEN 'VISUALIZACION_ESPECIALISTAS' THEN 'specialties.view' "
                "WHEN 'CREACION_ESPEIALISTA' THEN 'specialties.manage' "
                "WHEN 'CREACION_ESPECIALISTA' THEN 'specialties.manage' "
                "WHEN 'CREACION_ESPECIALISTAS' THEN 'specialties.manage' "
                "WHEN 'EDICION_ESPECIALISTA' THEN 'specialties.manage' "
                "WHEN 'EDICION_ESPECIALISTAS' THEN 'specialties.manage' "
                "WHEN 'ELIMINACION_ESPECIALISTA' THEN 'specialties.manage' "
                "WHEN 'ELIMINACION_ESPECIALISTAS' THEN 'specialties.manage' "
                "WHEN 'VISUALIZACION_TIPOALERGIAS' THEN 'allergy_types.view' "
                "WHEN 'CREACION_TIPOALERGIAS' THEN 'allergy_types.manage' "
                "WHEN 'EDICION_TIPOALERGIAS' THEN 'allergy_types.manage' "
                "WHEN 'VISUALIZACION_ALERGIAS' THEN 'allergies.view' "
                "WHEN 'CREACION_ALERGIAS' THEN 'allergies.manage' "
                "WHEN 'EDICION_ALERGIAS' THEN 'allergies.manage' "
                "ELSE CASE WHEN position('.' IN lower(trim(p.nom_permiso))) > 0 "
                "THEN lower(trim(p.nom_permiso)) ELSE NULL END END AS permiso_key "
                "FROM permisos p) "
                "SELECT id_permiso, nom_permiso, usu_creacion, fec_creacion, "
                "usu_actualizacion, fec_actualizacion, activo, permiso_key, "
                "CASE permiso_key "
                "WHEN 'users.view' THEN 'Consultar usuarios' "
                "WHEN 'users.create' THEN 'Registrar usuarios' "
                "WHEN 'users.manage' THEN 'Crear y editar usuarios, estados y contraseñas' "
                "WHEN 'roles.manage' THEN 'Crear roles y asignar permisos' "
                "WHEN 'doctors.view' THEN 'Consultar profesionales' "
                "WHEN 'doctors.manage' THEN 'Registrar profesionales' "
                "WHEN 'doctors.link_user' THEN 'Vincular cuenta de acceso al profesional' "
                "WHEN 'specialties.view' THEN 'Consultar especialidades' "
                "WHEN 'specialties.manage' THEN 'Crear y editar especialidades' "
                "WHEN 'patients.view' THEN 'Consultar pacientes' "
                "WHEN 'patients.manage' THEN 'Registrar pacientes' "
                "WHEN 'patients.edit' THEN 'Editar pacientes' "
                "WHEN 'patients.delete' THEN 'Eliminar pacientes' "
                "WHEN 'appointments.view' THEN 'Consultar citas' "
                "WHEN 'appointments.manage' THEN 'Crear y reprogramar citas' "
                "WHEN 'audit.view' THEN 'Consultar auditoría' "
                "WHEN 'my_patients.view' THEN 'Consultar mis pacientes' "
                "WHEN 'medical_history.view' THEN 'Consultar historia clínica' "
                "WHEN 'medical_history.manage' THEN 'Crear historias y registrar/rectificar notas' "
                "WHEN 'medical_history.delete' THEN 'Archivar historias clínicas conservando las notas' "
                "WHEN 'states.view' THEN 'Consultar estados' "
                "WHEN 'states.manage' THEN 'Gestionar estados' "
                "WHEN 'documents.view' THEN 'Consultar documentos' "
                "WHEN 'documents.manage' THEN 'Gestionar documentos' "
                "WHEN 'allergy_types.view' THEN 'Consultar tipos de alergias' "
                "WHEN 'allergy_types.manage' THEN 'Crear y editar tipos de alergias' "
                "WHEN 'allergies.view' THEN 'Consultar alergias de pacientes' "
                "WHEN 'allergies.manage' THEN 'Registrar y editar alergias de pacientes' "
                "ELSE nom_permiso END AS etiqueta, "
                "CASE WHEN permiso_key LIKE 'users.%' THEN 'Usuarios' "
                "WHEN permiso_key = 'roles.manage' THEN 'Roles y permisos' "
                "WHEN permiso_key IN ('doctors.view','doctors.manage','doctors.link_user') THEN 'Profesionales' "
                "WHEN permiso_key LIKE 'specialties.%' THEN 'Especialidades' "
                "WHEN permiso_key LIKE 'patients.%' THEN 'Pacientes' "
                "WHEN permiso_key LIKE 'appointments.%' THEN 'Citas' "
                "WHEN permiso_key = 'audit.view' THEN 'Auditoría' "
                "WHEN permiso_key = 'my_patients.view' OR permiso_key LIKE 'medical_history.%' "
                "THEN 'Atención clínica' "
                "WHEN permiso_key LIKE 'states.%' THEN 'Estados' "
                "WHEN permiso_key LIKE 'documents.%' THEN 'Documentos' "
                "WHEN permiso_key LIKE 'allergy_types.%' THEN 'Tipos de alergias' "
                "WHEN permiso_key LIKE 'allergies.%' THEN 'Alergias' "
                "ELSE 'Otros permisos' END AS nom_grupo "
                "FROM normalized_permissions"
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
