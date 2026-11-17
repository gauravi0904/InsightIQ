from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from backend.app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processing_status = Column(String(50), default="ready")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
