from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id_doctors: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ape_doctors: Mapped[str] = mapped_column(String(80), nullable=False)
    nom_doctors: Mapped[str] = mapped_column(String(80), nullable=False)
    id_espect: Mapped[int] = mapped_column(ForeignKey("espect.id_espect"), nullable=False)
    id_sexo: Mapped[int] = mapped_column(ForeignKey("sexo.id_sexo"), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(255))
    usu_creacion: Mapped[str | None] = mapped_column(String(80))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[str | None] = mapped_column(String(80))
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    specialty: Mapped["Specialty"] = relationship(back_populates="doctors")
    sexo: Mapped["Sexo"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
    clinical_records: Mapped[list["ClinicalRecord"]] = relationship(back_populates="doctor")
    clinical_entries: Mapped[list["ClinicalEntry"]] = relationship(back_populates="doctor")
