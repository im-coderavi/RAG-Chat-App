import streamlit as st
from utils.api import ask_question
import requests

def render_chat():
    # Header with Clear Button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("💬 Chat with your documents")
    with col2:
        if st.button("🗑️ Clear", help="Clear chat history"):
            st.session_state.messages = []
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Welcome message if chat is empty
    if not st.session_state.messages:
        st.info("👋 **Welcome!** Upload documents in the sidebar, then ask me anything about them.")

    # Render existing chat history
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = "👤" if role == "user" else "🤖"
        st.chat_message(role, avatar=avatar).markdown(msg["content"])

    # Input and response
    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.chat_message("user", avatar="👤").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            try:
                response = ask_question(user_input)
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The server is taking too long. Please try again.")
                return
            except requests.exceptions.ConnectionError:
                st.error("🔌 Cannot connect to server. Is the backend running?")
                return
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                return
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "No response received.")
            sources = data.get("sources", [])
            
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(answer)
                if sources:
                    with st.expander("📄 Source Documents"):
                        for src in sources:
                            st.markdown(f"- `{src}`")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            # Parse JSON error for user-friendly message
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Unknown error occurred.")
            except Exception:
                error_msg = response.text or "Unknown error occurred."
            st.error(f"⚠️ {error_msg}")
