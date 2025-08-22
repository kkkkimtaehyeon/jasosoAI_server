import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# chroma_db의 절대 경로를 설정합니다.
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# 임베딩 모델 선언
EMBEDDING_MODEL_NAME = 'jhgan/ko-sroberta-multitask'
hf_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def get_vectorstore(user_id: int) -> Chroma:
    collection_name = f'cover_letters_{user_id}'
    # vector db 선언
    return Chroma(
        collection_name=collection_name,
        embedding_function=hf_embeddings,
        persist_directory=CHROMA_DB_PATH
    )