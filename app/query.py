# app/query.py
from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
from langchain.chains import RetrievalQA # type: ignore
from langchain_core.prompts import PromptTemplate # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()
INDEX_DIR = "app/vector_store/faiss_index"

PROMPT_TEMPLATE = """You are given a user's question and a set of relevant document excerpts below.
Using these documents, answer the user's question succinctly. If the answer is not present, say you don't know and offer to search further.

{context}

Question: {question}
Answer concisely and include the source metadata for each supporting sentence where possible.
"""

def get_retriever(k=5):
    """Get retriever from vector store"""
    try:
        print(f"Loading vector store from: {INDEX_DIR}")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        if not os.path.exists(INDEX_DIR):
            raise Exception("Vector store not found. Please upload a document first.")
        
        vectordb = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        print(f"Vector store loaded successfully")
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        raise

def answer_query(question: str, k=5, model="gemini-2.0-flash-exp"):
    """Answer a question using RAG"""
    try:
        print(f"Getting retriever with k={k}")
        retriever = get_retriever(k)
        prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

        # Use Gemini via LangChain
        print("Initializing Gemini LLM...")
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.0
        )

        print("Creating QA chain...")
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # "map_reduce" or "refine" are alternatives for longer contexts
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

        print("Running query...")
        result = qa(question)
        print("Query completed successfully")
        # result contains 'result' and 'source_documents'
        return result
        
    except Exception as e:
        print(f"Error in answer_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise