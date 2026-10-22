from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class State(Base):
    __tablename__ = "estados"

    id_estado: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_estado: Mapped[str] = mapped_column(String(30), nullable=False,     unique=True)
