from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.document import Document
from app.models.entity import CliEntidad

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
    edad: Mapped[int] = mapped_column(Integer, nullable=False)
    id_sexo: Mapped[int] = mapped_column(ForeignKey("sexo.id_sexo"), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    direccion: Mapped[str | None] = mapped_column(String(255))
    nit_entidad: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("cli_entidades.nit"), nullable=True
    )
    contacto_emergencia: Mapped[str | None] = mapped_column(String(200))
    discapacidad: Mapped[bool | None] = mapped_column(Boolean)

    document: Mapped[Document] = relationship(back_populates="patients")
    sexo: Mapped["Sexo"] = relationship(back_populates="patients")
    entidad: Mapped[CliEntidad | None] = relationship(lazy="joined")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")

    @property
    def nom_entidad(self) -> str | None:
        return self.entidad.nom_entidad if self.entidad else None
