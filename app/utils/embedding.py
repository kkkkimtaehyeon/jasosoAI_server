from langchain_core.documents import Document

from app.core.vectorstore import get_vectorstore
from app.schemas.cover_letter import CoverLetterResponse
from app.utils.logging import logger


def save_embedding(user_id: int, cover_letter: CoverLetterResponse):
    vectorstore = get_vectorstore(user_id)

    documents = []

    for item in cover_letter.items:
        document = Document(
            page_content=item.content,
            metadata={
                'user_id': user_id,
                'title': cover_letter.title,
                'question': item.question,
                'cover_letter_id': cover_letter.id
            }
        )

        documents.append(document)
    try:
        vectorstore.add_documents(documents)
        logger.info(f"벡터 저장 완료: {len(documents)}개, user_id: {user_id}, cover_letter_id: {cover_letter.id}")
    except Exception as e:
        logger.error(f"벡터 저장 중 에러 발생: {e}, user_id: {user_id}, cover_letter_id: {cover_letter.id}")


async def delete_embedding(user_id: int, cover_letter_id: int):
    vectorstore = get_vectorstore(user_id)
    try:
        vectorstore.delete(where={'cover_letter_id': cover_letter_id})
        logger.info(f"벡터 삭제 완료: user_id: {user_id}, cover_letter_id: {cover_letter_id}")
    except Exception as e:
        logger.error(f"벡터 삭제 중 에러 발생: {e}, user_id: {user_id}, cover_letter_id: {cover_letter_id}")
