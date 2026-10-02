from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cedula: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    usuario: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    id_role: Mapped[int] = mapped_column(ForeignKey("roles.id_role"), nullable=False)
    id_estado: Mapped[int] = mapped_column(Integer, nullable=False)
    usu_creacion: Mapped[str | None] = mapped_column(String(80))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usu_actualizacion: Mapped[str | None] = mapped_column(String(80))

    role: Mapped["Role"] = relationship(back_populates="users")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
