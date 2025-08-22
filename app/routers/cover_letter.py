from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from starlette import status

from app.core.security import get_current_user_id, get_current_user
from app.models.cover_letter import CoverLetterType
from app.models.users import User
from app.schemas.cover_letter import CoverLetterAdditionRequest, CoverLetterSimpleResponse, CoverLetterResponse, \
    CoverLetterEditRequest
from app.services.cover_letter_service import CoverLetterService, get_cover_letter_service

router = APIRouter(
    prefix='/api/cover-letters',
    tags=['cover-letters']
)


@router.post('/user', status_code=status.HTTP_201_CREATED)
async def add_cover_letter(request: CoverLetterAdditionRequest,
                           background_tasks: BackgroundTasks,
                           user_id: int = Depends(get_current_user_id),
                           user: User = Depends(get_current_user),
                           service: CoverLetterService = Depends(get_cover_letter_service)):
    try:
        cover_letter_id = service.create_cover_letter(user.id, request, background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return cover_letter_id


@router.get('', status_code=status.HTTP_200_OK, response_model=list[CoverLetterSimpleResponse])
async def get_cover_letters(type: Optional[CoverLetterType] = CoverLetterType.USER,
                            user: User = Depends(get_current_user),
                            service: CoverLetterService = Depends(get_cover_letter_service)) -> list[
    CoverLetterSimpleResponse]:
    cover_letters = service.get_cover_letters(user.id, type)
    return cover_letters


@router.get('/{cover_letter_id}', status_code=status.HTTP_200_OK, response_model=CoverLetterResponse)
async def get_cover_letter(cover_letter_id: int,
                           user: User = Depends(get_current_user),
                           service: CoverLetterService = Depends(get_cover_letter_service)) -> CoverLetterResponse:
    cover_letter = service.get_cover_letter(user.id, cover_letter_id)
    return cover_letter


@router.patch('/{cover_letter_id}', status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def update_cover_letter(cover_letter_id: int,
                              request: CoverLetterEditRequest,
                              user: User = Depends(get_current_user),
                              service: CoverLetterService = Depends(get_cover_letter_service)) -> None:
    service.edit_cover_letter(user.id, cover_letter_id, request)


@router.delete('/{cover_letter_id}', status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_cover_letter(cover_letter_id: int,
                              user: User = Depends(get_current_user),
                              service: CoverLetterService = Depends(get_cover_letter_service)) -> None:
    service.remove_cover_letter(user.id, cover_letter_id)
