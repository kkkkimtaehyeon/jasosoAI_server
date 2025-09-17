# 시간이 좀 걸려도 괜찮은 작업
# 1. 요청을 우선 큐에 넣음
# 2. 429 에러 시 retryDelay만큼 sleep
# 3. sleep 끝나면 다시 요청 처리
# 내 서비스의 gemini-api 호출 횟수
# /generate
# 채용공고 분석 - 1회, 이미 분석된 채용공고이면 - 0회
# 자소서 검색 쿼리 생성 - 1회
# 자소서 항목 n개 생성 - n회
# 동적 세마포어 - 큐에 task 개수에 따라 동적으로 세마포어 크기 조절
# 세마포어는 동시에 많은 요청이 들어오는 것을 막아줌


import asyncio
import logging
from asyncio import Queue

import httpx
import uvicorn
from fastapi import FastAPI, APIRouter
from tenacity import retry, retry_if_exception_type, before_sleep_log, stop_after_attempt, stop_after_delay
from tenacity.wait import wait_base, wait_exponential, wait_random

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    def __init__(self, msg, retry_after=None):
        super().__init__(msg)
        self.retry_after = retry_after


MAX_CONCURRENT_REQUESTS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # 동시에 최대 5개의 요청만 처리

app = FastAPI()
router = APIRouter()

# -------------------------------
# 큐 정의 (전역)
# -------------------------------
task_queue: Queue = Queue()


@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=(stop_after_attempt(6) & stop_after_delay(60)),
    wait=wait_exponential(multiplier=1, min=1, max=30) + wait_random(0, 2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def call_gemini():
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/generate")
        if res.status_code == 429:
            raise RateLimitError(f"Rate limit exceeded. retry...")


async def analyze_job_posting():
    await call_gemini()


async def generate_search_query():
    await call_gemini()


async def generate_cover_letter_items(n: int):
    tasks = [call_gemini() for _ in range(n)]
    await asyncio.gather(*tasks)


counter = 0


async def do_work_flow(items: int):
    global counter
    counter += 1
    try:
        print(f'워크 플로우{counter} 시작')
        await analyze_job_posting()
        await generate_search_query()
        await generate_cover_letter_items(items)
        print(f'워크 플로우{counter} 완료')
    except RateLimitError:
        raise Exception("워크 플로우 실패, 재큐 필요")
        # TODO: 실패 시 다시 큐에 넣어주기
        # await task_queue.put((do_work_flow, items))


# -------------------------------
# Worker 정의
# -------------------------------
async def worker(worker_id: int):
    while True:
        func, arg = await task_queue.get()
        try:
            await func(arg)
        except Exception as e:
            logger.error(f"[Worker {worker_id}] 작업 실패: {e}")
        finally:
            task_queue.task_done()


# -------------------------------
# API 엔드포인트
# -------------------------------
@router.post("/start-workflow/{items}")
async def start_workflow(items: int):
    await task_queue.put((do_work_flow, items))
    return {"message": f"{items}개 아이템 워크플로우 작업이 큐에 등록되었습니다."}


app.include_router(router)


# -------------------------------
# 앱 시작 시 Worker 실행
# -------------------------------
@app.on_event("startup")
async def startup_event():
    for i in range(5):  # 워커 3개 실행
        asyncio.create_task(worker(i))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
