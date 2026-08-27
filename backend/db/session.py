from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def configure_engine() -> None:
    global engine, SessionLocal
    if not DATABASE_URL:
        return
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Motor SQL configurado (pool_pre_ping activo).")


def init_db() -> None:
    if engine is None:
        return
    from backend.db.models import Base

    Base.metadata.create_all(bind=engine)
    logger.info("Tablas SQL verificadas/creadas.")


def dispose_engine() -> None:
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
        logger.info("Motor SQL cerrado.")
    engine = None
    SessionLocal = None
