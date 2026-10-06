from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

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
    estado: Mapped[str] = mapped_column(String(40), nullable=False)
    usu_creacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    doctor: Mapped["Doctor"] = relationship(back_populates="appointments")
