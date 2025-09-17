#
# import asyncio
# import logging
# import time
# from asyncio import Queue
# from typing import Dict, Optional
#
# import httpx
# import uvicorn
# from fastapi import FastAPI, APIRouter
# from tenacity import retry, retry_if_exception_type, before_sleep_log
# from tenacity.wait import wait_base
#
# logger = logging.getLogger(__name__)
#
# # 성능 측정을 위한 글로벌 변수들
# performance_tracker = {
#     "start_time": None,
#     "end_time": None,
#     "total_requests": 0,
#     "completed_requests": 0,
#     "failed_requests": 0,
#     "workflow_times": []  # 각 워크플로우별 소요시간 저장
# }
#
#
# class RateLimitError(Exception):
#     def __init__(self, msg, retry_after=None):
#         super().__init__(msg)
#         self.retry_after = retry_after
#
#
# MAX_CONCURRENT_REQUESTS = 5
# semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
#
# app = FastAPI()
# router = APIRouter()
#
# # 큐 정의 (전역)
# task_queue: Queue = Queue()
#
#
# def extract_retry_delay(response: dict) -> float:
#     error = response.get('error', {})
#     error_details = error.get('details', [])
#     for detail in error_details:
#         if detail.get('@type') == "type.googleapis.com/google.rpc.RetryInfo":
#             retry_delay_str: str = detail.get('retryDelay', {})
#             seconds = float(retry_delay_str[:-1])
#             return seconds
#     return 1.0  # 기본값 추가
#
#
# class WaitRetryAfter(wait_base):
#     def __call__(self, retry_state):
#         exc = retry_state.outcome.exception()
#         if exc and hasattr(exc, "retry_after") and exc.retry_after is not None:
#             return exc.retry_after
#         return 1
#
#
# @retry(
#     retry=retry_if_exception_type(RateLimitError),
#     wait=WaitRetryAfter(),
#     before_sleep=before_sleep_log(logger, logging.WARNING),
#     reraise=True
# )
# async def call_gemini():
#     async with httpx.AsyncClient() as client:
#         res = await client.post("http://localhost:8000/generate")
#         if res.status_code == 429:
#             retry_after = extract_retry_delay(res.json())
#             raise RateLimitError(f"Rate limit exceeded. retry after: {retry_after}", retry_after=retry_after + 1)
#
#
# async def analyze_job_posting():
#     await call_gemini()
#
#
# async def generate_search_query():
#     await call_gemini()
#
#
# async def generate_cover_letter_items(n: int):
#     tasks = [call_gemini() for _ in range(n)]
#     await asyncio.gather(*tasks)
#
#
# counter = 0
#
#
# async def do_work_flow(items: int):
#     global counter
#     counter += 1
#     workflow_start_time = time.time()
#
#     try:
#         print(f'워크 플로우{counter} 시작 - {time.strftime("%H:%M:%S")}')
#         await analyze_job_posting()
#         await generate_search_query()
#         await generate_cover_letter_items(items)
#
#         workflow_duration = time.time() - workflow_start_time
#         performance_tracker["workflow_times"].append(workflow_duration)
#         performance_tracker["completed_requests"] += 1
#
#         print(f'워크 플로우{counter} 완료 - 소요시간: {workflow_duration:.2f}초')
#
#         # 모든 작업이 완료되었는지 확인
#         if performance_tracker["completed_requests"] + performance_tracker["failed_requests"] == performance_tracker[
#             "total_requests"]:
#             performance_tracker["end_time"] = time.time()
#             print_performance_summary()
#
#     except RateLimitError:
#         performance_tracker["failed_requests"] += 1
#         print(f'워크 플로우{counter} 실패 - Rate Limit')
#
#         # 실패한 작업을 다시 큐에 넣기
#         await task_queue.put((do_work_flow, items))
#
#     except Exception as e:
#         performance_tracker["failed_requests"] += 1
#         print(f'워크 플로우{counter} 실패 - {str(e)}')
#
#
# def print_performance_summary():
#     """성능 측정 결과 출력"""
#     if performance_tracker["start_time"] and performance_tracker["end_time"]:
#         total_duration = performance_tracker["end_time"] - performance_tracker["start_time"]
#         avg_workflow_time = sum(performance_tracker["workflow_times"]) / len(performance_tracker["workflow_times"]) if \
#             performance_tracker["workflow_times"] else 0
#
#         print("\n" + "=" * 50)
#         print("성능 측정 결과")
#         print("=" * 50)
#         print(f"전체 소요시간: {total_duration:.2f}초")
#         print(f"총 요청 수: {performance_tracker['total_requests']}")
#         print(f"완료된 요청 수: {performance_tracker['completed_requests']}")
#         print(f"실패한 요청 수: {performance_tracker['failed_requests']}")
#         print(f"평균 워크플로우 시간: {avg_workflow_time:.2f}초")
#         print(f"처리량 (TPS): {performance_tracker['completed_requests'] / total_duration:.2f} req/sec")
#
#         if performance_tracker["workflow_times"]:
#             print(f"최단 워크플로우 시간: {min(performance_tracker['workflow_times']):.2f}초")
#             print(f"최장 워크플로우 시간: {max(performance_tracker['workflow_times']):.2f}초")
#
#         print("=" * 50)
#
#
# # Worker 정의
# async def worker(worker_id: int):
#     while True:
#         func, arg = await task_queue.get()
#         try:
#             await func(arg)
#         except Exception as e:
#             logger.error(f"[Worker {worker_id}] 작업 실패: {e}")
#         finally:
#             task_queue.task_done()
#
#
# # API 엔드포인트
# @router.post("/start-workflow/{items}")
# async def start_workflow(items: int):
#     # 첫 번째 요청일 때 시작 시간 기록
#     if performance_tracker["start_time"] is None:
#         performance_tracker["start_time"] = time.time()
#         print(f"성능 측정 시작 - {time.strftime('%H:%M:%S')}")
#
#     performance_tracker["total_requests"] += 1
#     await task_queue.put((do_work_flow, items))
#
#     return {"message": f"{items}개 아이템 워크플로우 작업이 큐에 등록되었습니다. (총 {performance_tracker['total_requests']}개 요청)"}
#
#
# # 성능 측정 상태 확인 API
# @router.get("/performance-status")
# async def get_performance_status():
#     current_time = time.time()
#     elapsed_time = current_time - performance_tracker["start_time"] if performance_tracker["start_time"] else 0
#
#     return {
#         "elapsed_time": elapsed_time,
#         "total_requests": performance_tracker["total_requests"],
#         "completed_requests": performance_tracker["completed_requests"],
#         "failed_requests": performance_tracker["failed_requests"],
#         "pending_requests": performance_tracker["total_requests"] - performance_tracker["completed_requests"] -
#                             performance_tracker["failed_requests"],
#         "queue_size": task_queue.qsize(),
#         "average_workflow_time": sum(performance_tracker["workflow_times"]) / len(
#             performance_tracker["workflow_times"]) if performance_tracker["workflow_times"] else 0,
#         "is_complete": performance_tracker["completed_requests"] + performance_tracker["failed_requests"] ==
#                        performance_tracker["total_requests"]
#     }
#
#
# # 성능 측정 리셋 API
# @router.post("/reset-performance")
# async def reset_performance():
#     global performance_tracker
#     performance_tracker = {
#         "start_time": None,
#         "end_time": None,
#         "total_requests": 0,
#         "completed_requests": 0,
#         "failed_requests": 0,
#         "workflow_times": []
#     }
#     return {"message": "성능 측정 데이터가 리셋되었습니다."}
#
#
# # 모든 작업 완료까지 대기하는 API
# @router.get("/wait-for-completion")
# async def wait_for_completion():
#     """모든 작업이 완료될 때까지 대기"""
#     while True:
#         if performance_tracker["total_requests"] > 0 and \
#                 (performance_tracker["completed_requests"] + performance_tracker["failed_requests"]) == \
#                 performance_tracker["total_requests"]:
#             break
#         await asyncio.sleep(1)
#
#     if performance_tracker["end_time"]:
#         total_duration = performance_tracker["end_time"] - performance_tracker["start_time"]
#         return {
#             "message": "모든 작업이 완료되었습니다.",
#             "total_duration": total_duration,
#             "completed_requests": performance_tracker["completed_requests"],
#             "failed_requests": performance_tracker["failed_requests"]
#         }
#     else:
#         return {"message": "작업이 아직 진행 중입니다."}
#
#
# app.include_router(router)
#
#
# # 앱 시작 시 Worker 실행
# @app.on_event("startup")
# async def startup_event():
#     for i in range(5):
#         asyncio.create_task(worker(i))
#
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8001)


