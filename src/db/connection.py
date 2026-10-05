from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from config.settings import DATABASE_URL

_engine: Engine | None = None

def get_engine() -> Engine:
    """Returns one shared SQLAlchemy engine (connection pool) for the whole app."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine