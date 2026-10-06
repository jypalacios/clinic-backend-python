import csv
import io
import unicodedata
from collections import Counter
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient_import_schema import (
    PatientCSVPreview,
    PatientCSVPreviewRow,
    PatientCSVRowError,
)
from app.schemas.patient_schema import PatientCreate

MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_CSV_ROWS = 5000
PREVIEW_ROW_LIMIT = 10

CSV_FIELDS = {
    "cedula": "ced_patients",
    "nombres": "nom_patients",
    "apellidos": "ape_patients",
    "fecha_nacimiento": "fec_nacimiento",
    "sexo": "sexo",
    "telefono": "telefono",
    "email": "email",
    "direccion": "direccion",
    "eps": "eps",
    "contacto_emergencia": "contacto_emergencia",
}
REQUIRED_HEADERS = {"cedula", "nombres", "apellidos", "fecha_nacimiento", "sexo"}
FIELD_LABELS = {
    "ced_patients": "Identificación",
    "nom_patients": "Nombres",
    "ape_patients": "Apellidos",
    "fec_nacimiento": "Fecha de nacimiento",
    "sexo": "Sexo",
    "telefono": "Teléfono",
    "email": "Correo electrónico",
    "direccion": "Dirección",
    "eps": "EPS",
    "contacto_emergencia": "Contacto de emergencia",
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    without_accents = "".join(character for character in decomposed if not unicodedata.combining(character))
    return without_accents


class PatientCSVImportService:
    def __init__(self, db: Session):
        self.repo = PatientRepository(db)

    def preview(self, filename: str | None, content: bytes) -> PatientCSVPreview:
        rows = self._validate_file(filename, content)
        valid_rows = [row for row in rows if not row["messages"]]
        preview = [
            PatientCSVPreviewRow(row_number=row["row_number"], patient=row["patient"])
            for row in valid_rows[:PREVIEW_ROW_LIMIT]
        ]
        invalid_rows = len(rows) - len(valid_rows)
        return PatientCSVPreview(
            total_rows=len(rows),
            valid_rows=len(valid_rows),
            invalid_rows=invalid_rows,
            can_import=bool(rows) and not invalid_rows,
            preview_rows=preview,
            errors=[
                PatientCSVRowError(row_number=row["row_number"], messages=row["messages"])
                for row in rows
                if row["messages"]
            ],
        )

    def import_file(self, filename: str | None, content: bytes, user: User) -> int:
        rows = self._validate_file(filename, content)
        invalid_rows = [row for row in rows if row["messages"]]
        if invalid_rows or not rows:
            raise ValueError(
                "El archivo contiene errores; no se importó ningún paciente. "
                "Corrija el CSV y vuelva a validarlo."
            )

        patients = [Patient(**row["patient"].model_dump()) for row in rows]
        return self.repo.import_many(patients, user.id)

    def _validate_file(
        self,
        filename: str | None,
        content: bytes,
    ) -> list[dict[str, Any]]:
        if not filename or not filename.casefold().endswith(".csv"):
            raise ValueError("Seleccione un archivo con extensión .csv")
        if len(content) > MAX_CSV_BYTES:
            raise ValueError("El archivo supera el límite de 5 MB")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("El archivo debe estar codificado en UTF-8") from exc
        if not text.strip():
            raise ValueError("El archivo CSV está vacío")

        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;")
            reader = csv.DictReader(io.StringIO(text, newline=""), dialect=dialect)
            headers = reader.fieldnames
        except csv.Error as exc:
            raise ValueError("No se pudo determinar el separador CSV. Use comas o punto y coma.") from exc
        if not headers:
            raise ValueError("El CSV debe incluir una fila de encabezados")

        normalized_headers = [_normalize(header) if header else "" for header in headers]
        repeated_headers = [header for header, count in Counter(normalized_headers).items() if count > 1]
        if repeated_headers:
            raise ValueError(f"Hay encabezados repetidos: {', '.join(repeated_headers)}")
        unknown_headers = sorted(set(normalized_headers) - set(CSV_FIELDS))
        missing_headers = sorted(REQUIRED_HEADERS - set(normalized_headers))
        if unknown_headers or missing_headers:
            problems = []
            if missing_headers:
                problems.append(f"faltan columnas obligatorias: {', '.join(missing_headers)}")
            if unknown_headers:
                problems.append(f"columnas no reconocidas: {', '.join(unknown_headers)}")
            raise ValueError("Encabezados CSV inválidos; " + "; ".join(problems))

        sexos = self.repo.list_sexos()
        sexos_by_name = {_normalize(sexo.nom_sexo): sexo.id_sexo for sexo in sexos}
        parsed_rows: list[dict[str, Any]] = []
        data_rows = 0
        for row_number, raw_row in enumerate(reader, start=2):
            if raw_row is None or all(not (value or "").strip() for value in raw_row.values() if value is not None):
                continue
            data_rows += 1
            if data_rows > MAX_CSV_ROWS:
                raise ValueError(f"El archivo supera el límite de {MAX_CSV_ROWS} filas")

            messages: list[str] = []
            if None in raw_row:
                messages.append("La fila tiene más valores que columnas")

            source = {
                header: (raw_row.get(original_header) or "").strip()
                for header, original_header in zip(normalized_headers, headers)
            }
            sex_name = _normalize(source.get("sexo", ""))
            sex_id = sexos_by_name.get(sex_name)
            if sex_id is None:
                messages.append(
                    "Sexo no reconocido; use uno de los valores del catálogo: "
                    + ", ".join(sexo.nom_sexo for sexo in sexos)
                )

            patient_data = {
                CSV_FIELDS[header]: source.get(header) or None
                for header in CSV_FIELDS
                if header != "sexo"
            }
            patient_data["id_sexo"] = sex_id if sex_id is not None else 1
            try:
                patient = PatientCreate.model_validate(patient_data)
            except ValidationError as exc:
                for error in exc.errors():
                    field = str(error["loc"][0])
                    label = FIELD_LABELS.get(field, field)
                    message = "es obligatorio" if error["type"] == "missing" else str(error["msg"])
                    messages.append(f"{label}: {message}")
                patient = None
            parsed_rows.append({
                "row_number": row_number,
                "patient": patient,
                "identification": source.get("cedula", ""),
                "messages": messages,
            })

        if not parsed_rows:
            raise ValueError("El archivo no contiene filas de pacientes")

        rows_with_identification = [row for row in parsed_rows if row["identification"]]
        identification_counts = Counter(row["identification"] for row in rows_with_identification)
        duplicate_ids = {
            identification for identification, count in identification_counts.items() if count > 1
        }
        existing_ids = self.repo.existing_identifications(set(identification_counts))
        for row in rows_with_identification:
            identification = row["identification"]
            if identification in duplicate_ids:
                row["messages"].append("La identificación está repetida dentro del archivo")
            if identification in existing_ids:
                row["messages"].append("La identificación ya está registrada")

        return parsed_rows
