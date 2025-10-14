# app/query.py
from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
from langchain.chains import RetrievalQA # type: ignore
from langchain_core.prompts import PromptTemplate # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()
INDEX_DIR = "app/vector_store"

PROMPT_TEMPLATE = """You are given a user's question and a set of relevant document excerpts below.
Using these documents, answer the user's question succinctly. If the answer is not present, say you don't know and offer to search further.

{context}

Question: {question}
Answer concisely and include the source metadata for each supporting sentence where possible.
"""

def get_retriever(k=5):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index_path = os.path.join(INDEX_DIR, "faiss_index")
    vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    return vectordb.as_retriever(search_kwargs={"k": k})

def answer_query(question: str, k=5, model="gemini-2.5-flash"):
    retriever = get_retriever(k)
    prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

    # Use Gemini via LangChain
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # "map_reduce" or "refine" are alternatives for longer contexts
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    result = qa(question)
    # result contains 'result' and 'source_documents'
    return result