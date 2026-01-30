import requests

from config import API_URL
TIMEOUT_SHORT = 10  # For quick operations like listing docs
TIMEOUT_LONG = 60   # For LLM operations that take time

def upload_pdfs_api(files):
    files_payload = [("files", (f.name, f.read(), "application/pdf")) for f in files]
    return requests.post(f"{API_URL}/upload_pdfs/", files=files_payload, timeout=TIMEOUT_LONG)

def get_documents_api():
    return requests.get(f"{API_URL}/documents/", timeout=TIMEOUT_SHORT)

def delete_document_api(filename):
    return requests.delete(f"{API_URL}/documents/{filename}", timeout=TIMEOUT_SHORT)

def ask_question(question):
    return requests.post(f"{API_URL}/ask/", data={"question": question}, timeout=TIMEOUT_LONG)