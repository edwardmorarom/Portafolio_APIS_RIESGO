from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM del proyecto."""
    pass


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """
    Crea la carpeta del archivo SQLite si la URL usa sqlite:///ruta.db.
    Evita errores cuando la carpeta data/ todavía no existe.
    """
    if not database_url.startswith("sqlite:///"):
        return

    db_path = database_url.replace("sqlite:///", "", 1)

    if db_path == ":memory:":
        return

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_dir(settings.database_url)

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia para inyectar una sesión SQLAlchemy por request.
    La sesión se cierra siempre al finalizar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Crea las tablas registradas en los modelos ORM.
    Útil para desarrollo local y pruebas iniciales.
    """
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)