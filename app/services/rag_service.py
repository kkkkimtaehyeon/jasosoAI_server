import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import TypeAdapter

from app.core.vectorstore import get_vectorstore
from app.models.job_posting import JobPosting
from app.schemas.ai_cover_letter import AiCoverLetterItemGenerationRequest, VectorDbQuery
from app.schemas.cover_letter import CoverLetterItemDto
from app.services.gemini_service import generate_content

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


def _get_search_query_prompt_v2(job_posting: JobPosting, items: list[AiCoverLetterItemGenerationRequest]):
    cover_letter_items_text = "\n".join([
        f"- 항목 ID: {item.id}\n- 항목 질문: {item.question}" for item in items
    ])

    template = f"""
        너는 지원자의 과거 경험 라이브러리(벡터 DB)에서, 특정 채용 공고와 자기소개서 질문에 가장 적합한 경험을 찾아내기 위한 '최적의 검색 쿼리'를 설계하는 AI 전략가야.

        **[너의 임무]**
        주어진 <채용 공고>와 <자기소개서 항목들>을 깊이 분석해서, 각 항목에 대한 최적의 검색 쿼리를 생성해야 해.
        생성된 쿼리의 목표는, 지원자의 경험들 중에서 아래 기준을 만족하는 가장 강력한 사례를 찾아내는 것이야:
        1. 채용 공고의 직무(position_title)와 요구 역량(required_qualifications)에 직접적으로 관련된 경험
        2. 지원자의 문제 해결 능력, 구체적인 성과, 또는 성장 과정이 잘 드러나는 경험

        ---

        **<채용 공고>**
        - 회사: {job_posting.company_name}
        - 직무: {job_posting.position_title}
        - 직무 상세: {job_posting.position_detail}
        - 요구 사항: {job_posting.required_qualifications}
        - 우대 사항: {job_posting.preferred_qualifications}

        ---

        **<자기소개서 항목들>**
        {cover_letter_items_text}

        ---

        **[쿼리 생성 가이드라인]**
        1. **분석:** 먼저, 각 자기소개서 항목 질문의 핵심 의도(예: 협업 능력, 주도성, 기술 이해도)를 파악해.
        2. **연결:** 그 다음, 채용 공고의 '직무 상세'와 '요구 사항'에서 핵심 키워드와 역량을 추출해.
        3. **융합:** 마지막으로, 질문의 의도와 공고의 핵심 역량을 자연스럽게 **융합**하여 검색 쿼리를 만들어. 단순한 단어 조합이 아니라, "어떤 상황에서 어떤 기술을 사용해 어떤 문제를 해결한 경험"과 같이 구체적인 시나리오 형태의 쿼리를 생성해야 해.

        **[쿼리 예시]**
        - (나쁜 쿼리): "프로젝트 경험"
        - (좋은 쿼리): "Python과 TensorFlow를 사용하여 추천 시스템의 정확도를 10% 이상 개선한 프로젝트 경험, 데이터 전처리부터 모델 평가까지 주도적으로 참여한 사례"

        ---

        위에 제시된 <자기소개서 항목들>의 개수만큼, 각 항목의 ID와 위 가이드라인에 따라 생성한 검색 쿼리를 아래 JSON list 형식으로만 응답해줘.

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
    prompt = _get_search_query_prompt_v2(job_posting, items)
    response = gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=GenerateContentConfig(
            response_schema=list[VectorDbQuery],
            response_mime_type="application/json"
        )
    )
    # print(f'검색쿼리 생성 완료: {response.text}')
    return TypeAdapter(list[VectorDbQuery]).validate_json(response.text)


async def generate_search_query2(job_posting: JobPosting,
                                 items: list[AiCoverLetterItemGenerationRequest]) -> list[VectorDbQuery]:
    prompt = _get_search_query_prompt_v2(job_posting, items)
    return await generate_content(prompt, list[VectorDbQuery])


def get_cover_letter_generation_prompt(job_posting: JobPosting, references: list[str],
                                       item: AiCoverLetterItemGenerationRequest) -> str:
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
    - 너는 지원자의 경험을 깊이 이해하고, 지원 직무와 회사의 인재상에 맞춰 매력적인 스토리를 만드는 최고의 자소서 컨설턴트야.
    - **(매우 중요) STAR 기법(Situation, Task, Action, Result)의 논리적 흐름에 따라 스토리를 구성하되, '[Situation]', '[Task]', '[Action]', '[Result]' 같은 소제목이나 태그는 절대 글에 포함하지 마.** 경험이 하나의 자연스러운 이야기처럼 매끄럽게 읽혀야 해.
    
    - **[문체 및 어조]**
      - 지원자의 **열정과 전문성**이 동시에 느껴지는 진정성 있는 어투를 사용해 줘.
      - '...을 통해 역량을 길렀습니다' 같은 상투적이고 수동적인 표현 대신, **'어떤 문제를 어떻게 해결했고, 그 결과 어떤 임팩트를 만들었습니다'** 와 같이 자신감 있고 능동적인 문장으로 작성해 줘.
      - AI가 쓴 것처럼 딱딱하거나 일반적인 표현(예: '노력했습니다', '배웠습니다')은 최대한 피하고, 지원자가 직접 깊이 고민해서 쓴 것처럼 독창적이고 구체적인 표현을 사용해 줘.
    
    - **[내용 구성]**
      - `<job_posting>`의 직무 상세, 요구 사항, 우대 사항에 언급된 **핵심 키워드**를 자연스럽게 문장에 녹여내어, 내가 이 직무에 얼마나 적합한 인재인지 명확히 보여줘.
      - 나의 경험(`<retrieved_experiences>`)이 지원하는 회사의 비전이나 목표와 어떻게 연결되는지 서두나 말미에 언급하여 **회사에 대한 관심과 이해도**를 어필해 줘.
      - 성과를 보여줄 수 있는 부분은 **수치를 활용**하여 구체적인 임팩트를 강조해 줘. 만약 명확한 수치가 없다면, '정성적 성과'(예: 팀원들의 긍정적 피드백, 문제 해결 프로세스 정립)라도 구체적으로 묘사해 줘.
    
    - **[제약 조건]**
      - {item.char_limit}자 내외로 분량을 맞춰줘.
      - **반드시 <retrieved_experiences>에 명시된 내용만을 기반으로 작성하고, 언급되지 않은 경험은 절대로 지어내지 마.**
      - 반드시 <response_format>에 명시된 JSON 형식으로만 응답할 것. 마크다운 형식이나 추가 설명은 포함하지 마.  
    </guidelines>

    """
    return prompt


# 참조할 자소서 내용 검색
async def retrieve_reference_cover_letters(user_id: int,
                                     job_posting: JobPosting,
                                     items: list[AiCoverLetterItemGenerationRequest]) -> dict[str, list[str]]:
    try:
        references = {}
        # 검색 쿼리 생성
        search_queries = await generate_search_query2(job_posting, items)
        vectorstore = get_vectorstore(user_id)
        # 쿼리로 references 검색
        for query in search_queries:
            search_results = vectorstore.similarity_search(query=query.query, k=3)
            references[query.id] = [doc.page_content for doc in search_results]

        # print(f'참조 자소서 검색 완료: {references}')
        return references
    except Exception as e:
        print(f'참조 자소서 검색 중 에러 발생: {e}')
        raise e


# 자소서 항목 생성
async def generate_cover_letter(job_posting, references, item) -> CoverLetterItemDto:
    prompt = get_cover_letter_generation_prompt(job_posting, references, item)
    response = await gemini.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=GenerateContentConfig(
            response_schema=CoverLetterItemDto,
            response_mime_type="application/json"
        )
    )
    # print(response.text)
    return TypeAdapter(CoverLetterItemDto).validate_json(response.text)


# retry를 적용한 응답 생선 적용 버전
async def generate_cover_letter2(job_posting, references, item) -> CoverLetterItemDto:
    prompt = get_cover_letter_generation_prompt(job_posting, references, item)
    return await generate_content(prompt, CoverLetterItemDto)  # 리스트로 감싸서 전달


# rag 수행 (검색 + 생성)
async def generate_cover_letters(user_id: int,
                                 job_posting: JobPosting,
                                 items: list[AiCoverLetterItemGenerationRequest]) -> list[CoverLetterItemDto]:
    references_dict = await retrieve_reference_cover_letters(user_id, job_posting, items)

    async def generate_one(item):
        references = references_dict[item.id]
        return await generate_cover_letter2(job_posting, references, item)

    tasks = [generate_one(item) for item in items]
    cover_letter_items = await asyncio.gather(*tasks)
    return cover_letter_items
