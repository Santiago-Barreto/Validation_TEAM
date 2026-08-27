from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PuntoValidacion(Base):
    """Comentario / corrección del equipo de validación."""

    __tablename__ = "puntos_validacion_team"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    comentario: Mapped[str] = mapped_column(Text, default="", nullable=False)
    nombre: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    clasificacion: Mapped[str] = mapped_column(String(64), nullable=False)
    anio_contexto: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    clase_col3: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    clase_col4: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    bioma: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    clase_sugerida: Mapped[str] = mapped_column(String(32), default="", nullable=False)
