# import os
#
# from dotenv import load_dotenv
# from langchain_chroma import Chroma
# from langchain_core.documents import Document
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
#
# _ = load_dotenv()
# GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
#
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# # chroma_db의 절대 경로를 설정합니다.
# CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")
#
#
# def get_vectorstore(user_id: int) -> Chroma:
#     collection_name = f'cover_letters_{user_id}'
#     gemini_embeddings = GoogleGenerativeAIEmbeddings(
#         model="gemini-embedding-001",
#         google_api_key=GOOGLE_API_KEY
#     )
#     # vector db 선언
#     return Chroma(
#         collection_name=collection_name,
#         embedding_function=gemini_embeddings,  # 변경된 임베딩 객체를 사용
#         persist_directory=CHROMA_DB_PATH
#     )
#
#
# documents = []
# vectorstore = get_vectorstore(1)
# document = Document(
#     page_content="test content",
#     metadata={
#         'user_id': 1,
#         'title': 'title',
#         'question': 'question',
#         'cover_letter_id': 1
#     }
# )
# documents.append(document)
# vectorstore.add_documents(documents)
#
#
#
# # from google import genai
# #
# # client = genai.Client(api_key=GOOGLE_API_KEY)
# #
# # result = client.models.embed_content(
# #     model="gemini-embedding-001",
# #     contents="Hello, world!"
# # )
# # print(result)
