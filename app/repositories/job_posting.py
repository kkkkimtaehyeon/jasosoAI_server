from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job_posting import JobPosting


class JobPostingRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_url(self, url: str):
        return self.db.query(JobPosting).filter(JobPosting.url == url).first()

    def save(self, job_posting: JobPosting) -> JobPosting:
        self.db.add(job_posting)
        self.db.commit()
        self.db.refresh(job_posting)
        return job_posting


def get_job_posting_repository(db: Session = Depends(get_db)) -> JobPostingRepository:
    return JobPostingRepository(db)
