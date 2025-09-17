# # app/core/redis.py
# import os
#
# import redis.asyncio as redis
# from dotenv import load_dotenv
#
# _ = load_dotenv()
# REDIS_URL = os.getenv("REDIS_URL")
# redis_client: redis.Redis | None = None
#
#
# async def init_redis():
#     global redis_client
#     redis_client = redis.from_url(REDIS_URL, decode_responses=True)
#
#
# async def close_redis():
#     if redis_client is not None:
#         await redis_client.close()
#
#
# def get_redis() -> redis.Redis:
#     if redis_client is None:
#         raise RuntimeError("Redis not initialized")
#     return redis_client
