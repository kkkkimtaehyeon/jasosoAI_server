import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi import Request
from pydantic import BaseModel
from starlette import status

from app.core.security import create_session
from app.schemas.user import UserCredentials, UserDetailResponse
from app.services.user_service import get_user_service, UserService

router = APIRouter()

# Google Cloud Console에서 얻은 클라이언트 ID
GOOGLE_CLIENT_ID = "973959640180-ku3hg81hm46rp49k00i7i7tsjfl99gue.apps.googleusercontent.com"
# Google Cloud Console에서 설정한 리디렉션 URI
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"


class Token(BaseModel):
    token: str


@router.post("/auth/google/login", status_code=status.HTTP_200_OK, response_model=UserDetailResponse)
async def google_login(request: Request,
                       token: Token,
                       service: UserService = Depends(get_user_service)):
    try:
        # Google API를 통해 액세스 토큰으로 사용자 정보 가져오기
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token.token}"}
            )
            response.raise_for_status()
            user_info = response.json()

        # 유저 정보를 기반으로 DB에 저장 또는 업데이트
        oauth_id = user_info['id']
        email = user_info['email']
        name = user_info['name']

        # 유저 DB 유무 확인
        user_detail = service.get_oauth_user(oauth_id, email, name)

        # 세션 생성
        create_session(request, UserCredentials(username=user_detail.id,
                                                email=user_detail.email,
                                                name=user_detail.name))
        return user_detail

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=400, detail=f"Google API Error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
