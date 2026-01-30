import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import pandas as pd
from rapidocr_onnxruntime import RapidOCR
from PIL import Image
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

UPLOAD_DIR = "./uploaded_pdfs"
PERSIST_DIR = "./chroma_db"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PERSIST_DIR, exist_ok=True)

# Initialize Embeddings
embed_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize OCR engine
try:
    ocr_engine = RapidOCR()
    print("✅ OCR Engine initialized")
except Exception as e:
    print(f"⚠️ OCR Init Warning: {e}")
    ocr_engine = None

def log_msg(msg):
    with open("ingestion.log", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    print(msg)

def extract_text_from_image(image_path):
    if not ocr_engine:
        return "OCR Engine not available"
    try:
        result, _ = ocr_engine(image_path)
        if result:
            text = "\n".join([line[1] for line in result])
            return text
        return ""
    except Exception as e:
        log_msg(f"❌ OCR Error on {image_path}: {e}")
        return ""

def process_file(file_path):
    ext = file_path.suffix.lower()
    docs = []
    
    # 1. Excel Files
    if ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(file_path)
            text_data = df.to_string(index=False)
            docs.append(Document(page_content=text_data, metadata={"source": str(file_path)}))
            log_msg(f"📊 Processed Excel: {file_path}")
        except Exception as e:
            log_msg(f"❌ Error processing Excel {file_path}: {e}")

    # 2. Image Files
    elif ext in ['.png', '.jpg', '.jpeg']:
        text = extract_text_from_image(str(file_path))
        if text:
            docs.append(Document(page_content=text, metadata={"source": str(file_path)}))
            log_msg(f"🖼️ OCR Success for Image: {file_path}")
        else:
            log_msg(f"⚠️ No text found in Image: {file_path}")

    # 3. PDF Files
    elif ext == '.pdf':
        try:
            # First pass: Try standard text extraction
            loader = PyPDFLoader(str(file_path))
            pdf_docs = loader.load()
            total_text_len = sum(len(d.page_content.strip()) for d in pdf_docs)
            
            # If text is sufficient, use it
            if total_text_len >= 50:
                docs.extend(pdf_docs)
                log_msg(f"📄 Processed Text PDF: {file_path}")
            else:
                log_msg(f"⚠️ Low text detected ({total_text_len} chars). Rasterizing PDF for OCR...")
                
                # Rasterize with PyMuPDF (Fitz)
                try:
                    doc = fitz.open(str(file_path))
                    ocr_full_text = ""
                    
                    for page_num, page in enumerate(doc):
                        # Render page to image (pixmap)
                        pix = page.get_pixmap(dpi=300)
                        img_bytes = pix.tobytes("png")
                        
                        if ocr_engine:
                            result, _ = ocr_engine(img_bytes)
                            if result:
                                page_text = "\n".join([line[1] for line in result])
                                ocr_full_text += page_text + "\n"
                                log_msg(f"   - Page {page_num+1}: OCR Success")
                            else:
                                log_msg(f"   - Page {page_num+1}: No text found")
                    
                    doc.close()

                    if ocr_full_text.strip():
                        docs.append(Document(page_content=ocr_full_text, metadata={"source": str(file_path)}))
                        log_msg(f"✅ OCR Extracted {len(ocr_full_text)} chars from scanned PDF")
                    else:
                        log_msg(f"❌ OCR found no text in {file_path}")

                except Exception as e:
                    log_msg(f"❌ PyMuPDF/OCR Error on {file_path}: {e}")

        except Exception as e:
            log_msg(f"❌ Error processing PDF {file_path}: {e}")
            
    return docs

def load_vectorstore(uploaded_files):
    """
    Ingests files and returns a status dictionary.
    """
    file_paths = []
    log_msg(f"🚀 Starting ingestion for {len(uploaded_files)} files")
    
    saved_files = []
    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / file.filename
        with open(save_path, "wb") as f:
            f.write(file.file.read())
        saved_files.append(save_path)
        log_msg(f"💾 Saved file: {save_path}")

    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    processed_count = 0
    failed_files = []

    for file_path in saved_files:
        documents = process_file(file_path)
        if documents:
            chunks = splitter.split_documents(documents)
            all_chunks.extend(chunks)
            processed_count += 1
            log_msg(f"🧩 Split {file_path.name} into {len(chunks)} chunks")
        else:
            failed_files.append(file_path.name)
            log_msg(f"⚠️ Skipping {file_path.name} (No content extracted)")

    if all_chunks:
        log_msg(f"🔍 Embedding {len(all_chunks)} chunks...")
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embed_model,
            collection_name="rag_app"
        )
        vectorstore.add_documents(documents=all_chunks)
        log_msg(f"✅ SUCCESS: Saved {len(all_chunks)} chunks to {PERSIST_DIR}")
        return {"status": "success", "processed": processed_count, "failed": failed_files}
    else:
        log_msg("⚠️ FAIL: No valid text extracted from any file.")
        return {"status": "error", "processed": 0, "failed": failed_files}

def get_all_documents():
    """Returns a list of unique filenames in the vectorstore."""
    try:
        if not os.path.exists(PERSIST_DIR):
            return []
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embed_model,
            collection_name="rag_app"
        )
        data = vectorstore.get()
        if not data or not data['metadatas']:
            return []
        sources = set()
        for meta in data['metadatas']:
            if meta and 'source' in meta:
                sources.add(os.path.basename(meta['source']))
        return list(sources)
    except Exception as e:
        log_msg(f"❌ Error listing documents: {e}")
        return []

def delete_document(filename):
    """Deletes a document from vectorstore and disk."""
    try:
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embed_model,
            collection_name="rag_app"
        )
        file_path = Path(UPLOAD_DIR) / filename
        data = vectorstore.get()
        ids_to_delete = []
        for i, meta in enumerate(data['metadatas']):
            if meta and 'source' in meta:
                if os.path.basename(meta['source']) == filename:
                    ids_to_delete.append(data['ids'][i])
        
        if ids_to_delete:
            vectorstore.delete(ids=ids_to_delete)
            log_msg(f"🗑️ Deleted {len(ids_to_delete)} chunks for {filename} from DB")
        
        if file_path.exists():
            os.remove(file_path)
            log_msg(f"🗑️ Deleted file {filename} from disk")
            
        return True
    except Exception as e:
        log_msg(f"❌ Error deleting document {filename}: {e}")
        return False
