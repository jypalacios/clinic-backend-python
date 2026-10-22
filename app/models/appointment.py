from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.state import State

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.patient import Patient


class Appointment(Base):
    __tablename__ = "appointments"

    id_appointments: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_patients: Mapped[int] = mapped_column(
        ForeignKey("patients.id_patients"), nullable=False
    )
    id_doctors: Mapped[int] = mapped_column(ForeignKey("doctors.id_doctors"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    id_estado: Mapped[int] = mapped_column(ForeignKey("estados.id_estado"), nullable=False)
    usu_creacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fec_ingreso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fec_dilatacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fec_finaliza: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    prioridad: Mapped[bool | None] = mapped_column(Boolean)
    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
    state: Mapped[State] = relationship(lazy="joined")

    @property
    def nom_estado(self) -> str:
        return self.state.nom_estado

    @property
    def paciente(self) -> str:
        return f"{self.patient.nom_patients} {self.patient.ape_patients}"

    @property
    def discapacidad(self) -> bool:
        return bool(self.patient.discapacidad)

    @property
    def medico(self) -> str:
        return f"{self.doctor.nom_doctors} {self.doctor.ape_doctors}"