import asyncio
import logging
import time
from asyncio import Queue

import httpx
import uvicorn
from fastapi import FastAPI, APIRouter
from tenacity import retry, retry_if_exception_type, before_sleep_log, stop_after_attempt, stop_after_delay
from tenacity.wait import wait_base, wait_exponential, wait_random

logger = logging.getLogger(__name__)

# 성능 측정을 위한 글로벌 변수들 (첫 번째 코드와 동일하게)
performance_tracker = {
    "start_time": None,
    "end_time": None,
    "total_requests": 0,
    "completed_requests": 0,
    "failed_requests": 0,
    "workflow_times": [],  # 각 워크플로우별 소요시간 저장
    "retry_counts": 0,  # 재시도 횟수
    "gemini_call_counts": 0,  # Gemini API 호출 횟수
    "queue_reinsert_counts": 0  # 큐 재삽입 횟수 (실패 후 재큐잉)
}


class RateLimitError(Exception):
    def __init__(self, msg, retry_after=None):
        super().__init__(msg)
        self.retry_after = retry_after


app = FastAPI()
router = APIRouter()

# 큐 정의 (전역)
task_queue: Queue = Queue()


def extract_retry_delay(response: dict) -> float:
    error = response.get('error', {})
    error_details = error.get('details', [])
    for detail in error_details:
        if detail.get('@type') == "type.googleapis.com/google.rpc.RetryInfo":
            retry_delay_str: str = detail.get('retryDelay', {})
            seconds = float(retry_delay_str[:-1])
            return seconds
    return 1.0  # 기본값 추가


