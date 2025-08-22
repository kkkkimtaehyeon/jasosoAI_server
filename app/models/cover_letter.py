# app/models/cover_letter.py

import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.cover_letter_item import CoverLetterItem


# CoverLetterType enum 정의
class CoverLetterType(str, enum.Enum):
    AI = "AI"
    USER = "USER"


class CoverLetter(Base):
    __tablename__ = "cover_letter"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    type = Column(Enum(CoverLetterType), default=CoverLetterType.USER, nullable=False)

    # 1:N 관계: CoverLetter가 여러 개의 CoverLetterItem을 가짐
    items: Mapped[list[CoverLetterItem]] = relationship("CoverLetterItem", back_populates="cover_letter", cascade="all, delete-orphan")

    # N:1 관계: 여러 CoverLetter가 한 User에 속함
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="cover_letters")