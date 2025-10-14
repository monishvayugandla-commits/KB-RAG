# app/ingest.py
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_core.documents import Document # type: ignore
from dotenv import load_dotenv # type: ignore
import os, uuid, json
from .utils import load_file
from typing import Optional

load_dotenv()

INDEX_DIR = "app/vector_store"
os.makedirs(INDEX_DIR, exist_ok=True)

def chunk_text(text: str, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs = splitter.split_text(text)
    return docs

def ingest_file(path: str, source: Optional[str] = None):
    raw = load_file(path)
    chunks = chunk_text(raw)
    docs = []
    for i, chunk in enumerate(chunks):
        metadata = {"source": source or path, "chunk": i}
        docs.append(Document(page_content=chunk, metadata=metadata))

    # Use free HuggingFace embeddings instead of OpenAI
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index_path = os.path.join(INDEX_DIR, "faiss_index")
    if os.path.exists(index_path):
        # load existing
        vectordb = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        vectordb.add_documents(docs)
    else:
        vectordb = FAISS.from_documents(docs, embeddings)
    vectordb.save_local(index_path)
    return {"ingested": len(docs), "source": source or path}