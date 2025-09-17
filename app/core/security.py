import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from app.core.database import get_db
from app.models.users import User
from app.schemas.user import UserCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_session(request: Request, user_credentials: UserCredentials) -> None:
    dict_value = {'username': user_credentials.username}
    request.session['user'] = dict_value


def get_current_user_id(request: Request) -> int:
    user_session = request.session.get('user', None)
    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str('로그인이 필요한 서비스입니다.')
        )

    return user_session.get('username')


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_session = request.session.get('user', None)
    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str('로그인이 필요한 서비스입니다.')
        )
    user_id = user_session.get('username')
    user = db.get(User, user_id)
    if not user:
        raise ValueError('user not found')
    # 유저 밴
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str('차단된 사용자입니다.'),
        )
    return user


def clear_session(request: Request) -> None:
    if request.session:
        request.session.clear()


_ = load_dotenv()
TEXT_ENCRYPT_SECRET_KEY = os.getenv('TEXT_ENCRYPT_SECRET_KEY')
fernet = Fernet(TEXT_ENCRYPT_SECRET_KEY)


def encrypt_text(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_text(cipher_text: str) -> str:
    return fernet.decrypt(cipher_text.encode()).decode()
