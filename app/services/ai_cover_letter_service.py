from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cover_letter import CoverLetter, CoverLetterType
from app.models.cover_letter_item import CoverLetterItem
from app.models.users import User
from app.repositories.cover_letter import CoverLetterRepository, get_cover_letter_repository
from app.schemas.ai_cover_letter import AiCoverLetterGenerationRequest
from app.schemas.cover_letter import CoverLetterResponse
from app.services.cover_letter_service import save_embedding_task
from app.services.job_posting_service import JobPostingService, get_job_posting_service
from app.services.rag_service import generate_cover_letters


class AiCoverLetterService:
    def __init__(self,
                 repo: CoverLetterRepository,
                 job_posting_service: JobPostingService,
                 db: Session):
        self.repo = repo
        self.job_posting_service = job_posting_service
        self.db = db

    def generate_ai_cover_letter(self, user_id: int, request: AiCoverLetterGenerationRequest) -> int:
        # 채용공고 가져오기
        job_posting = self.job_posting_service.get_job_posting(request.job_posting_url)
        # 자소서 생성
        generated_items = generate_cover_letters(user_id, job_posting, request.items)

        # DB 저장
        ai_cover_letter = CoverLetter(type=CoverLetterType.AI,
                                      title=f'{job_posting.company_name}-{job_posting.position_title}',
                                      user_id=user_id)
        ai_cover_letter.items = [CoverLetterItem(**dto.model_dump()) for dto in generated_items]
        self.repo.save(ai_cover_letter)
        # return
        return ai_cover_letter.id

    def convert_type(self, user_id, cover_letter_id, type, background_tasks: BackgroundTasks):
        # 유저 검증
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        # 타입 변경 (ai -> user)
        cover_letter = self.repo.find_by_id(cover_letter_id)
        if cover_letter.user_id != user.id:
            raise HTTPException(status_code=401, detail='Unauthorized')
        cover_letter.type = type
        self.db.commit()
        # 임베딩 vector db 저장
        background_tasks.add_task(save_embedding_task, user_id, CoverLetterResponse.model_validate(cover_letter))


def get_ai_cover_letter_service(repo: CoverLetterRepository = Depends(get_cover_letter_repository),
                                job_posting_service: JobPostingService = Depends(get_job_posting_service),
                                db: Session = Depends(get_db)):
    return AiCoverLetterService(repo, job_posting_service, db)
