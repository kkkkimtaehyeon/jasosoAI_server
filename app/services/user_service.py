import uuid

from fastapi import Depends, HTTPException

from app.core.security import encrypt_text
from app.models.users import User
from app.repositories.user import UserRepositoryInterface, get_user_repository
from app.schemas.user import UserRegistrationRequest, UserDetailResponse
from app.utils.logging import logger


class UserService:
    def __init__(self, repo: UserRepositoryInterface):
        self.repo = repo

    def register_user(self, request: UserRegistrationRequest) -> int:
        if self.repo.find_user_by_email(request.email):
            raise HTTPException(status_code=400, detail='이미 사용중인 이메일입니다.')
            logger.error(f'duplicated email: {request.email}')
        user = User(email=request.email,
                    password=request.password,
                    name=request.name)
        self.repo.save_user(user)
        logger.info(f'Created new user: {request.email}')
        return user.id

    def get_oauth_user(self, oauth_id: str, email: str, name: str, oauth_provider: str) -> UserDetailResponse:
        user = self.repo.find_user_by_oauth_id(oauth_id)
        if not user:
            password = str(uuid.uuid4())
            user = User(
                email=encrypt_text(email),
                password=password,
                name=name,
                oauth_id=oauth_id,
                oauth_provider=oauth_provider)
            self.repo.save_user(user)
            logger.info(f'Created new OAuth user: {email}')

        return UserDetailResponse.model_validate(user)

    def get_user(self, user_id: int) -> UserDetailResponse:
        user = self.repo.find_user_by_id(user_id)
        if user is None:
            raise ValueError('존재하지 않는 유저입니다.')
        return UserDetailResponse.model_validate(user)


def get_user_service(repo: UserRepositoryInterface = Depends(get_user_repository)):
    return UserService(repo)
