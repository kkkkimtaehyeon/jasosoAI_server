import os

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# from app.core.redis import init_redis, close_redis
from app.routers import user, cover_letter, ai_cover_letter, auth, feedback

_ = load_dotenv()
admin_id = os.getenv('ADMIN_ID')
admin_pw = os.getenv('ADMIN_PW')
sentry_dns = os.getenv('SENTRY_DNS')

origins = [
    "http://localhost:5173",  # 로컬 React
    "https://jasoso-ai.netlify.app",  # 실제 배포된 서비스
    "https://jasoso-ai.store",
    "https://www.jasoso-ai.store"

]
security = HTTPBasic()


def admin_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != admin_id or credentials.password != admin_pw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )


sentry_sdk.init(
    dsn=sentry_dns,
    send_default_pii=True,
)
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    # dependencies=[Depends(admin_auth)]  # 모든 Swagger 접근에 인증 적용
)
app.add_middleware(SessionMiddleware, secret_key='your_secret_key')
# 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처
    allow_credentials=True,  # 쿠키 포함 요청 허용 여부
    allow_methods=["*"],  # 허용할 메서드 (GET, POST 등)
    allow_headers=["*"],  # 허용할 헤더
)


# @app.on_event("startup")
# async def startup():
#     await init_redis()
#
#
# @app.on_event("shutdown")
# async def shutdown():
#     await close_redis()


app.include_router(user.router)
app.include_router(cover_letter.router)
app.include_router(ai_cover_letter.router)
app.include_router(auth.router)
app.include_router(feedback.router)


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
