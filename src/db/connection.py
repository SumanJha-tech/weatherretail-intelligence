from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from config.settings import DATABASE_URL

_engine: Engine | None = None

def get_engine() -> Engine:
    """Process-wide engine. pool_pre_ping drops connections Postgres has already closed."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine