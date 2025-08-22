import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import TypeAdapter

from app.core.vectorstore import get_vectorstore
from app.models.job_posting import JobPosting
from app.schemas.ai_cover_letter import AiCoverLetterItemGenerationRequest, VectorDbQuery
from app.schemas.cover_letter import CoverLetterItemDto

_ = load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

gemini = genai.Client(api_key=GEMINI_API_KEY)


def _get_search_query_prompt(job_posting: JobPosting, items: list[AiCoverLetterItemGenerationRequest]):
    # 여러 개의 CoverLetterItem을 하나의 문자열로 결합
    cover_letter_items_text = "\n".join([
        f"- 항목 고유 식별자 (ID) = {item.id}\n- 항목 질문 (Question) = {item.question}" for item in items
    ])

    template = f"""
        너는 벡터 데이터베이스 검색 질의를 생성하는 데 도움을 주는 유용한 AI야.
        주어진 채용 공고를 바탕으로, 각 항목과 관련된 검색 질의를 한글로 생성해줘.

        ---

        채용 공고:
        회사: {job_posting.company_name}
        직무: {job_posting.position_title}
        경력: {job_posting.experience}
        직무 상세: {job_posting.position_detail}
        요구 사항: {job_posting.required_qualifications}
        우대 사항: {job_posting.preferred_qualifications}

        ---

        자기소개서 항목들:
        {cover_letter_items_text}

        ---

        위에 제시된 자기소개서 항목의 개수만큼, 각 항목의 고유 식별자(ID)와 채용 공고를 모두 고려한 검색 질의를 생성해줘.
        아래와 같은 JSON list 형식으로 무조건 응답 해.
    
        [
            {{
                "id": "항목의 고유 식별자(ID)",
                "query": "생성한 질의"
            }}
        ]
        """

    return template


def generate_search_query(job_posting: JobPosting,
                          items: list[AiCoverLetterItemGenerationRequest]) -> list[VectorDbQuery]:
    prompt = _get_search_query_prompt(job_posting, items)
    response = gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=GenerateContentConfig(
            response_schema=list[VectorDbQuery],
            response_mime_type="application/json"
        )
    )
    print(f'검색쿼리 생성 완료: {response.text}')
    return TypeAdapter(list[VectorDbQuery]).validate_json(response.text)


def get_cover_letter_generation_prompt(job_posting: JobPosting, references: list[str],
                                       item: AiCoverLetterItemGenerationRequest):
    prompt = f"""
    <job_posting>
        회사: {job_posting.company_name}
        직무: {job_posting.position_title}
        경력: {job_posting.experience}
        직무 상세: {job_posting.position_detail}
        요구 사항: {job_posting.required_qualifications}
        우대 사항: {job_posting.preferred_qualifications}
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


# 참조할 자소서 내용 검색
def retrieve_reference_cover_letters(user_id: int,
                                     job_posting: JobPosting,
                                     items: list[AiCoverLetterItemGenerationRequest]) -> dict[str, list[str]]:
    references = {}
    # 검색 쿼리 생성
    search_queries = generate_search_query(job_posting, items)
    vectorstore = get_vectorstore(user_id)
    # 쿼리로 references 검색
    for query in search_queries:
        search_results = vectorstore.similarity_search(query=query.query, k=3)
        references[query.id] = [doc.page_content for doc in search_results]

    print(f'참조 자소서 검색 완료: {references}')
    return references


# 자소서 항목 생성
def generate_cover_letter(job_posting, references, item) -> CoverLetterItemDto:
    prompt = get_cover_letter_generation_prompt(job_posting, references, item)
    response = gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=GenerateContentConfig(
            response_schema=CoverLetterItemDto,
            response_mime_type="application/json"
        )
    )
    print(response.text)
    return TypeAdapter(CoverLetterItemDto).validate_json(response.text)


# rag 수행 (검색 + 생성)
def generate_cover_letters(user_id: int,
                           job_posting: JobPosting,
                           items: list[AiCoverLetterItemGenerationRequest]) -> list[CoverLetterItemDto]:
    cover_letter_items = []
    references_dict = retrieve_reference_cover_letters(user_id, job_posting, items)
    for item in items:
        references = references_dict[item.id]
        generated_item = generate_cover_letter(job_posting, references, item)
        cover_letter_items.append(generated_item)
    print(f'자기소개서 생성 완료: {cover_letter_items}')
    return cover_letter_items
