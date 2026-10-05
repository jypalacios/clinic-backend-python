from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    __tablename__ = "roles"

    id_role: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom_role: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    permisos: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    usu_creacion: Mapped[int | None] = mapped_column(Integer)
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(Integer)
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["User"]] = relationship(back_populates="role")
