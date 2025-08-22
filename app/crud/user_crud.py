from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.users import User


def create_user(db: Session, user: User) -> User:
    user.password = hash_password(user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def find_user_by_id(db: Session, user_id: int):
    pass


def find_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()
