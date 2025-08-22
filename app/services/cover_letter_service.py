from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cover_letter import CoverLetter, CoverLetterType
from app.models.cover_letter_item import CoverLetterItem
from app.repositories.cover_letter import CoverLetterRepository, get_cover_letter_repository
from app.schemas.cover_letter import CoverLetterAdditionRequest, CoverLetterResponse, CoverLetterSimpleResponse, \
    CoverLetterEditRequest
from app.utils import embedding


def save_embedding_task(user_id: int, cover_letter: CoverLetterResponse):
    embedding.save_embedding(user_id, cover_letter)


class CoverLetterService:
    def __init__(self,
                 repo: CoverLetterRepository,
                 db: Session):
        self.repo = repo
        self.db = db

    def create_cover_letter(self,
                            user_id: int,
                            request: CoverLetterAdditionRequest,
                            background_tasks: BackgroundTasks):
        cover_letter = CoverLetter(title=request.title, user_id=user_id)

        for item in request.items:
            cover_letter.items.append(
                CoverLetterItem(
                    question=item.question,
                    char_limit=item.char_limit,
                    content=item.content
                )
            )
        # cover_letter RDB 저장
        self.repo.save(cover_letter)
        # cover_letter vector DB 저장
        background_tasks.add_task(save_embedding_task, user_id, CoverLetterResponse.model_validate(cover_letter))
        return cover_letter.id

    def get_cover_letter(self, user_id: int, cover_letter_id) -> CoverLetterResponse:
        cover_letter = self.repo.find_by_id(cover_letter_id)
        if not cover_letter:
            raise ValueError('cover letter not found')
        if user_id != cover_letter.user_id:
            raise ValueError('403')
        return CoverLetterResponse.model_validate(cover_letter)

    def get_cover_letters(self, user_id: int, type: CoverLetterType) -> list[CoverLetterSimpleResponse]:
        cover_letters = self.repo.find_all_by_user_id(user_id, type)
        return [CoverLetterSimpleResponse.model_validate(cover_letter) for cover_letter in cover_letters]

    def remove_cover_letter(self, user_id: int, cover_letter_id: int) -> None:
        self.repo.delete_by_id(cover_letter_id)

    def edit_cover_letter(self, user_id: int, cover_letter_id: int, request: CoverLetterEditRequest) -> int:
        cover_letter = self.repo.find_by_id(cover_letter_id)
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover letter not found")
        if user_id != cover_letter.user_id:
            raise ValueError('403')
        # cover_letter 전체 수정
        cover_letter.title = request.title
        edit_item_dict = {item.id: item for item in request.items}
        for item in cover_letter.items:
            edit_item = edit_item_dict[item.id]
            item.question = edit_item.question
            item.content = edit_item.content
        self.db.commit()
        return cover_letter.id


def get_cover_letter_service(repo: CoverLetterRepository = Depends(get_cover_letter_repository),
                             db: Session = Depends(get_db)):
    return CoverLetterService(repo, db)
