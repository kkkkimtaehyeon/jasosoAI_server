from pydantic import BaseModel


class FeedbackCreationRequest(BaseModel):
    content: str
