from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id_logs: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    ip: Mapped[str | None] = mapped_column(INET)
    timestamp: Mapped[datetime] = mapped_column(
        "timestamp", DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
