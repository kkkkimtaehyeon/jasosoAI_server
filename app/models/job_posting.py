from datetime import datetime

from sqlalchemy import Integer, Column, String, DateTime, Text

from app.core.database import Base


class JobPosting(Base):
    __tablename__ = 'job_posting'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(Text, nullable=False)
    company_name = Column(String(255), nullable=True)
    position_title = Column(String(255), nullable=True)
    experience = Column(String(50), nullable=True)
    position_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    required_qualifications = Column(Text, nullable=True)
    preferred_qualifications = Column(Text, nullable=True)

