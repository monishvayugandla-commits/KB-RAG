# app/query.py
from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
from langchain.chains import RetrievalQA # type: ignore
from langchain_core.prompts import PromptTemplate # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from dotenv import load_dotenv # type: ignore
import os
from app.ingest import get_embeddings

load_dotenv()

# Use /tmp for vector store on Render (writable location)
INDEX_DIR = os.environ.get("VECTOR_STORE_DIR", "/tmp/vector_store/faiss_index")

PROMPT_TEMPLATE = """You are given a user's question and a set of relevant document excerpts below.
Using these documents, answer the user's question succinctly. If the answer is not present, say you don't know and offer to search further.

{context}

Question: {question}
Answer concisely and include the source metadata for each supporting sentence where possible.
"""

def get_retriever(k=3):
    """Get retriever from vector store - using shared embeddings"""
    try:
        print(f"Loading vector store from: {INDEX_DIR}")
        embeddings = get_embeddings()  # Use singleton
        
        if not os.path.exists(INDEX_DIR):
            raise Exception("Vector store not found. Please upload a document first.")
        
        vectordb = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        print(f"✓ Vector store loaded")
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        print(f"✗ Error loading vector store: {str(e)}")
        raise

def answer_query(question: str, k=3, model="gemini-2.0-flash-exp"):
    """Answer a question using RAG - OPTIMIZED"""
    try:
        # Check for API key first
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Please configure it in Render dashboard: "
                "Settings → Environment → Add GOOGLE_API_KEY"
            )
        
        print(f"[1/4] Getting retriever with k={k}")
        retriever = get_retriever(k)
        prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

        print("[2/4] Initializing Gemini LLM...")
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.0,
            timeout=30
        )

        print("[3/4] Creating QA chain...")
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

        print("[4/4] Running query...")
        result = qa(question)
        print("✓ Query completed")
        return result
        
    except Exception as e:
        print(f"✗ Error in answer_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise