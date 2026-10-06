from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.sexo import Sexo


class Patient(Base):
    __tablename__ = "patients"

    id_patients: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ced_patients: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nom_patients: Mapped[str] = mapped_column(String(100), nullable=False)
    ape_patients: Mapped[str] = mapped_column(String(100), nullable=False)
    fec_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    id_sexo: Mapped[int] = mapped_column(ForeignKey("sexo.id_sexo"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    direccion: Mapped[str | None] = mapped_column(String(255))
    eps: Mapped[str | None] = mapped_column(String(100))
    contacto_emergencia: Mapped[str | None] = mapped_column(String(200))

    sexo: Mapped["Sexo"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
