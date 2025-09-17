from datetime import datetime, timezone

from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import encrypt_text, decrypt_text
from app.models.cover_letter import CoverLetter, CoverLetterType
from app.models.cover_letter_item import CoverLetterItem
from app.repositories.cover_letter import CoverLetterRepository, get_cover_letter_repository
from app.schemas.cover_letter import CoverLetterAdditionRequest, CoverLetterResponse, CoverLetterSimpleResponse, \
    CoverLetterEditRequest, CoverLetterItemResponse
from app.utils import embedding
# from app.utils.api_limit_manager import get_gemini_api_limit_manager, ApiLimitManager
from app.utils.embedding import delete_embedding


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
            # 내용 암호화
            encrypted_content = encrypt_text(item.content)
            cover_letter.items.append(
                CoverLetterItem(
                    question=item.question,
                    char_limit=item.char_limit,
                    content=encrypted_content
                )
            )
        # cover_letter RDB 저장
        self.repo.save(cover_letter)
        # cover_letter vector DB 저장
        cover_letter_response = CoverLetterResponse.model_validate(cover_letter)
        cover_letter_response.items = [
            CoverLetterItemResponse(
                id=item.id,
                question=item.question,
                char_limit=item.char_limit,
                content=decrypt_text(item.content)  # content만 복호화
            )
            for item in cover_letter_response.items
        ]

        background_tasks.add_task(save_embedding_task, user_id, cover_letter_response)
        return cover_letter.id

    def get_cover_letter(self, user_id: int, cover_letter_id) -> CoverLetterResponse:
        cover_letter = self.repo.find_by_id(cover_letter_id)

        if not cover_letter:
            raise ValueError('cover letter not found')
        if user_id != cover_letter.user_id:
            raise ValueError('403')
        cover_letter_response = CoverLetterResponse.model_validate(cover_letter)
        for item in cover_letter_response.items:
            item.content = decrypt_text(item.content)
        return cover_letter_response

    def get_cover_letters(self, user_id: int, type: CoverLetterType) -> list[CoverLetterSimpleResponse]:
        cover_letters = self.repo.find_all_by_user_id(user_id, type)
        return [CoverLetterSimpleResponse.model_validate(cover_letter) for cover_letter in cover_letters]

    def remove_cover_letter(self, user_id: int, cover_letter_id: int, background_tasks: BackgroundTasks) -> None:
        cover_letter = self.db.get(CoverLetter, cover_letter_id)
        if cover_letter is not None:
            # 유저 권한 검증
            if user_id != cover_letter.user_id:
                raise HTTPException(status_code=403, detail="권한이 없는 유저입니다.")
            # soft delete
            now = datetime.now(timezone.utc)
            cover_letter.deleted_at = now
            for item in cover_letter.items:
                item.deleted_at = now
            self.db.commit()
        # vectorstore에서 embedding 삭제
        background_tasks.add_task(delete_embedding, user_id, cover_letter_id)

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
