from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base 
from sqlalchemy import BigInteger, String 

class Dataset(Base):
    __tablename__ = "datasets"
    id : Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    stored_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
        