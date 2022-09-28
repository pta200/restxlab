from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
from sqlalchemy.engine.url import URL
import os
from .db_models import *

logger = logging.getLogger(__name__)
logger.info("start postgres engine....")

engine_uri = URL(
        drivername='postgresql',
        username=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        database=os.environ.get("POSTGRES_DATABASE")
    )
engine = create_engine(engine_uri, pool_size=int(os.environ.get("POOL_SIZE")),
        max_overflow=int(os.environ.get("POOL_OVERFLOW")))

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    logger.info("init db....")
    Base.metadata.create_all(bind=engine)