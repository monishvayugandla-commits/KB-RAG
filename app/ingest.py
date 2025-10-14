# app/ingest.py
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import FAISS # type: ignore
from langchain_core.documents import Document # type: ignore
from dotenv import load_dotenv # type: ignore
import os
from .utils import load_file
from typing import Optional

load_dotenv()

INDEX_DIR = "app/vector_store/faiss_index"

def chunk_text(text: str, chunk_size=1000, chunk_overlap=200):
    """Split text into chunks for processing"""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        docs = splitter.split_text(text)
        return docs
    except Exception as e:
        print(f"Error in chunk_text: {str(e)}")
        raise

def ingest_file(path: str, source: Optional[str] = None):
    """Ingest a file and add to vector store"""
    try:
        print(f"Loading file: {path}")
        raw = load_file(path)
        print(f"File loaded, length: {len(raw)} characters")
        
        print("Chunking text...")
        chunks = chunk_text(raw)
        print(f"Created {len(chunks)} chunks")
        
        docs = []
        for i, chunk in enumerate(chunks):
            metadata = {"source": source or path, "chunk": i}
            docs.append(Document(page_content=chunk, metadata=metadata))
        
        print("Initializing embeddings model...")
        # Use free HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Ensure directory exists
        os.makedirs(INDEX_DIR, exist_ok=True)
        print(f"Vector store directory: {INDEX_DIR}")
        
        # Check if index exists
        index_files_exist = os.path.exists(os.path.join(INDEX_DIR, "index.faiss"))
        print(f"Existing index found: {index_files_exist}")
        
        if index_files_exist:
            print("Loading existing vector store...")
            vectordb = FAISS.load_local(
                INDEX_DIR, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print("Adding new documents...")
            vectordb.add_documents(docs)
        else:
            print("Creating new vector store...")
            vectordb = FAISS.from_documents(docs, embeddings)
        
        print("Saving vector store...")
        vectordb.save_local(INDEX_DIR)
        print("Vector store saved successfully")
        
        return {"ingested": len(docs), "source": source or path}
        
    except Exception as e:
        print(f"ERROR in ingest_file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to ingest file: {str(e)}")