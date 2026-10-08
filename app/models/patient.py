from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.document import Document

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.sexo import Sexo


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("id_documents", "ced_patients", name="uq_patients_document_identification"),
    )

    id_patients: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ced_patients: Mapped[str] = mapped_column(String(20), nullable=False)
    id_documents: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id_documents"),
        nullable=False,
    )
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

    document: Mapped[Document] = relationship(back_populates="patients")
    sexo: Mapped["Sexo"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
