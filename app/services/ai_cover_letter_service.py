from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import encrypt_text, decrypt_text
from app.models.cover_letter import CoverLetter, CoverLetterType
from app.models.cover_letter_item import CoverLetterItem
from app.models.users import User
from app.repositories.cover_letter import CoverLetterRepository, get_cover_letter_repository
from app.schemas.ai_cover_letter import AiCoverLetterGenerationRequest
from app.schemas.cover_letter import CoverLetterResponse
from app.services.cover_letter_service import save_embedding_task
from app.services.job_posting_service import JobPostingService, get_job_posting_service
from app.services.rag_service import generate_cover_letters
# from app.utils.api_limit_manager import get_gemini_api_limit_manager, ApiLimitManager
from app.utils.logging import logger

AI_COVER_LETTER_GENERATION_LIMIT = 5


class AiCoverLetterService:
    def __init__(self,
                 repo: CoverLetterRepository,
                 job_posting_service: JobPostingService,
                 db: Session):
        self.repo = repo
        self.job_posting_service = job_posting_service
        self.db = db

    async def generate_ai_cover_letter(self, user_id: int, request: AiCoverLetterGenerationRequest) -> int:
        # 유저가 업로드한 cover letter가 있는지 확인
        _check_user_uploaded_cover_letter(user_id, self.db)
        # AI 자소서 생성 횟수 확인
        _check_ai_cover_letter_limit(user_id, self.db)

        try:
            # 채용공고 가져오기
            job_posting = await self.job_posting_service.get_job_posting(request.job_posting_url)
            # 자소서 생성
            generated_items = await generate_cover_letters(user_id, job_posting, request.items)

            # DB 저장
            ai_cover_letter = CoverLetter(type=CoverLetterType.AI,
                                          title=f'{job_posting.company_name}-{job_posting.position_title}',
                                          user_id=user_id)
            ai_cover_letter.items = [
                CoverLetterItem(
                    question=item.question,
                    char_limit=item.char_limit,
                    content=encrypt_text(item.content)  # 내용 암호화
                ) for item in generated_items]
            self.repo.save(ai_cover_letter)
            # return
            return ai_cover_letter.id
        except Exception as e:
            logger.error(f"Error generating AI cover letter: {e}")
            raise HTTPException(status_code=500, detail={e})

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
        cover_letter_response = CoverLetterResponse.model_validate(cover_letter)
        for item in cover_letter_response.items:
            item.content = decrypt_text(item.content)
        background_tasks.add_task(save_embedding_task, user_id, cover_letter_response)


def _check_user_uploaded_cover_letter(user_id: int, db: Session):
    user_cover_letter_count = (db.query(CoverLetter)
                               .filter(CoverLetter.user_id == user_id,
                                       CoverLetter.type == CoverLetterType.USER)
                               .count())
    if user_cover_letter_count < 1:
        raise HTTPException(status_code=400, detail='at least one cover letter is required')


def _check_ai_cover_letter_limit(user_id: int, db: Session):
    ai_cover_letter_count = (db.query(CoverLetter)
                             .filter(CoverLetter.user_id == user_id, CoverLetter.type == CoverLetterType.AI)
                             .count())
    if ai_cover_letter_count > AI_COVER_LETTER_GENERATION_LIMIT:
        raise HTTPException(status_code=400, detail=f'AI 자소서는 하루에 최대 {AI_COVER_LETTER_GENERATION_LIMIT}번 생성할 수 있습니다.')


def get_ai_cover_letter_service(repo: CoverLetterRepository = Depends(get_cover_letter_repository),
                                job_posting_service: JobPostingService = Depends(get_job_posting_service),
                                db: Session = Depends(get_db)):
    return AiCoverLetterService(repo, job_posting_service,  db)
