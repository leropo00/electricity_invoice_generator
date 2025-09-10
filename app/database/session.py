from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

debug_queries = os.getenv("DEBUG_QUERIES", "false").lower() == "true"

engine = create_engine(os.getenv("DATABASE_URI"), echo=debug_queries)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
