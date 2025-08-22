import os
from typing import Union

from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import TypeAdapter

from app.schemas.job_posting import JobPostingAnalyzeResponse
from app.utils.job_posting_crawlers.job_posting_crawler_factory import JobPostingCrawlerFactory

WANTED = 'https://www.wanted.co.kr/'
JOBKOREA = 'https://www.jobkorea.co.kr/'
SARMIN = 'https://www.saramin.co.kr/'
ZIGHANG = 'https://zighang.com/'

_ = load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')

gemini = genai.Client(api_key=API_KEY)


def get_job_posting_analyze_prompt(raw_text: str) -> str:
    prompt = f"""
    너는 채용공고 분석 전문가야. 아래 채용공고에서 , 회사명, 직무명, 경력, 직무 상세, 요구 사항, 우대 사항을 추출해야 해.

    채용공고:
    {raw_text}

    반환 형식:
    {{
        "companyName": "회사명",
        "positionTitle": "직무명",
        "experience": "경력",
        "positionDetail": "직무 상세",
        "requiredQualifications": "요구 사항",
        "preferredQualifications": "우대 사항"
    }}
    """
    return prompt


def analyze_job_posting_from_text(raw_text: str) -> JobPostingAnalyzeResponse:
    prompt = get_job_posting_analyze_prompt(raw_text)
    contents = [prompt]

    response = gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=contents,
        config=GenerateContentConfig(
            response_schema=JobPostingAnalyzeResponse,
            response_mime_type="application/json"
        )
    )
    result = TypeAdapter(JobPostingAnalyzeResponse).validate_json(response.text)
    print(f'채용공고 분석 완료: {result}')
    return result


class JobPostingAnalyzeService:
    def __init__(self):
        pass

    def analyze_job_posting(self, job_posting_url: str) -> JobPostingAnalyzeResponse:
        # 1. 채용공고 크롤링
        crawler = JobPostingCrawlerFactory.get_crawler(job_posting_url)
        raw_data = crawler.crawl(job_posting_url)
        print(f'크롤링 완료: {raw_data}')
        # 2. llm으로 채용공고 분석
        return analyze_job_posting_from_text(raw_data)


def get_job_posting_analyze_service() -> JobPostingAnalyzeService:
    return JobPostingAnalyzeService()
