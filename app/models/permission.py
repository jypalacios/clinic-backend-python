from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Permission(Base):
    __tablename__ = "permisos"

    id_permiso: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nom_permiso: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    usu_creacion: Mapped[int | None] = mapped_column(Integer)
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(Integer)
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class RolePermission(Base):
    __tablename__ = "matriz_permisos"
    __table_args__ = (Index("ux_matriz_permisos", "id_role", "id_permiso", unique=True),)

    id_matriz: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_role: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id_role"), nullable=False)
    id_permiso: Mapped[int] = mapped_column(BigInteger, ForeignKey("permisos.id_permiso"), nullable=False)
    usu_creacion: Mapped[int | None] = mapped_column(Integer)
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(Integer)
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activo: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=True, server_default="true")
