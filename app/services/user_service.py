import uuid

from fastapi import Depends

from app.core.security import verify_password
from app.models.users import User
from app.repositories.user import UserRepositoryInterface, get_user_repository
from app.schemas.user import UserRegistrationRequest, UserDetailResponse, UserLoginRequest


class UserService:
    def __init__(self, repo: UserRepositoryInterface):
        self.repo = repo

    def register_user(self, request: UserRegistrationRequest) -> int:
        if self.repo.find_user_by_email(request.email):
            raise ValueError('이미 존재하는 이메일입니다.')
        user = User(email=request.email,
                    password=request.password,
                    name=request.name)
        self.repo.save_user(user)
        return user.id

    def get_oauth_user(self, oauth_id: str, email: str, name: str) -> UserDetailResponse:
        user = self.repo.find_user_by_oauth_id(oauth_id)
        if not user:
            password = str(uuid.uuid4())
            user = User(
                email=email,
                password=password,
                name=name,
                oauth_id=oauth_id)
            self.repo.save_user(user)
        return UserDetailResponse.model_validate(user)

    def get_user(self, user_id: int) -> UserDetailResponse:
        user = self.repo.find_user_by_id(user_id)
        if user is None:
            raise ValueError('존재하지 않는 유저입니다.')
        return UserDetailResponse.model_validate(user)

    def authenticate_user(self, request: UserLoginRequest) -> int:
        user = self.repo.find_user_by_email(request.email)
        if user is None:
            raise ValueError('잘못된 이메일 혹은 비밀번호')
        if not verify_password(plain_password=request.password,
                               hashed_password=user.password):
            raise ValueError('잘못된 이메일 혹은 비밀번호')
        return user.id


def get_user_service(repo: UserRepositoryInterface = Depends(get_user_repository)):
    return UserService(repo)