class WaitRetryAfter(wait_base):
    def __call__(self, retry_state):
        exc = retry_state.outcome.exception()
        if exc and hasattr(exc, "retry_after") and exc.retry_after is not None:
            return exc.retry_after
        return 1


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=WaitRetryAfter(),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def call_gemini_with_retry_delay():
    """Gemini API 호출 (재시도 카운트 추가)"""
    performance_tracker["gemini_call_counts"] += 1

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/generate")
            if res.status_code == 429:
                performance_tracker["retry_counts"] += 1
                retry_after = extract_retry_delay(res.json())
                raise RateLimitError(f"Rate limit exceeded. retry after: {retry_after}", retry_after=retry_after + 1)
        except RateLimitError:
            # 재시도가 발생할 때마다 카운트
            raise


@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=(stop_after_attempt(6) & stop_after_delay(60)),
    wait=wait_exponential(multiplier=1, min=1, max=30) + wait_random(0, 2),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def call_gemini_with_expotential_backoff():
    """Gemini API 호출 (재시도 카운트 추가)"""
    performance_tracker["gemini_call_counts"] += 1

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/generate")
            if res.status_code == 429:
                performance_tracker["retry_counts"] += 1
                # retry_after = extract_retry_delay(res.json())
                # raise RateLimitError(f"Rate limit exceeded. retry after: {retry_after}", retry_after=retry_after + 1)
                raise RateLimitError(f"Rate limit exceeded. retry...")
        except RateLimitError:
            # 재시도가 발생할 때마다 카운트
            raise


async def analyze_job_posting():
    """채용공고 분석 - 1회 API 호출"""
    # await call_gemini_with_retry_delay()
    await call_gemini_with_expotential_backoff()


async def generate_search_query():
    """자소서 검색 쿼리 생성 - 1회 API 호출"""
    # await call_gemini_with_retry_delay()
    await call_gemini_with_expotential_backoff()


async def generate_cover_letter_items(n: int):
    """자소서 항목 n개 생성 - n회 API 호출"""
    # tasks = [call_gemini_with_retry_delay() for _ in range(n)]
    tasks = [call_gemini_with_expotential_backoff() for _ in range(n)]
    await asyncio.gather(*tasks)


