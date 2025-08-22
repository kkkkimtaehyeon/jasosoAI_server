from _datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CoverLetterItemAdditionRequest(BaseModel):
    question: str
    char_limit: int
    content: str


class CoverLetterAdditionRequest(BaseModel):
    title: str
    items: list[CoverLetterItemAdditionRequest]


class CoverLetterItemDto(BaseModel):
    question: str
    char_limit: int
    content: str


class CoverLetterItemResponse(BaseModel):
    id: int
    question: str
    char_limit: int
    content: str

    class Config:
        from_attributes = True


class CoverLetterResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    items: list[CoverLetterItemResponse]

    class Config:
        from_attributes = True


class CoverLetterSimpleResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class CoverLetterItemEditRequest(BaseModel):
    id: int
    question: str
    char_limit: int
    content: str


class CoverLetterEditRequest(BaseModel):
    title: str
    items: list[CoverLetterItemEditRequest]
