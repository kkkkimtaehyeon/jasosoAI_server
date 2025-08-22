from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.vectorstore import get_vectorstore
from app.models.cover_letter import CoverLetter
from app.schemas.cover_letter import CoverLetterResponse

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # 분할할 청크의 최대 크기 (글자 수)
    chunk_overlap=50  # 청크 간 겹칠 글자 수
)


def save_embedding(user_id: int, cover_letter: CoverLetterResponse):
    documents = []
    # vector db 선언
    vectorstore = get_vectorstore(user_id)
    for item in cover_letter.items:
        question_and_content = f'{item.question},{item.content}'

        # document(question + content) 선언
        source_document = Document(
            page_content=question_and_content,
            metadata={
                'user_id': user_id,
                'title': cover_letter.title,
                'question': item.question
            }
        )
        chunks = text_splitter.split_documents([source_document])
        documents.extend(chunks)

    if documents:
        vectorstore.add_documents(documents)
        print(f"총 {len(documents)}개의 벡터를 저장했습니다.")
    else:
        print("저장할 데이터가 없습니다.")
