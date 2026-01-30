import streamlit as st
from utils.api import upload_pdfs_api, get_documents_api, delete_document_api
import requests

def render_uploader():
    st.sidebar.header("📤 Upload Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload files (PDF, Excel, Images)", 
        type=["pdf", "xlsx", "xls", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    if st.sidebar.button("Upload to DB", type="primary") and uploaded_files:
        with st.sidebar.spinner("Processing files..."):
            try:
                response = upload_pdfs_api(uploaded_files)
                if response.status_code == 200:
                    st.sidebar.success("✅ Uploaded successfully!")
                    st.rerun()  # Refresh to show new docs
                elif response.status_code == 422:
                    try:
                        error_msg = response.json().get("error", "File processing failed")
                    except:
                        error_msg = "File processing failed"
                    st.sidebar.error(f"⚠️ {error_msg}")
                else:
                    st.sidebar.error(f"❌ Upload failed (Status: {response.status_code})")
            except requests.exceptions.Timeout:
                st.sidebar.error("⏱️ Upload timed out. Try smaller files or restart the server.")
            except requests.exceptions.ConnectionError as e:
                st.sidebar.error(f"🔌 Cannot connect to server. Details: {e}")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)[:50]}")

    # --- Manage Knowledge Base ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Knowledge Base")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh"):
        st.rerun()

    # Fetch documents with error handling
    try:
        response = get_documents_api()
        if response.status_code == 200:
            doc_list = response.json().get("documents", [])
            if doc_list:
                for doc in doc_list:
                    col1, col2 = st.sidebar.columns([0.75, 0.25])
                    col1.markdown(f"📄 `{doc[:20]}...`" if len(doc) > 20 else f"📄 `{doc}`")
                    if col2.button("🗑️", key=f"del_{doc}", help=f"Delete {doc}"):
                        try:
                            del_response = delete_document_api(doc)
                            if del_response.status_code == 200:
                                st.sidebar.success(f"Deleted!")
                                st.rerun()
                            else:
                                st.sidebar.error("Delete failed")
                        except Exception:
                            st.sidebar.error("Delete failed")
            else:
                st.sidebar.info("📭 No documents uploaded yet.")
        else:
            st.sidebar.warning("⚠️ Could not fetch documents.")
    except requests.exceptions.Timeout:
        st.sidebar.warning("⏱️ Server slow. Click Refresh.")
    except requests.exceptions.ConnectionError:
        st.sidebar.warning("🔌 Backend offline.")
    except Exception:
        st.sidebar.warning("⚠️ Backend unavailable.")