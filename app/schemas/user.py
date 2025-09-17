from pydantic import BaseModel, EmailStr, constr


class UserCredentials(BaseModel):
    username: int
    email: str
    name: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=16)


class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    name: constr(min_length=2, max_length=20)


class UserDetailResponse(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        # Pydantic 2.x에서 ORM 모드를 활성화하는 새로운 방식
        # SQLAlchemy 객체에서 Pydantic 모델로 데이터 변환을 허용
        from_attributes = True
