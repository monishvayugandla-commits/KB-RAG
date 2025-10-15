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

# Use /tmp for vector store on Render (writable location)
INDEX_DIR = os.environ.get("VECTOR_STORE_DIR", "/tmp/vector_store/faiss_index")

# Initialize embeddings model once (singleton pattern for speed)
_embeddings = None

def get_embeddings():
    """Get or create embeddings model (singleton for performance)"""
    global _embeddings
    if _embeddings is None:
        print("  → Loading embeddings model (first time: ~10-30s)")
        import time
        import gc
        
        # Force garbage collection before loading model
        gc.collect()
        
        start = time.time()
        
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
                # encode_kwargs removed - causes parameter conflicts with sentence-transformers
                # batch_size and normalize_embeddings will use library defaults
            )
            
            elapsed = time.time() - start
            print(f"  → Model loaded in {elapsed:.1f}s")
            
            # Force garbage collection after loading
            gc.collect()
            
        except Exception as e:
            print(f"✗ Failed to load embeddings: {e}")
            raise
    return _embeddings

def chunk_text(text: str, chunk_size=800, chunk_overlap=150):
    """Split text into semantically meaningful chunks with optimal overlap
    
    Args:
        text: Raw document text to chunk
        chunk_size: Target size for each chunk (default: 800 chars)
        chunk_overlap: Overlap between chunks to preserve context (default: 150 chars)
        
    Returns:
        list[str]: List of text chunks
        
    Strategy:
        - Uses RecursiveCharacterTextSplitter for intelligent splitting
        - Preserves sentence and paragraph boundaries when possible
        - Maintains context across chunks with overlap
        - Optimizes for both retrieval accuracy and LLM context window
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Smart splitting hierarchy
        )
        docs = splitter.split_text(text)
        return docs
    except Exception as e:
        print(f"Error in chunk_text: {str(e)}")
        raise

def ingest_file(path: str, source: Optional[str] = None, replace_existing: bool = True):
    """Ingest a file and add to vector store - OPTIMIZED for speed and memory
    
    Args:
        path: Path to the file to ingest
        source: Optional source name for metadata
        replace_existing: If True, replaces existing vector store. If False, adds to it.
    """
    try:
        import time
        import gc
        
        total_start = time.time()
        
        # Load file
        raw = load_file(path)
        print(f"  → Loaded {len(raw)} characters")
        
        # Chunk text
        chunks = chunk_text(raw)
        print(f"  → Created {len(chunks)} chunks")
        
        # Free memory after loading
        del raw
        gc.collect()
        
        # Prepare documents
        docs = []
        for i, chunk in enumerate(chunks):
            metadata = {"source": source or path, "chunk": i}
            docs.append(Document(page_content=chunk, metadata=metadata))
        
        # Free memory
        del chunks
        gc.collect()
        
        # Load embeddings model
        embeddings = get_embeddings()
        
        # Ensure directory exists
        os.makedirs(INDEX_DIR, exist_ok=True)
        
        # Check if index exists
        index_files_exist = os.path.exists(os.path.join(INDEX_DIR, "index.faiss"))
        
        print("[5/6] Processing vector store...")
        step_start = time.time()
        
        # IMPORTANT: Handle replace_existing flag
        if replace_existing and index_files_exist:
            print("      🗑️  Clearing old vector store (replace mode)...")
            import shutil
            try:
                # Remove old index files
                shutil.rmtree(INDEX_DIR)
                os.makedirs(INDEX_DIR, exist_ok=True)
                index_files_exist = False
            except Exception as e:
                print(f"      ⚠ Could not clear old store: {e}")
        
        # Process in smaller batches if we have many documents
        if len(docs) > 50:
            print(f"  → Processing {len(docs)} docs in batches")
            
            if index_files_exist and not replace_existing:
                vectordb = FAISS.load_local(
                    INDEX_DIR, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
            else:
                # Create initial index with first batch
                batch_size = 25
                vectordb = FAISS.from_documents(docs[:batch_size], embeddings)
                docs = docs[batch_size:]
                gc.collect()
            
            # Add remaining documents in batches
            batch_size = 25
            for i in range(0, len(docs), batch_size):
                batch = docs[i:i+batch_size]
                vectordb.add_documents(batch)
                gc.collect()
        else:
            # Process all at once for small document sets
            if index_files_exist and not replace_existing:
                vectordb = FAISS.load_local(
                    INDEX_DIR, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                vectordb.add_documents(docs)
            else:
                vectordb = FAISS.from_documents(docs, embeddings)
        
        # Free memory before saving
        del docs
        gc.collect()
        
        # Save vector store
        vectordb.save_local(INDEX_DIR)
        
        total_time = time.time() - total_start
        num_docs = vectordb.index.ntotal
        
        # Final cleanup
        del vectordb
        gc.collect()
        
        print(f"  ✓ Completed in {total_time:.1f}s")
        
        return {
            "ingested": num_docs, 
            "source": source or path,
            "time_seconds": round(total_time, 2)
        }
        
    except Exception as e:
        print(f"✗ Ingest error: {str(e)}")
        # Return a proper error dict instead of raising
        return {"error": f"Failed to ingest file: {str(e)}", "ingested": 0}