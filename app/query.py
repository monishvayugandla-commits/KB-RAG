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

PROMPT_TEMPLATE = """You are an expert AI assistant specializing in document analysis and question answering.

Your task is to provide accurate, comprehensive answers based ONLY on the provided document excerpts below.

INSTRUCTIONS:
1. Synthesize information from multiple sources when relevant
2. Provide specific details and examples from the documents
3. If information spans multiple excerpts, connect them coherently
4. Cite source metadata when making claims
5. If the answer is not in the documents, clearly state: "Based on the provided documents, I don't have enough information to answer this question."
6. Be concise but thorough - aim for completeness without unnecessary verbosity

DOCUMENT EXCERPTS:
{context}

USER QUESTION: {question}

ANSWER (synthesized from the documents above):"""

def get_retriever(k=None):
    """Get retriever from vector store - using shared embeddings
    
    If k is None, automatically retrieves ALL chunks for maximum accuracy
    """
    try:
        embeddings = get_embeddings()  # Use singleton
        
        if not os.path.exists(INDEX_DIR):
            raise Exception("Vector store not found. Please upload a document first.")
        
        vectordb = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        
        # Auto-determine k: use all chunks for best accuracy
        if k is None:
            total_chunks = vectordb.index.ntotal
            k = total_chunks
            print(f"  → Using all {k} chunks for maximum accuracy")
        
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        print(f"✗ Retriever error: {str(e)}")
        raise

def answer_query(question: str, k=None, model="gemini-2.0-flash-exp"):
    """Answer a question using RAG with advanced retrieval and synthesis
    
    Args:
        question: User's question
        k: Number of chunks to retrieve (None = use all for maximum accuracy)
        model: Google Gemini model to use
        
    Returns:
        dict: Contains 'result' (answer) and 'source_documents' (retrieved chunks)
        
    Features:
        - Automatic retrieval of ALL relevant chunks (k=None)
        - Zero temperature for consistent, factual responses
        - Custom prompt engineering for better synthesis
        - Source attribution for answer verification
        - Comprehensive error handling
    """
    try:
        # Check for API key first
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Set it in environment or .env file"
            )
        
        # Get retriever with automatic k selection
        retriever = get_retriever(k)
        
        # Use enhanced prompt template for better synthesis
        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE, 
            input_variables=["context", "question"]
        )

        # Initialize Google Gemini LLM with optimal settings
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.0,  # Deterministic, factual responses
            timeout=30,
            max_retries=2  # Automatic retry on transient failures
        )

        # Create RetrievalQA chain with "stuff" strategy (concatenate all docs)
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # Best for comprehensive answers
            retriever=retriever,
            return_source_documents=True,  # Enable source attribution
            chain_type_kwargs={"prompt": prompt}
        )

        # Execute query and return results with source documents
        result = qa(question)
        return result
        
    except Exception as e:
        print(f"✗ Query error: {str(e)}")
        raise