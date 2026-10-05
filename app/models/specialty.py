from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Specialty(Base):
    """Especialidad médica (tabla `espect` en config.md)."""

    __tablename__ = "espect"

    id_espect: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom_espect: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="specialty")
