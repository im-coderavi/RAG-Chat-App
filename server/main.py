from fastapi import FastAPI,UploadFile,File,Form,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from modules.load_vectorstore import load_vectorstore
from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from logger import logger
import os

app=FastAPI(title="RagBot2.0")

# allow frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def catch_exception_middleware(request:Request,call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("UNHANDLED EXCEPTION")
        return JSONResponse(status_code=500,content={"error":str(exc)})
    
@app.post("/upload_pdfs/")
async def upload_pdfs(files:List[UploadFile]=File(...)):
    try:
        logger.info(f"recieved {len(files)} files")
        result = load_vectorstore(files)
        
        if result.get("status") == "success":
            logger.info("documents added to chroma")
            return {"message": f"Successfully processed {result.get('processed')} files."}
        else:
            failed_files = ", ".join(result.get("failed", []))
            logger.error(f"Ingestion failed for: {failed_files}")
            return JSONResponse(status_code=422, content={"error": f"Failed to process: {failed_files}. Files may be empty or unreadable."})
            
    except Exception as e:
        logger.exception("Error during pdf upload")
        return JSONResponse(status_code=500,content={"error":str(e)})

@app.get("/documents/")
async def list_documents():
    from modules.load_vectorstore import get_all_documents
    docs = get_all_documents()
    return {"documents": docs}

@app.delete("/documents/{filename}")
async def delete_document_endpoint(filename: str):
    from modules.load_vectorstore import delete_document
    success = delete_document(filename)
    if success:
        return {"message": f"Document {filename} deleted"}
    else:
        return JSONResponse(status_code=500, content={"error": "Failed to delete document"})
# async def ask_quyestion(question:str=Form(...)):
#     try:
#         logger.info("fuser query:{question}")
#         from langchain.vectorstores import Chroma
#         from langchain.embeddings import HuggingFaceBgeEmbeddings
#         from modules.load_vectorstore import PERSIST_DIR

#         vectorstore=Chroma(
#             persist_directory=PERSIST_DIR,
#             embedding_function=HuggingFaceBgeEmbeddings(model_name="all-MiniLM-L12-v2")
#         )
#         chain=get_llm_chain(vectorstore)
#         result=query_chain(chain,question)
#         logger.info("query successfull")
#         return result
#     except Exception as e:
#         logger.exception("error processing question")
#         return JSONResponse(status_code=500,content={"error":str(e)})

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        # Input Validation
        if not question or not question.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Please enter a question.", "code": "EMPTY_QUESTION"}
            )
        
        question = question.strip()
        logger.info(f"user query: {question}")

        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
        from modules.llm import get_llm_chain
        from modules.query_handlers import query_chain
        import os

        PERSIST_DIR = "./chroma_db"
        
        # Check if database exists and has data
        if not os.path.exists(PERSIST_DIR):
            return JSONResponse(
                status_code=422,
                content={
                    "error": "No documents uploaded yet. Please upload some files first.",
                    "code": "NO_DOCUMENTS"
                }
            )
        
        # 1. Initialize Embeddings
        embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # 2. Load Chroma Vector Store
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embed_model,
            collection_name="rag_app"
        )
        
        # Check if collection is empty
        try:
            count = vectorstore._collection.count()
            if count == 0:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": "Your knowledge base is empty. Please upload some documents first.",
                        "code": "EMPTY_DATABASE"
                    }
                )
        except Exception:
            pass  # Fallback: let it proceed if count fails
        
        # 3. Create Retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6}
        )

        # 4. LLM + RetrievalQA chain
        chain = get_llm_chain(retriever)
        result = query_chain(chain, question)

        logger.info("query successful")
        return result

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong. Please try again later.", "code": "SERVER_ERROR"}
        )


@app.get("/test")
async def test():
    return {"message":"Testing successfull..."}