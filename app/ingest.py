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
        print("⏳ Initializing embeddings model (first time only)...")
        print("   This downloads ~90MB model - may take 10-30 seconds...")
        import time
        start = time.time()
        
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={
                    'normalize_embeddings': True, 
                    'batch_size': 16,  # Reduced from 32 for lower memory
                    'show_progress_bar': False
                }
            )
            
            elapsed = time.time() - start
            print(f"✓ Embeddings model ready in {elapsed:.2f}s")
        except Exception as e:
            print(f"✗ Failed to load embeddings model: {e}")
            raise
    else:
        print("✓ Using cached embeddings model")
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
        import time
        total_start = time.time()
        
        print(f"\n{'='*60}")
        print(f"[1/6] Loading file: {path}")
        step_start = time.time()
        raw = load_file(path)
        print(f"[1/6] ✓ File loaded: {len(raw)} characters ({time.time()-step_start:.2f}s)")
        
        print("[2/6] Chunking text...")
        step_start = time.time()
        chunks = chunk_text(raw)
        print(f"[2/6] ✓ Created {len(chunks)} chunks ({time.time()-step_start:.2f}s)")
        
        # Prepare documents
        print("[3/6] Preparing documents...")
        step_start = time.time()
        docs = []
        for i, chunk in enumerate(chunks):
            metadata = {"source": source or path, "chunk": i}
            docs.append(Document(page_content=chunk, metadata=metadata))
        print(f"[3/6] ✓ Prepared {len(docs)} documents ({time.time()-step_start:.2f}s)")
        
        print("[4/6] Loading embeddings model...")
        step_start = time.time()
        embeddings = get_embeddings()
        print(f"[4/6] ✓ Embeddings ready ({time.time()-step_start:.2f}s)")
        
        # Ensure directory exists
        os.makedirs(INDEX_DIR, exist_ok=True)
        
        # Check if index exists
        index_files_exist = os.path.exists(os.path.join(INDEX_DIR, "index.faiss"))
        
        print("[5/6] Processing vector store...")
        step_start = time.time()
        if index_files_exist:
            print("      Loading existing vector store...")
            vectordb = FAISS.load_local(
                INDEX_DIR, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print("      Adding new documents...")
            vectordb.add_documents(docs)
        else:
            print("      Creating new vector store...")
            vectordb = FAISS.from_documents(docs, embeddings)
        print(f"[5/6] ✓ Vector store updated ({time.time()-step_start:.2f}s)")
        
        print("[6/6] Saving vector store...")
        step_start = time.time()
        vectordb.save_local(INDEX_DIR)
        print(f"[6/6] ✓ Vector store saved ({time.time()-step_start:.2f}s)")
        
        total_time = time.time() - total_start
        print(f"{'='*60}")
        print(f"✓ SUCCESS: Ingested {len(docs)} chunks in {total_time:.2f}s")
        print(f"{'='*60}\n")
        
        return {
            "ingested": len(docs), 
            "source": source or path,
            "time_seconds": round(total_time, 2)
        }
        
    except Exception as e:
        print(f"✗ ERROR in ingest_file: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a proper error dict instead of raising
        return {"error": f"Failed to ingest file: {str(e)}", "ingested": 0}