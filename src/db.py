from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.config import DB_CONFIG


def get_engine() -> Engine:
    """Return a SQLAlchemy engine for the tennis_analytics MySQL database."""
    url = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url, pool_pre_ping=True)


def run_schema(engine: Engine, schema_path: str = "sql/schema.sql") -> None:
    """Execute the schema.sql file statement-by-statement (idempotent, uses IF NOT EXISTS)."""
    with open(schema_path, "r", encoding="utf-8") as f:
        raw = f.read()

    statements = [
    s.strip()
    for s in raw.split(";")
    if s.strip()
    and not s.strip().startswith("--")
    and not s.strip().upper().startswith("CREATE INDEX")
]

    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)
