from typing import Type

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.users import User


class UserRepositoryInterface:
    def find_user_by_id(self, id: int) -> User:
        pass

    def find_user_by_email(self, email: str) -> User:
        pass

    def save_user(self, user: User) -> User:
        pass

    def find_user_by_oauth_id(self, oauth_id) -> User:
        pass


class UserRepository(UserRepositoryInterface):
    def __init__(self, db: Session):
        self.db = db

    def find_user_by_id(self, id: int) -> Type[User] | None:
        return self.db.get(User, id)

    def find_user_by_oauth_id(self, oauth_id: str) -> Type[User] | None:
        query = self.db.query(User).filter(User.oauth_id == oauth_id)
        user = query.first()
        return user

    def find_user_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    def save_user(self, user: User) -> User:
        user.password = hash_password(user.password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


def get_user_repository(db: Session = Depends(get_db)) -> UserRepositoryInterface:
    return UserRepository(db)
