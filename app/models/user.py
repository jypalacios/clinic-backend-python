from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cedula: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    usuario: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    id_role: Mapped[int] = mapped_column(ForeignKey("roles.id_role"), nullable=False)
    id_estado: Mapped[int] = mapped_column(Integer, nullable=False)
    usu_creacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usu_actualizacion: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    role: Mapped[Role] = relationship(back_populates="users")