counter = 0


async def do_work_flow(items: int):
    """워크플로우 실행 - 총 (2 + items)회의 API 호출"""
    global counter
    counter += 1
    workflow_start_time = time.time()

    try:
        print(f'워크 플로우{counter} 시작 - {time.strftime("%H:%M:%S")} (예상 API 호출: {2 + items}회)')

        await analyze_job_posting()  # 1회 API 호출
        await generate_search_query()  # 1회 API 호출
        await generate_cover_letter_items(items)  # items회 API 호출

        workflow_duration = time.time() - workflow_start_time
        performance_tracker["workflow_times"].append(workflow_duration)
        performance_tracker["completed_requests"] += 1

        print(f'워크 플로우{counter} 완료 - 소요시간: {workflow_duration:.2f}초')

        # 모든 작업이 완료되었는지 확인
        if performance_tracker["completed_requests"] + performance_tracker["failed_requests"] == performance_tracker[
            "total_requests"]:
            performance_tracker["end_time"] = time.time()
            print_performance_summary()

    except RateLimitError:
        performance_tracker["failed_requests"] += 1
        performance_tracker["queue_reinsert_counts"] += 1
        print(f'워크 플로우{counter} 실패 - Rate Limit (재큐 처리)')

        # 실패한 작업을 다시 큐에 넣기
        await task_queue.put((do_work_flow, items))

    except Exception as e:
        performance_tracker["failed_requests"] += 1
        print(f'워크 플로우{counter} 실패 - {str(e)}')


def print_performance_summary():
    """성능 측정 결과 출력 (첫 번째 코드와 동일한 형식)"""
    if performance_tracker["start_time"] and performance_tracker["end_time"]:
        total_duration = performance_tracker["end_time"] - performance_tracker["start_time"]
        avg_workflow_time = sum(performance_tracker["workflow_times"]) / len(performance_tracker["workflow_times"]) if \
            performance_tracker["workflow_times"] else 0

        print("\n" + "=" * 60)
        print("성능 측정 결과")
        print("=" * 60)
        print(f"전체 소요시간: {total_duration:.2f}초")
        print(f"총 요청 수: {performance_tracker['total_requests']}")
        print(f"완료된 요청 수: {performance_tracker['completed_requests']}")
        print(f"실패한 요청 수: {performance_tracker['failed_requests']}")
        print(f"평균 워크플로우 시간: {avg_workflow_time:.2f}초")
        print(f"처리량 (TPS): {performance_tracker['completed_requests'] / total_duration:.2f} req/sec")
        print(f"총 Gemini API 호출 횟수: {performance_tracker['gemini_call_counts']}")
        print(f"Rate Limit 재시도 횟수: {performance_tracker['retry_counts']}")
        print(f"큐 재삽입 횟수: {performance_tracker['queue_reinsert_counts']}")

        if performance_tracker["workflow_times"]:
            print(f"최단 워크플로우 시간: {min(performance_tracker['workflow_times']):.2f}초")
            print(f"최장 워크플로우 시간: {max(performance_tracker['workflow_times']):.2f}초")

        print("=" * 60)


# Worker 정의
async def worker(worker_id: int):
    """워커 - 큐에서 작업을 가져와 처리"""
    while True:
        func, arg = await task_queue.get()
        try:
            print(f"[Worker {worker_id}] 작업 시작 (큐 크기: {task_queue.qsize()})")
            await func(arg)
        except Exception as e:
            logger.error(f"[Worker {worker_id}] 작업 실패: {e}")
        finally:
            task_queue.task_done()


# API 엔드포인트
@router.post("/start-workflow/{items}")
async def start_workflow(items: int):
    """워크플로우 시작 - 큐에 작업 추가"""
    # 첫 번째 요청일 때 시작 시간 기록
    if performance_tracker["start_time"] is None:
        performance_tracker["start_time"] = time.time()
        print(f"성능 측정 시작 - {time.strftime('%H:%M:%S')}")

    performance_tracker["total_requests"] += 1
    await task_queue.put((do_work_flow, items))

    return {
        "message": f"{items}개 아이템 워크플로우 작업이 큐에 등록되었습니다. (총 {performance_tracker['total_requests']}개 요청)",
        "queue_size": task_queue.qsize(),
        "expected_api_calls": 2 + items  # 예상 API 호출 횟수
    }


