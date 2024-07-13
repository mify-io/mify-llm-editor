import logging
import os
import sys
from typing import Any

from anthropic import Anthropic

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _init_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def _init_db():
    SQLALCHEMY_DATABASE_URL = "sqlite:///./storage.db"
    # SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"


    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

class Context:
    def __init__(self) -> None:
        self.logger = _init_logger()
        self.anthropic_client = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
        )
        self.db_pool = _init_db()

    def add_dependencies(self, deps: Any):
        self.deps = deps
