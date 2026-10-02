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
│   │   └── appointment.py
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── user_schema.py
│   │   ├── patient_schema.py
│   │   ├── doctor_schema.py
│   │   └── appointment_schema.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── patient_repository.py
│   │   ├── doctor_repository.py
│   │   └── appointment_repository.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── patient_service.py
│   │   ├── doctor_service.py
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
- control de acceso por rol

### Usuarios
- registro y actualización de usuarios
- control de roles
- validación de email, usuario y cédula

### Pacientes
- registro de pacientes
- consulta por identificación
- relación con citas

### Médicos
- registro de médicos
- consulta por especialidad y datos del profesional

### Citas
- agendamiento de consultas
- asociación con paciente y médico
- consulta por disponibilidad y historial

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
- seguridad JWT y control por roles
- configuración Alembic

## Siguientes mejoras propuestas

- completar módulos de historias clínicas
- añadir auditoría de acciones
- implementar paginación y filtros
- consolidar validaciones por rol y permisos más específicos
- preparar pruebas automáticas


