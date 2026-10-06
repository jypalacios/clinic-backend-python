# Clinica Backend

Aplicación de backend para la gestión clínica, desarrollada con FastAPI, SQLAlchemy y PostgreSQL.

## Arquitectura general

┌──────────────┐     HTTP/JSON     ┌────────────────┐     SQLAlchemy     ┌──────────────┐
│  Frontend    │ ───────────────► │   Backend      │ ───────────────► │  PostgreSQL  │
│  React / UI  │                  │  FastAPI       │                  │  Base de     │
│              │                  │  + SQLAlchemy  │                  │  datos       │
└──────────────┘                  └────────────────┘                  └──────────────┘

## Objetivo del proyecto

Este backend permite:
- gestionar usuarios y roles
- registrar pacientes
- gestionar médicos y especialidades
- agendar citas
- autenticar usuarios mediante JWT
- mantener el esquema versionado con Alembic

## Stack tecnológico

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- Pydantic
- Passlib + Argon2
- python-jose
- Docker / Docker Compose

## Estructura del proyecto

clinica_backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── patients.py
│   │       ├── doctors.py
│   │       ├── clinical_records.py
│   │       └── appointments.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── deps.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── sexo.py
│   │   ├── specialty.py
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── clinical_record.py
│   │   └── appointment.py
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── user_schema.py
│   │   ├── patient_schema.py
│   │   ├── doctor_schema.py
│   │   ├── clinical_record_schema.py
│   │   └── appointment_schema.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── patient_repository.py
│   │   ├── doctor_repository.py
│   │   ├── clinical_record_repository.py
│   │   └── appointment_repository.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── patient_service.py
│   │   ├── doctor_service.py
│   │   ├── clinical_record_service.py
│   │   └── appointment_service.py
│   ├── main.py
│   └── __init__.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── 01_tablas.sql
├── 02_procedimientos.sql
├── 03_vistas.sql
├── 05_historias_clinicas.sql
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── config.md
└── README.md

## Principales módulos de negocio

### Autenticación
- login con email y contraseña
- generación de token JWT
- validación del usuario autenticado
- control de acceso por permisos asignados al rol
- permisos iniciales para `ADMINISTRADOR`, `ASISTENTE` y `MEDICO`, preservados al migrar la base de datos

### Usuarios
- registro y actualización de usuarios
- alta y edición de roles y permisos por módulo
- cambio administrativo de contraseña con hash Argon2
- validación de email, usuario y cédula

### Pacientes
- registro de pacientes
- consulta por identificación
- relación con citas
- importación CSV con validación previa, detección de identificaciones duplicadas y transacción todo-o-nada (requiere `patients.manage`)

### Médicos
- registro de médicos
- consulta por especialidad y datos del profesional
- gestión del catálogo de especialidades
- administradores y asistentes pueden registrar profesionales y crear especialidades

### Citas
- agendamiento de consultas
- el perfil asistente puede crear citas futuras y reprogramar fecha, hora o médico de citas programadas/confirmadas
- validación de paciente/médico activos, disponibilidad del médico y auditoría de altas y reprogramaciones
- consulta por disponibilidad y historial

### Historias clínicas
- apertura de una historia por paciente y captura de la primera atención
- el médico solo consulta pacientes con citas asignadas y no canceladas; la apertura valida esa asignación en el backend
- médicos con cuenta vinculada pueden agregar evoluciones y rectificaciones
- las notas son de solo inserción: una rectificación crea una nota enlazada y conserva el original
- administradores pueden archivar y restaurar historias; se conservan tanto cabecera como notas y queda auditoría de cada acción
- las cuentas médicas se vinculan al perfil profesional desde Médicos y profesionales

## Flujo de trabajo recomendado

1. La base de datos PostgreSQL queda levantada con Docker o con el entorno del proyecto.
2. El backend inicia con FastAPI.
3. Los endpoints consumen la capa de servicios.
4. Los servicios usan repositorios para acceso a datos.
5. Los modelos SQLAlchemy reflejan el esquema de la base.
6. Alembic se usa para versionar futuros cambios de esquema.

## Estado actual

