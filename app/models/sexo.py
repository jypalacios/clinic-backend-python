from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sexo(Base):
    __tablename__ = "sexo"

    id_sexo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom_sexo: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)

    patients: Mapped[list["Patient"]] = relationship(back_populates="sexo")
    doctors: Mapped[list["Doctor"]] = relationship(back_populates="sexo")
