# from datetime import datetime
#
# from fastapi import Depends
# from redis.asyncio import Redis
#
# from app.core.redis import get_redis
# from app.utils.logging import logger
#
#
# class ApiLimitManager:
#     def __init__(self,
#                  embedding_model_rpm: int,
#                  embedding_model_rpd: int,
#                  text_model_rpm: int,
#                  text_model_rpd: int,
#                  session: Redis):
#         self.embedding_model_rpm = embedding_model_rpm
#         self.embedding_model_rpd = embedding_model_rpd
#         self.text_model_rpm = text_model_rpm
#         self.text_model_rpd = text_model_rpd
#         self.session = session
#
#         self._EMBEDDING_MODEL_NAME = "embedding_model"
#         self._TEXT_MODEL_NAME = "text_model"
#
#     def _get_current_key_and_field(self, model_name: str) -> (str, str):
#         """현재 날짜의 Redis Key와 현재 시간(분)의 Field를 생성합니다."""
#         now = datetime.now()
#         date_str = now.strftime("%Y-%m-%d")
#         time_str = now.strftime("%H:%M")
#         key = f"{model_name}:{date_str}"
#         return key, time_str
#
#     async def _check_limit(self, model_name: str, rpm_limit: int, rpd_limit: int, requests: int = 1):
#         key, field = self._get_current_key_and_field(model_name)
#
#         # 현재 분의 카운트와 오늘 총 카운트를 원자적으로 가져옴
#         current_minute_count_raw, total_day_count_raw = await self.session.hmget(key, [field, "total"])
#
#         # 필드나 키가 존재하지 않으면 Redis는 None을 반환. 이 경우 0으로 처리.
#         current_minute_count = int(current_minute_count_raw) if current_minute_count_raw else 0
#         total_day_count = int(total_day_count_raw) if total_day_count_raw else 0
#
#         # RPM 확인
#         if current_minute_count + requests > rpm_limit:
#             raise Exception(  # RateLimitExceededError
#                 f"RPM limit for {model_name} exceeded. "
#                 f"Current: {current_minute_count}, Limit: {rpm_limit}"
#             )
#
#         # RPD 확인
#         if total_day_count + requests > rpd_limit:
#             raise Exception(  # RateLimitExceededError
#                 f"RPD limit for {model_name} exceeded. "
#                 f"Current: {total_day_count}, Limit: {rpd_limit}"
#             )
#
#     async def _consume(self, model_name: str, requests: int = 1):
#         """
#         모델의 Rate Limit 카운터를 소모(증가)하는 내부 메소드.
#
#         Args:
#             model_name (str): 소모할 모델의 이름.
#             requests (int): 소모할 요청의 수 (기본값 1).
#         """
#         key, field = self._get_current_key_and_field(model_name)
#
#         # 파이프라인을 사용하여 원자적 연산을 보장
#         async with self.session.pipeline() as pipe:
#             # 현재 분의 카운터 증가
#             await pipe.hincrby(key, field, requests)
#             # 오늘의 총 카운터 증가
#             await pipe.hincrby(key, "total", requests)
#             # 오래된 데이터 자동 삭제를 위해 Key 만료 시간 설정/갱신
#             # await pipe.expire(key, self._KEY_EXPIRATION_SECONDS)
#             # 모든 명령 실행
#             await pipe.execute()
#             logger.info(f"Consumed {requests} requests for {model_name}. Key: {key}, Field: {field}")
#
#     async def check_embedding_model_limit(self, requests: int = 1):
#         """임베딩 모델이 RPM 및 RPD 제한 내에 있는지 확인합니다."""
#         await self._check_limit(
#             self._EMBEDDING_MODEL_NAME,
#             self.embedding_model_rpm,
#             self.embedding_model_rpd,
#             requests
#         )
#
#     async def check_text_model_limit(self, requests: int = 1):
#         """텍스트 모델이 RPM 및 RPD 제한 내에 있는지 확인합니다."""
#         await self._check_limit(
#             self._TEXT_MODEL_NAME,
#             self.text_model_rpm,
#             self.text_model_rpd,
#             requests
#         )
#
#     async def consume_embedding_model(self, requests: int = 1):
#         """임베딩 모델 API 호출을 소모하고 Redis 카운터를 증가시킵니다."""
#         await self._consume(self._EMBEDDING_MODEL_NAME, requests)
#
#     async def consume_text_model(self, requests: int = 1):
#         """텍스트 모델 API 호출을 소모하고 Redis 카운터를 증가시킵니다."""
#         await self._consume(self._TEXT_MODEL_NAME, requests)
#
#
# def get_gemini_api_limit_manager(session: Redis = Depends(get_redis)) -> ApiLimitManager:
#     embedding_model_rpm = 100
#     embedding_model_rpd = 1000
#     text_model_rpm = 100
#     text_model_rpd = 1000
#     # 세션 생성 (rdb or redis)
#
#     return ApiLimitManager(embedding_model_rpm,
#                            embedding_model_rpd,
#                            text_model_rpm,
#                            text_model_rpd,
#                            session)
