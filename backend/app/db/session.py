from sqlalchemy import create_engine
from app.core.config import settings
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,

)
SessionLocal = sessionmaker(expire_on_commit=False, autoflush=False, bind=engine)