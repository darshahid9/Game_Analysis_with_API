from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "tennis_analytics.db"


def get_engine() -> Engine:
    """Return a SQLAlchemy engine for the local SQLite database."""
    return create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
    )


def run_schema(engine: Engine, schema_path: str = "sql/schema.sql") -> None:
    """
    Kept for compatibility with the existing loader.

    The Streamlit application uses the already-created SQLite database,
    so no schema creation is required when the app starts.
    """
    pass
