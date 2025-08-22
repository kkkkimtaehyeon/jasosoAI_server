from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    oauth_id = Column(String(255), nullable=True, unique=True)

    # # CoverLetter와 1:N 관계
    cover_letters = relationship(
        "CoverLetter",
        back_populates="user",
        cascade="all, delete-orphan"
    )
