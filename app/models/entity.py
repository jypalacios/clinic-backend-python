from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CliEntidad(Base):
    __tablename__ = "cli_entidades"

    nit: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nom_entidad: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
