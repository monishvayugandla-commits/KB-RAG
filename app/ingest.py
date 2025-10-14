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

# Initialize embeddings model once (singleton pattern for speed)
_embeddings = None

def get_embeddings():
    """Get or create embeddings model (singleton for performance)"""
    global _embeddings
    if _embeddings is None:
        print("Initializing embeddings model (first time only)...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )
        print("Embeddings model ready")
    return _embeddings

def chunk_text(text: str, chunk_size=800, chunk_overlap=150):
    """Split text into smaller chunks for faster processing"""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        docs = splitter.split_text(text)
        return docs
    except Exception as e:
        print(f"Error in chunk_text: {str(e)}")
        raise

def ingest_file(path: str, source: Optional[str] = None):
    """Ingest a file and add to vector store - OPTIMIZED for speed"""
    try:
        print(f"\n[1/6] Loading file: {path}")
        raw = load_file(path)
        print(f"[2/6] File loaded: {len(raw)} characters")
        
        print("[3/6] Chunking text...")
        chunks = chunk_text(raw)
        print(f"[4/6] Created {len(chunks)} chunks")
        
        # Prepare documents
        docs = []
        for i, chunk in enumerate(chunks):
            metadata = {"source": source or path, "chunk": i}
            docs.append(Document(page_content=chunk, metadata=metadata))
        
        print("[5/6] Generating embeddings (this may take a moment)...")
        embeddings = get_embeddings()
        
        # Ensure directory exists
        os.makedirs(INDEX_DIR, exist_ok=True)
        
        # Check if index exists
        index_files_exist = os.path.exists(os.path.join(INDEX_DIR, "index.faiss"))
        
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
        
        print("[6/6] Saving vector store...")
        vectordb.save_local(INDEX_DIR)
        print("✓ SUCCESS: Vector store saved")
        
        return {"ingested": len(docs), "source": source or path}
        
    except Exception as e:
        print(f"✗ ERROR in ingest_file: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a proper error dict instead of raising
        return {"error": f"Failed to ingest file: {str(e)}", "ingested": 0}