El proyecto ya cuenta con:
- estructura base del backend
- modelos principales
- schemas Pydantic
- repositorios
- servicios
- endpoints v1
- seguridad JWT y autorización por permisos, aplicada a las rutas de frontend y endpoints
- configuración Alembic

La columna `roles.permisos` y las migraciones de permisos e historias clínicas se aplican automáticamente al iniciar la aplicación en bases existentes. Los scripts `04_permisos_roles.sql` y `05_historias_clinicas.sql` contienen las migraciones manuales equivalentes.

### Administración de acceso
- `GET /api/v1/roles/` lista los roles para usuarios con permiso de consulta de usuarios o administración de roles.
- `POST /api/v1/roles/` y `PUT /api/v1/roles/{role_id}` crean roles o editan nombre y permisos.
- `PUT /api/v1/users/{user_id}/password` cambia una contraseña sin exponerla en el CRUD general.
- `POST /api/v1/patients/import/preview` valida un CSV multipart y devuelve un resumen, una muestra de filas válidas y errores por fila.
- `POST /api/v1/patients/import` vuelve a validar el CSV y lo importa en una única transacción; rechaza el archivo completo si alguna fila es inválida.
- `POST /api/v1/appointments/` crea una cita con estado inicial `PROGRAMADA`.
- `PUT /api/v1/appointments/{appointment_id}` reprograma la fecha/hora o el médico de una cita programada o confirmada; requiere `appointments.manage`.
- `GET/POST /api/v1/clinical-records/` consulta y abre historias clínicas.
- Para médicos, `GET /api/v1/patients/` se limita a sus pacientes con citas no canceladas ni marcadas como inasistencia.
- `POST /api/v1/clinical-records/{record_id}/entries` agrega una evolución.
- `PUT /api/v1/clinical-records/{record_id}/entries/{entry_id}` registra una rectificación inmutable.
- `DELETE /api/v1/clinical-records/{record_id}` archiva la historia (permiso exclusivo de administración).
- `PUT /api/v1/clinical-records/{record_id}/restore` restaura una historia archivada (permiso exclusivo de administración).
- `PUT /api/v1/doctors/{doctor_id}/user` vincula una cuenta con rol médico a su perfil profesional.
- `GET /api/v1/auth/me` devuelve los permisos efectivos del usuario para construir el menú y proteger rutas.
- Los permisos `*.manage` incluyen también el permiso de consulta `*.view` del mismo módulo.
- El rol `ASISTENTE` puede consultar la lista y registrar usuarios no administradores; solo roles con `users.manage` pueden editar usuarios, cambiar contraseñas y administrar estados.
- El rol `MEDICO` recibe permiso de consulta y gestión de historias; `ADMINISTRADOR` recibe archivo lógico y vinculación de cuentas médicas.
- La primera actualización posterior a esta versión agrega una sola vez `users.view` y `users.create` a `ASISTENTE`, conservando los permisos ya configurados.

### Importación de pacientes por CSV
- Descargue desde Pacientes la plantilla UTF-8 y use encabezados `cedula,nombres,apellidos,fecha_nacimiento,sexo,telefono,email,direccion,eps,contacto_emergencia`.
- Son obligatorios `cedula`, `nombres`, `apellidos`, `fecha_nacimiento` (formato `AAAA-MM-DD`) y `sexo`; los demás campos son opcionales. El valor de `sexo` debe coincidir con una opción del catálogo.
- Se aceptan separadores coma o punto y coma; el tamaño máximo es 5 MB y el archivo admite hasta 5.000 filas de datos.
- La previsualización valida encabezados, tipos, longitudes, catálogo de sexo e identificaciones duplicadas en el archivo o en la base. Muestra máximo 10 filas válidas y los errores por número de fila.
- La confirmación vuelve a validar el mismo archivo. No se actualizan pacientes existentes y no se inserta ningún paciente si hay errores. Una falla al guardar revierte toda la carga.
- El log de auditoría guarda el usuario, la cantidad importada y el origen CSV; no almacena las filas ni datos personales del archivo.

## Siguientes mejoras propuestas

- implementar paginación y filtros
- ampliar pruebas automáticas
