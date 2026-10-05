from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.patient import Patient


class ClinicalRecord(Base):
    __tablename__ = "clinical_records"

    id_clinic: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_patients: Mapped[int] = mapped_column(ForeignKey("patients.id_patients"), nullable=False, unique=True)
    id_doctors: Mapped[int] = mapped_column(ForeignKey("doctors.id_doctors"), nullable=False)
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    patient: Mapped["Patient"] = relationship()
    doctor: Mapped["Doctor"] = relationship()
    entries: Mapped[list["ClinicalEntry"]] = relationship(
        back_populates="record",
        order_by="ClinicalEntry.fec_entrada.desc()",
    )


class ClinicalEntry(Base):
    __tablename__ = "clinical_entries"

    id_entries: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_clinics: Mapped[int] = mapped_column(ForeignKey("clinical_records.id_clinic"), nullable=False)
    id_doctors: Mapped[int] = mapped_column(ForeignKey("doctors.id_doctors"), nullable=False)
    id_entries_rectifica: Mapped[int | None] = mapped_column(
        ForeignKey("clinical_entries.id_entries"), nullable=True
    )
    fec_entrada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    motivo_consulta: Mapped[str] = mapped_column(Text, nullable=False)
    examen_fisico: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str | None] = mapped_column(Text)
    formulacion: Mapped[str | None] = mapped_column(Text)
    notas: Mapped[str | None] = mapped_column(Text)

    record: Mapped[ClinicalRecord] = relationship(back_populates="entries")
    doctor: Mapped["Doctor"] = relationship()
