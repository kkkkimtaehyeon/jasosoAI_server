from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.database import create_db_tables
from app.routers import user, cover_letter, ai_cover_letter, auth

origins = [
    "http://localhost:5173",  # 로컬 React
    "https://myfrontend.com",  # 실제 배포된 서비스
]
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your_secret_key')
# 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처
    allow_credentials=True,  # 쿠키 포함 요청 허용 여부
    allow_methods=["*"],  # 허용할 메서드 (GET, POST 등)
    allow_headers=["*"],  # 허용할 헤더
)


@app.on_event('startup')
def on_startup():
    create_db_tables()


app.include_router(user.router)
app.include_router(cover_letter.router)
app.include_router(ai_cover_letter.router)
app.include_router(auth.router)
