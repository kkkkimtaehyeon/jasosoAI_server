import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="가짜 API RPM 제한 시뮬레이터")


class TokenBucket:
    def __init__(self, max_tokens: int = 15, refill_period: float = 60.0):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_period = refill_period
        self.last_refill = time.time()
        self.lock = threading.Lock()

        # 백그라운드에서 토큰 리필 스레드 시작
        self.refill_thread = threading.Thread(target=self._refill_tokens, daemon=True)
        self.refill_thread.start()

    def _refill_tokens(self):
        """1분마다 토큰을 최대치로 리필"""
        while True:
            time.sleep(self.refill_period)
            with self.lock:
                self.tokens = self.max_tokens
                self.last_refill = time.time()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 토큰 리필됨: {self.tokens}/{self.max_tokens}")

    def consume_token(self) -> bool:
        """토큰 1개 소비, 성공 시 True 반환"""
        with self.lock:
            if self.tokens > 0:
                self.tokens -= 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 토큰 소비: 남은 토큰 {self.tokens}/{self.max_tokens}")
                return True
            return False

    def get_status(self) -> Dict[str, Any]:
        """현재 토큰 버킷 상태 반환"""
        with self.lock:
            next_refill = self.last_refill + self.refill_period
            time_until_refill = max(0, next_refill - time.time())
            return {
                "current_tokens": self.tokens,
                "max_tokens": self.max_tokens,
                "time_until_refill": round(time_until_refill, 1),
                "last_refill": datetime.fromtimestamp(self.last_refill).strftime('%H:%M:%S')
            }


# 전역 토큰 버킷 인스턴스
rate_limiter = TokenBucket(max_tokens=15, refill_period=60.0)


def create_quota_error(retry_delay: int):
    """할당량 초과 에러 응답 생성"""
    return {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota...",
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                    "violations": [
                        {
                            "quotaMetric": "GenerateRequestsPerMinute",
                            "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
                            "quotaValue": "15"
                        }
                    ]
                },
                {
                    "@type": "type.googleapis.com/google.rpc.Help",
                    "links": [
                        {
                            "description": "Learn more about Gemini API quotas",
                            "url": "https://ai.google.dev/gemini-api/docs/rate-limits"
                        }
                    ]
                },
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": f'{retry_delay}s'
                }
            ]
        }
    }


@app.get("/")
async def root():
    """API 상태 및 토큰 정보"""
    status = rate_limiter.get_status()
    return {
        "message": "가짜 API RPM 제한 시뮬레이터",
        "rpm_limit": 15,
        "current_status": status,
        "endpoints": {
            "POST /generate": "텍스트 생성 (토큰 소비)",
            "GET /status": "현재 토큰 상태 확인",
            "POST /reset": "토큰 버킷 리셋"
        }
    }


@app.post("/generate")
async def generate_text():
    """가짜 텍스트 생성 API - 토큰 소비"""
    if not rate_limiter.consume_token():
        # 토큰이 부족할 때 429 에러 반환
        status = rate_limiter.get_status()
        retry_delay = status["time_until_refill"]
        error_response = create_quota_error(retry_delay)
        return JSONResponse(
            status_code=429,
            content=error_response
        )
    await asyncio.sleep(3)
    # 성공 시 가짜 응답
    # return {
    #     "status": "success",
    #     "generated_text": "이것은 가짜 생성된 텍스트입니다.",
    #     "timestamp": datetime.now().isoformat(),
    #     "remaining_tokens": rate_limiter.get_status()["current_tokens"]
    # }


@app.get("/status")
async def get_status():
    """현재 토큰 버킷 상태 확인"""
    return {
        "rate_limit_status": rate_limiter.get_status(),
        "rpm_limit": 15,
        "refill_interval": "60 seconds"
    }


@app.post("/reset")
async def reset_tokens():
    """토큰 버킷을 수동으로 리셋 (테스트용)"""
    with rate_limiter.lock:
        rate_limiter.tokens = rate_limiter.max_tokens
        rate_limiter.last_refill = time.time()

    return {
        "message": "토큰 버킷이 리셋되었습니다.",
        "status": rate_limiter.get_status()
    }


@app.get("/test-burst")
async def test_burst():
    """RPM 제한 테스트용 - 여러 번 연속 호출"""
    results = []

    for i in range(20):  # 15개 제한보다 많이 시도
        if rate_limiter.consume_token():
            results.append({
                "request": i + 1,
                "status": "success",
                "remaining_tokens": rate_limiter.get_status()["current_tokens"]
            })
        else:
            results.append({
                "request": i + 1,
                "status": "rate_limited",
                "error": "토큰 부족"
            })

    return {
        "test_results": results,
        "final_status": rate_limiter.get_status()
    }


if __name__ == "__main__":
    import uvicorn

    print("가짜 API 서버 시작...")
    print("RPM 제한: 15 requests/minute")
    print("토큰은 1분마다 자동으로 리필됩니다.")
    print("\n사용법:")
    print("- POST /generate : 텍스트 생성 (토큰 소비)")
    print("- GET /status : 현재 상태 확인")
    print("- POST /reset : 토큰 리셋")
    print("- GET /test-burst : RPM 제한 테스트")

    uvicorn.run(app, host="0.0.0.0", port=8000)
