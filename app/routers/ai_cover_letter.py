import uuid

from fastapi import APIRouter, Depends, BackgroundTasks
from starlette import status

from app.core.security import get_current_user_id
from app.models.cover_letter import CoverLetterType
from app.schemas.ai_cover_letter import AiCoverLetterGenerationRequest
from app.services.ai_cover_letter_service import AiCoverLetterService, get_ai_cover_letter_service

router = APIRouter(
    prefix='/api/cover-letters',
    tags=['ai-cover-letters']
)


@router.post('/ai', status_code=status.HTTP_201_CREATED)
async def generate_ai_cover_letter(request: AiCoverLetterGenerationRequest,
                                   user_id: int = Depends(get_current_user_id),
                                   service: AiCoverLetterService = Depends(get_ai_cover_letter_service)) -> int:
    return service.generate_ai_cover_letter(user_id, request)


@router.patch('/{cover_letter_id}/type', status_code=status.HTTP_201_CREATED)
async def convert_cover_letter_type(cover_letter_id: int,
                                    background_tasks: BackgroundTasks,
                                    user_id: int = Depends(get_current_user_id),
                                    service: AiCoverLetterService = Depends(get_ai_cover_letter_service)):
    cover_letter_type = CoverLetterType.USER
    service.convert_type(user_id, cover_letter_id, cover_letter_type, background_tasks)
