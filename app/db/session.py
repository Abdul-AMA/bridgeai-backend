from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Ensure charset=utf8mb4 is set for full Unicode support (including Arabic, emoji, etc.)
database_url = settings.DATABASE_URL
if "mysql" in database_url.lower() and "charset" not in database_url.lower():
    # Add charset parameter if not present for MySQL/MariaDB
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}charset=utf8mb4"

_is_sqlite = database_url.startswith("sqlite")
_engine_kwargs = {} if _is_sqlite else {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "pool_timeout": 30,
}
engine = create_engine(database_url, echo=False, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
