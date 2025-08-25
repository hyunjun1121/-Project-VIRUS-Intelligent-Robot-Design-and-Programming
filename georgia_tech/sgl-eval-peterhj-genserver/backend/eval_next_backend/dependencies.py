from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from eval_next_backend.consts import DB_URL

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 