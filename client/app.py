import streamlit as st
from components.upload import render_uploader
from components.history_download import render_history_download
from components.chatUI import render_chat
from PIL import Image

# Page Config
st.set_page_config(
    page_title="RagBot 2.0 - AI Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- Layout: Sidebar ---
render_uploader()

# --- Main Content ---
# Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🤖 RagBot 2.0</div>
    <div class="hero-subtitle">Chat with your PDFs, Excel sheets, and more. Upload your documents in the sidebar to get started.</div>
</div>
""", unsafe_allow_html=True)

# Main Chat Interface (with custom styling from chatUI)
render_chat()

# Footer / History Download (only show if history exists)
if "messages" in st.session_state and st.session_state.messages:
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        render_history_download()