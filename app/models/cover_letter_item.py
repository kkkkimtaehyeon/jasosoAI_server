# app/models/cover_letter_item.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class CoverLetterItem(Base):
    __tablename__ = "cover_letter_item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question = Column(String(500), nullable=False)
    char_limit = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # N:1 관계: 여러 CoverLetterItem이 하나의 CoverLetter에 속함
    cover_letter_id = Column(Integer, ForeignKey("cover_letter.id"), nullable=False)
    cover_letter = relationship("CoverLetter", back_populates="items")
