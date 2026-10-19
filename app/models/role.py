from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.permissions import permission_key_for_name
from app.db.base import Base
from app.models.permission import Permission, RolePermission

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    __tablename__ = "roles"

    id_role: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom_role: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    usu_creacion: Mapped[int | None] = mapped_column(Integer)
    fec_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usu_actualizacion: Mapped[int | None] = mapped_column(Integer)
    fec_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    users: Mapped[list["User"]] = relationship(back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="matriz_permisos",
        primaryjoin=lambda: Role.id_role == RolePermission.id_role,
        secondaryjoin=lambda: (
            (Permission.id_permiso == RolePermission.id_permiso)
            & RolePermission.activo.is_(True)
            & Permission.activo.is_(True)
        ),
        viewonly=True,
        lazy="selectin",
    )

    @property
    def permisos(self) -> list[str]:
        return list(
            dict.fromkeys(
                permission_key
                for permission in self.permissions
                if (permission_key := permission_key_for_name(permission.nom_permiso)) is not None
            )
        )
