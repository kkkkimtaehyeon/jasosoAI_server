from typing import Optional

from fastapi import Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cover_letter import CoverLetter, CoverLetterType


class CoverLetterRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, cover_letter: CoverLetter) -> CoverLetter:
        self.db.add(cover_letter)
        self.db.commit()
        self.db.refresh(cover_letter)
        return cover_letter

    def find_all_by_user_id(self, user_id: int, type: CoverLetterType) -> list[CoverLetter]:
        query = (
            self.db.query(CoverLetter)
            .filter(
                CoverLetter.user_id == user_id,
                CoverLetter.type == type.value
            )
            .order_by(desc(CoverLetter.created_at))
        )
        return query.all()

    def find_by_id(self, cover_letter_id) -> Optional[CoverLetter]:
        return self.db.get(CoverLetter, cover_letter_id)

    def delete_by_id(self, cover_letter_id) -> None:
        cover_letter = self.find_by_id(cover_letter_id)
        if cover_letter:
            self.db.delete(cover_letter)
            self.db.commit()


def get_cover_letter_repository(db: Session = Depends(get_db)) -> CoverLetterRepository:
    return CoverLetterRepository(db)
