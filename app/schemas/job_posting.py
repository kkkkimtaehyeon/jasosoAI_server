from pydantic import BaseModel, Field


class JobPostingAnalyzeResponse(BaseModel):
    # url: str = Field(..., alias='url')
    company: str = Field(..., alias='companyName')
    position_name: str = Field(..., alias='positionTitle')
    position_detail: str = Field(..., alias='positionDetail')
    experience: str = Field(..., alias='experience')
    requirements: str = Field(..., alias='requiredQualifications')
    preferred: str = Field(..., alias='preferredQualifications')

    class Config:
        populate_by_name = True