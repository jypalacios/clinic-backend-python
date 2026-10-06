from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.sexo import Sexo
    from app.models.specialty import Specialty


class Doctor(Base):
    __tablename__ = "doctors"

    id_doctors: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_user: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    ape_doctors: Mapped[str] = mapped_column(String(100), nullable=False)
    nom_doctors: Mapped[str] = mapped_column(String(100), nullable=False)
    id_espect: Mapped[int] = mapped_column(ForeignKey("espect.id_espect"), nullable=False)
    id_sexo: Mapped[int] = mapped_column(ForeignKey("sexo.id_sexo"), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    direccion: Mapped[str | None] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    usu_creacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    specialty: Mapped["Specialty"] = relationship(back_populates="doctors")
    sexo: Mapped["Sexo"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
