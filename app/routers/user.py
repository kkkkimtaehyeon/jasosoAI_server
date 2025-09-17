from fastapi import APIRouter, Depends, Request
from starlette import status

from app.core.security import clear_session
from app.schemas.user import UserRegistrationRequest
from app.services.user_service import get_user_service, UserService

router = APIRouter(
    prefix='/api/users',
    tags=['users']
)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(request: UserRegistrationRequest,
                      service: UserService = Depends(get_user_service)):
    return service.register_user(request)


@router.get('/{user_id}', status_code=status.HTTP_200_OK)
async def get_user(user_id: int,
                   service: UserService = Depends(get_user_service)):
    return service.get_user(user_id)


# @router.post('/login', status_code=status.HTTP_200_OK)
# async def user_login(request: Request,
#                      login_request: UserLoginRequest,
#                      service: UserService = Depends(get_user_service)):
#     try:
#         user_id = service.authenticate_user(login_request)
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=str(e)
#         )
#     create_session(request, UserCredentials(username=user_id))


@router.post('/logout', status_code=status.HTTP_200_OK)
async def user_logout(request: Request):
    clear_session(request)
