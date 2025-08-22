from pydantic import BaseModel


class AiCoverLetterItemGenerationRequest(BaseModel):
    id: str
    question: str
    char_limit: int


class AiCoverLetterGenerationRequest(BaseModel):
    job_posting_url: str
    items: list[AiCoverLetterItemGenerationRequest]


class VectorDbQuery(BaseModel):
    id: str
    query: str

