from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class Document(Base):
    __tablename__ = "documents"

    id_documents: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    desc_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    desc_documents: Mapped[str] = mapped_column(String(100), nullable=False)

    patients: Mapped[list["Patient"]] = relationship(back_populates="document")


class DocumentCatalog(Base):
    __tablename__ = "v_documents"

    id_documents: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    desc_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    desc_documents: Mapped[str] = mapped_column(String(100), nullable=False)
