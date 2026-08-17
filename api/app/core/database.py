from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import config

Base = declarative_base()

import pkgutil
import importlib
import app.module

for module_info in pkgutil.walk_packages(app.module.__path__, "app.module."):
    if module_info.name.endswith(".model"):
        importlib.import_module(module_info.name)

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
