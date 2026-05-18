from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_settings


settings = get_settings()

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM del proyecto."""
    pass


def _resolve_sqlite_url(database_url: str) -> str:
    """
    Resuelve rutas SQLite relativas contra la carpeta backend/.

    Esto evita que la base cambie dependiendo de si el comando se ejecuta desde:
    - la raíz del proyecto
    - backend/
    - pytest
    - GitHub Actions
    """
    if not database_url.startswith("sqlite:///"):
        return database_url

    db_path_raw = database_url.replace("sqlite:///", "", 1)

    if db_path_raw == ":memory:":
        return database_url

    db_path = Path(db_path_raw)

    if not db_path.is_absolute():
        db_path = BACKEND_DIR / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{db_path.as_posix()}"


DATABASE_URL = _resolve_sqlite_url(settings.database_url)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
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
