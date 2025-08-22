from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


class AiCoverLetterRepository:
    def __init__(self, db: Session):
        self.db = db


def get_ai_cover_letter_repository(db: Session = Depends(get_db)) -> AiCoverLetterRepository:
    return AiCoverLetterRepository(db)
