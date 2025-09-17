import os

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-001"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# 임베딩 모델 선언
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    google_api_key=GEMINI_API_KEY
)


def get_vectorstore(user_id: int) -> Chroma:
    collection_name = f'cover_letters_{user_id}'
    # vector db 선언
    return Chroma(
        collection_name=collection_name,
        embedding_function=gemini_embeddings,  # 변경된 임베딩 객체를 사용
        persist_directory=CHROMA_DB_PATH,
    )
