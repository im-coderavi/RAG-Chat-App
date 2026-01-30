from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

print("✅ Imported successfully")

embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("✅ Embeddings model loaded")

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embed_model,
    collection_name="rag_app"
)
print("✅ Vectorstore loaded")

print("✅ Test complete")
