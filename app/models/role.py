from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id_role: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom_role: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    usu_creacion: Mapped[str | None] = mapped_column(String(80))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[str | None] = mapped_column(String(80))
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["User"]] = relationship(back_populates="role")
