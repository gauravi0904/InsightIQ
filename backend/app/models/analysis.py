from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.app.core.database import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
