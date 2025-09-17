
import enum

from sqlalchemy import Column, Integer, DateTime, Enum
from sqlalchemy.sql import func

from app.core.database import Base


# CoverLetterType enum 정의
class ApiType(str, enum.Enum):
    EMBEDDING = "EMBEDDING_MODEL"
    TEXT = "TEXT_MODEL"


class ApiCallLog(Base):
    __tablename__ = "api_call_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    api_type = Column(Enum(ApiType), nullable=False)
    consumed = Column(Integer, nullable=False)
