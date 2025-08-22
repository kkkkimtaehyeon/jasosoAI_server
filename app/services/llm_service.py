import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import TypeAdapter

_ = load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

MODEL = "gemini-2.5-flash-lite"
gemini = genai.Client(api_key=GEMINI_API_KEY)


def get_cover_letter_generation_prompt(job_posting: JobPosting, references: list[str],
                                       item: CoverLetterItemGenerationRequest):
    prompt = f"""
    <job_posting>
        회사: {job_posting.company}
        직무: {job_posting.position_name}
        경력: {job_posting.experience}
        직무 상세: {job_posting.position_detail}
        요구 사항: {job_posting.requirements}
        우대 사항: {job_posting.preferred}
    </job_posting>

    <cover_letter_question>
    질문: {item.question} 
    글자 수 제한: {item.char_limit}
    </cover_letter_question>

    <retrieved_experiences>
    {"\n".join(references)}
    </retrieved_experiences>

    <instructions>
    너는 최고의 커리어 컨설턴트야.
    위의 <job_posting>과 <cover_letter_question>을 깊이 분석하고,
    <retrieved_experiences>에 담긴 나의 핵심 경험을 재료로 삼아서
    아래 작성 가이드라인에 맞춰 자소서를 작성해 줘.
    </instructions>

    <response_format>
    {{
        question: {item.question},
        char_limit: {item.char_limit},
        content: "생성한 내용" 
    }}
    </response_format>

    <guidelines>
    - STAR 기법을 활용할 것
    - 성과가 드러나도록 수치를 포함할 것
    - 채용공고의 인재상과 직무 역량을 연결할 것
    - {item.char_limit}자 내외로 작성할 것
    - **반드시 <retrieved_experiences>에 명시된 내용만을 기반으로 작성하고, 언급되지 않은 경험을 지어내지 말 것**
    - 반드시 <response_format>에 명시된 JSON 형식으로만 응답할 것
    </guidelines>

    """
    return prompt


def generate_cover_letter(job_posting, reference_dict, item) -> CoverLetterItem:
    prompt = get_cover_letter_generation_prompt(job_posting, reference_dict, item)
    response = gemini.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=GenerateContentConfig(
            response_schema=CoverLetterItem,
            response_mime_type="application/json"
        )
    )
    print(response.text)
    return TypeAdapter(CoverLetterItem).validate_json(response.text)