# 성능 측정 상태 확인 API (첫 번째 코드와 동일)
@router.get("/performance-status")
async def get_performance_status():
    """실시간 성능 측정 상태 확인"""
    current_time = time.time()
    elapsed_time = current_time - performance_tracker["start_time"] if performance_tracker["start_time"] else 0

    return {
        "elapsed_time": f"{elapsed_time:.2f}초",
        "total_requests": performance_tracker["total_requests"],
        "completed_requests": performance_tracker["completed_requests"],
        "failed_requests": performance_tracker["failed_requests"],
        "pending_requests": performance_tracker["total_requests"] - performance_tracker["completed_requests"] -
                            performance_tracker["failed_requests"],
        "queue_size": task_queue.qsize(),
        # "semaphore_size": semaphore._value if hasattr(semaphore, '_value') else "unknown",
        "gemini_api_calls": performance_tracker["gemini_call_counts"],
        "retry_counts": performance_tracker["retry_counts"],
        "queue_reinsert_counts": performance_tracker["queue_reinsert_counts"],
        "average_workflow_time": f"{sum(performance_tracker['workflow_times']) / len(performance_tracker['workflow_times']):.2f}초" if
        performance_tracker["workflow_times"] else "0초",
        "is_complete": performance_tracker["completed_requests"] + performance_tracker["failed_requests"] ==
                       performance_tracker["total_requests"]
    }


# 성능 측정 리셋 API (첫 번째 코드와 동일)
@router.post("/reset-performance")
async def reset_performance():
    """성능 측정 데이터 리셋"""
    global performance_tracker
    performance_tracker = {
        "start_time": None,
        "end_time": None,
        "total_requests": 0,
        "completed_requests": 0,
        "failed_requests": 0,
        "workflow_times": [],
        "retry_counts": 0,
        "gemini_call_counts": 0,
        "queue_reinsert_counts": 0
    }
    return {"message": "성능 측정 데이터가 리셋되었습니다."}


# 모든 작업 완료까지 대기하는 API (첫 번째 코드와 동일)
@router.get("/wait-for-completion")
async def wait_for_completion():
    """모든 작업이 완료될 때까지 대기"""
    while True:
        if performance_tracker["total_requests"] > 0 and \
                (performance_tracker["completed_requests"] + performance_tracker["failed_requests"]) == \
                performance_tracker["total_requests"] and \
                task_queue.qsize() == 0:  # 큐도 비어있어야 함
            break
        await asyncio.sleep(1)

    if performance_tracker["end_time"]:
        total_duration = performance_tracker["end_time"] - performance_tracker["start_time"]
        return {
            "message": "모든 작업이 완료되었습니다.",
            "total_duration": f"{total_duration:.2f}초",
            "completed_requests": performance_tracker["completed_requests"],
            "failed_requests": performance_tracker["failed_requests"],
            "total_gemini_calls": performance_tracker["gemini_call_counts"],
            "retry_counts": performance_tracker["retry_counts"],
            "queue_reinsert_counts": performance_tracker["queue_reinsert_counts"]
        }
    else:
        return {"message": "작업이 아직 진행 중입니다."}


# 큐 상태 확인 API (첫 번째 코드와 동일)
@router.get("/queue-status")
async def get_queue_status():
    """큐 상태 확인"""
    return {
        "queue_size": task_queue.qsize(),
        "active_workers": 5,  # 워커 수
        "total_gemini_calls": performance_tracker["gemini_call_counts"],
        "retry_counts": performance_tracker["retry_counts"],
        "queue_reinsert_counts": performance_tracker["queue_reinsert_counts"]
    }


app.include_router(router)


# 앱 시작 시 Worker 실행
@app.on_event("startup")
async def startup_event():
    print("서버 시작 - 5개의 워커 실행")
    for i in range(5):  # 워커 5개 실행
        asyncio.create_task(worker(i))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
