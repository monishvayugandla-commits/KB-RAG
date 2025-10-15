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
        print("⏳ Initializing embeddings model (first time only)...")
        print("   This downloads ~90MB model - may take 10-30 seconds...")
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
            print(f"✓ Embeddings model ready in {elapsed:.2f}s")
            
            # Force garbage collection after loading
            gc.collect()
            
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
        
        print(f"\n{'='*60}")
        print(f"[1/6] Loading file: {path}")
        step_start = time.time()
        raw = load_file(path)
        print(f"[1/6] ✓ File loaded: {len(raw)} characters ({time.time()-step_start:.2f}s)")
        
        print("[2/6] Chunking text...")
        step_start = time.time()
        chunks = chunk_text(raw)
        print(f"[2/6] ✓ Created {len(chunks)} chunks ({time.time()-step_start:.2f}s)")
        
        # Free memory after loading
        del raw
        gc.collect()
        
        # Prepare documents
        print("[3/6] Preparing documents...")
        step_start = time.time()
        docs = []
        for i, chunk in enumerate(chunks):
            metadata = {"source": source or path, "chunk": i}
            docs.append(Document(page_content=chunk, metadata=metadata))
        print(f"[3/6] ✓ Prepared {len(docs)} documents ({time.time()-step_start:.2f}s)")
        
        # Free memory
        del chunks
        gc.collect()
        
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
        
        # IMPORTANT: Handle replace_existing flag
        if replace_existing and index_files_exist:
            print("      🗑️  Clearing old vector store (replace mode)...")
            import shutil
            try:
                # Remove old index files
                shutil.rmtree(INDEX_DIR)
                os.makedirs(INDEX_DIR, exist_ok=True)
                index_files_exist = False
                print("      ✓ Old vector store cleared")
            except Exception as e:
                print(f"      ⚠ Warning: Could not clear old store: {e}")
        
        # Process in smaller batches if we have many documents
        if len(docs) > 50:
            print(f"      Processing {len(docs)} documents in batches to save memory...")
            
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
                print(f"      Adding batch {i//batch_size + 1} ({len(batch)} docs)...")
                vectordb.add_documents(batch)
                gc.collect()
        else:
            # Process all at once for small document sets
            if index_files_exist and not replace_existing:
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
        
        # Free memory before saving
        del docs
        gc.collect()
        
        print("[6/6] Saving vector store...")
        step_start = time.time()
        vectordb.save_local(INDEX_DIR)
        print(f"[6/6] ✓ Vector store saved ({time.time()-step_start:.2f}s)")
        
        total_time = time.time() - total_start
        num_docs = vectordb.index.ntotal
        
        # Final cleanup
        del vectordb
        gc.collect()
        
        print(f"{'='*60}")
        print(f"✓ SUCCESS: Ingested {num_docs} chunks in {total_time:.2f}s")
        print(f"{'='*60}\n")
        
        return {
            "ingested": num_docs, 
            "source": source or path,
            "time_seconds": round(total_time, 2)
        }
        
    except Exception as e:
        print(f"✗ ERROR in ingest_file: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a proper error dict instead of raising
        return {"error": f"Failed to ingest file: {str(e)}", "ingested": 0}