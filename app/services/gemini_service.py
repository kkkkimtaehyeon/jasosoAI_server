import os
from asyncio import Queue
from typing import Type, TypeVar, Union

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError
from google.genai.types import GenerateContentConfig
from pydantic import TypeAdapter, BaseModel
from tenacity import retry, retry_if_exception_type
from tenacity.wait import wait_base

_ = load_dotenv()
gemini = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
GEMINI_DEFAULT_MODEL = 'gemini-2.5-flash-lite'
MODEL = os.getenv('GEMINI_MODEL_NAME', GEMINI_DEFAULT_MODEL)

task_queue: Queue = Queue()


class RateLimitError(Exception):
    def __init__(self, msg, retry_after=None):
        super().__init__(msg)
        self.retry_after = retry_after


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


T = TypeVar("T", bound=BaseModel)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=WaitRetryAfter(),
    # before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def generate_content(contents: Union[list[str], str], response_schema):
    try:
        response = await gemini.aio.models.generate_content(
            model=MODEL,
            contents=contents,
            config=GenerateContentConfig(
                response_schema=response_schema,
                response_mime_type="application/json"
            )
        )
        return TypeAdapter(response_schema).validate_json(response.text)
    except ClientError as e:
        if e.code == 429:
            retry_after = extract_retry_delay(e.details)
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after) from e
        else:
            raise
