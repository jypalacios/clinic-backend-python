from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id_patients: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ced_patients: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nom_patients: Mapped[str] = mapped_column(String(80), nullable=False)
    ape_patients: Mapped[str] = mapped_column(String(80), nullable=False)
    fec_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    id_sexo: Mapped[int] = mapped_column(ForeignKey("sexo.id_sexo"), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(255))
    eps: Mapped[str | None] = mapped_column(String(120))
    contacto_emergencia: Mapped[str | None] = mapped_column(String(120))

    sexo: Mapped["Sexo"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
    clinical_records: Mapped[list["ClinicalRecord"]] = relationship(back_populates="patient")
