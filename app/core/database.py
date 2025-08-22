# app/core/database.py
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# 환경 변수에서 DB URL 가져오기
_ = load_dotenv()
DATABASE_URL = os.getenv("DB_URL")

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결이 살아있는지 확인
)

# 세션 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모델에서 상속받아서 사용)
Base = declarative_base()


# 의존성 함수
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_tables():
    Base.metadata.create_all(bind=engine)
