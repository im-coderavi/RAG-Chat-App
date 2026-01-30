from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_llm_chain(retriever):
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile"
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a smart **Document Assistant**. Your job is to answer the user's question based **only** on the provided context.

---
**Context:**
{context}

**User Question:**
{question}
---

**Instructions:**
1. If the answer is in the context, provide it clearly.
2. If the context does not contain the answer, say "I couldn't find that information in the document."
3. Do not make up information.
""",
    )

    # Custom chain wrapper to replace RetrievalQA and avoid langchain package dependency issues
    def run_chain(inputs):
        question = inputs["query"]
        
        # 1. Retrieve documents
        # retriever.invoke is the modern LCEL method (langchain-core)
        docs = retriever.invoke(question)
        
        # 2. Format context
        context = "\n\n".join(doc.page_content for doc in docs)
        
        # 3. Generate answer
        formatted_prompt = prompt.format(context=context, question=question)
        response = llm.invoke(formatted_prompt)
        
        # 4. Return result in expected format
        return {
            "result": response.content,
            "source_documents": docs
        }

    return run_chain
