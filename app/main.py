# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import traceback
import tempfile
from app.storage import init_storage, get_storage_info, check_vector_store_exists

# DON'T import these at module level - causes slow startup!
# from app.ingest import ingest_file
# from app.query import answer_query

# Create FastAPI app
app = FastAPI(
    title="KB-RAG - AI Knowledge Base",
    description="Retrieval-Augmented Generation system with Google Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use /tmp for uploads on Render (ephemeral but writable)
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/tmp/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"✓ Upload directory: {UPLOAD_DIR}")

# Vector store directory
VECTOR_STORE_DIR = os.environ.get("VECTOR_STORE_DIR", "/tmp/vector_store/faiss_index")
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
print(f"✓ Vector store directory: {VECTOR_STORE_DIR}")

# Check environment variables at startup (only show detailed warnings if missing)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("⚠️  GOOGLE_API_KEY not set - queries will fail")
else:
    print(f"✓ GOOGLE_API_KEY is set")

# Initialize storage (handles ephemeral filesystem on Render)
try:
    storage_paths = init_storage()
    print(f"✓ Storage initialized: {storage_paths}")
except Exception as e:
    print(f"⚠ Storage initialization warning: {e}")
    # Fallback already created above

# Progress tracking for long operations
upload_progress = {"status": "idle", "message": "", "progress": 0}

# Health check endpoint
@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint for Render"""
    api_key_set = bool(os.environ.get('GOOGLE_API_KEY'))
    return JSONResponse({
        "status": "healthy", 
        "message": "KB-RAG is running",
        "api_key_configured": api_key_set,
        "upload_dir": UPLOAD_DIR,
        "vector_store_dir": VECTOR_STORE_DIR
    })

@app.get("/storage-info")
async def storage_info():
    """Get storage information for debugging"""
    info = get_storage_info()
    info["vector_store_initialized"] = check_vector_store_exists()
    return JSONResponse(info)

@app.get("/progress")
async def get_progress():
    """Get progress of current upload operation"""
    return JSONResponse(upload_progress)

@app.get("/")
@app.head("/")
async def home():
    """Serve the home page"""
    return FileResponse("templates/index.html")

@app.get("/app")
async def app_page():
    """Serve the application page"""
    return FileResponse("templates/app.html")

@app.get("/test")
async def test_page():
    """Serve the debug test page"""
    return FileResponse("templates/test.html")

@app.post("/ingest")
async def ingest(file: UploadFile = File(...), source: str = Form(None)):
    """
    Upload and ingest a document into the vector store.
    ROBUST error handling - always returns JSON.
    MEMORY OPTIMIZED for Render free tier (512MB limit).
    """
    global upload_progress
    import gc
    
    try:
        # Force garbage collection before starting
        gc.collect()
        
        upload_progress = {"status": "starting", "message": "Initializing upload...", "progress": 5}
        
        # LAZY IMPORT - only load when endpoint is called!
        from app.ingest import ingest_file
        
        print(f"📄 Upload: {file.filename}")
        
        if not file.filename:
            upload_progress = {"status": "error", "message": "No filename provided", "progress": 0}
            return JSONResponse(
                status_code=400,
                content={"error": "No filename provided", "ingested": 0}
            )
        
        # Save to /tmp directory (writable on Render)
        upload_progress = {"status": "saving", "message": "Saving file...", "progress": 20}
        
        # Create temp directory for this upload
        tmp_dir = tempfile.mkdtemp(dir=UPLOAD_DIR)
        file_path = os.path.join(tmp_dir, file.filename)
        
        # Save file with error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as save_error:
            print(f"✗ Failed to save file: {save_error}")
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to save file: {str(save_error)}", "ingested": 0}
            )
        
        # Verify file exists and is readable
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=500,
                content={"error": "File was not saved correctly", "ingested": 0}
            )
        
        file_size = os.path.getsize(file_path)
        
        # Ingest the document
        upload_progress = {"status": "processing", "message": "Processing document...", "progress": 40}
        
        # Check if vector store already exists - if yes, ADD to it (don't replace)
        # This allows multiple documents to coexist in the knowledge base
        from app.ingest import INDEX_DIR
        index_exists = os.path.exists(os.path.join(INDEX_DIR, "index.faiss"))
        replace_mode = not index_exists  # Only replace if no index exists (first upload)
        
        result = ingest_file(file_path, source=source or file.filename, replace_existing=replace_mode)
        
        if replace_mode:
            print(f"  ℹ️  First document - created new vector store")
            # Add flag to indicate this was a fresh start (frontend should clear old document list)
            result['is_first_document'] = True
        else:
            print(f"  ℹ️  Added to existing vector store")
            result['is_first_document'] = False
        
        # Check if there was an error in ingest_file
        if isinstance(result, dict) and "error" in result:
            print(f"✗ Ingestion failed: {result['error']}")
            upload_progress = {"status": "error", "message": result['error'], "progress": 0}
            return JSONResponse(
                status_code=500,
                content=result
            )
        
        print(f"✓ Ingested {result.get('ingested', 0)} chunks")
        
        upload_progress = {"status": "complete", "message": "Upload successful!", "progress": 100}
        
        # Force garbage collection after operation
        import gc
        gc.collect()
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        
        print(f"\n{'='*60}")
        print(f"✗ CRITICAL ERROR in /ingest endpoint")
        print(f"✗ Error type: {type(e).__name__}")
        print(f"✗ Error message: {error_msg}")
        print(f"✗ Full traceback:")
        print(tb)
        print(f"{'='*60}\n")
        
        upload_progress = {"status": "error", "message": error_msg, "progress": 0}
        
        # ALWAYS return JSON, never HTML
        return JSONResponse(
            status_code=500,
            content={
                "error": f"{type(e).__name__}: {error_msg}",
                "ingested": 0,
                "details": tb.split('\n')[-3:-1]  # Last 2 lines of traceback
            },
            media_type="application/json"  # Explicitly set content-type
        )

@app.post("/clear")
async def clear_knowledge_base():
    """
    Clear all documents from the vector store and reset the knowledge base.
    """
    try:
        from app.ingest import INDEX_DIR
        import gc
        
        print("🗑️ Clearing knowledge base...")
        
        # Check if vector store exists
        if os.path.exists(INDEX_DIR):
            try:
                # Remove the entire vector store directory
                shutil.rmtree(INDEX_DIR)
                print("  ✓ Vector store deleted")
            except Exception as e:
                print(f"  ✗ Failed to delete vector store: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to delete vector store: {str(e)}"}
                )
        else:
            print("  ℹ️  Vector store was already empty")
        
        # Force garbage collection
        gc.collect()
        
        print("✓ Knowledge base cleared successfully")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Knowledge base cleared successfully",
                "cleared": True
            }
        )
    
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        
        print(f"\n{'='*60}")
        print(f"✗ ERROR in /clear endpoint")
        print(f"✗ Error: {error_msg}")
        print(f"✗ Traceback:")
        print(tb)
        print(f"{'='*60}\n")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to clear knowledge base: {error_msg}",
                "cleared": False
            }
        )

@app.post("/query")
async def query(question: str = Form(...)):
    """
    Query the RAG system with a question.
    ROBUST error handling - always returns JSON.
    Now automatically uses ALL chunks from uploaded document for best accuracy.
    """
    try:
        # Check if vector store exists first
        if not check_vector_store_exists():
            return JSONResponse(
                status_code=400,
                content={
                    "error": "No documents uploaded yet. Please upload a document first.",
                    "answer": "Please upload a document before asking questions."
                }
            )
        
        # LAZY IMPORT - only load when endpoint is called!
        from app.query import answer_query
        
        print(f"❓ Query: {question[:50]}{'...' if len(question) > 50 else ''}")
        
        result = answer_query(question, k=None)  # None = use all chunks
        
        # Format response for frontend
        response = {
            "answer": result.get("result", "No answer generated"),
            "sources": []
        }
        
        # Extract source documents
        if "source_documents" in result:
            for i, doc in enumerate(result["source_documents"]):
                response["sources"].append({
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        print(f"✓ Answer generated ({len(result['source_documents'])} sources)")
        
        return JSONResponse(
            status_code=200,
            content=response
        )
    
    except Exception as e:
        error_msg = str(e)
        
        print(f"✗ Query error: {error_msg}")
        
        # ALWAYS return JSON, never HTML
        return JSONResponse(
            status_code=500,
            content={
                "error": f"{type(e).__name__}: {error_msg}",
                "answer": "An error occurred while processing your query."
            },
            media_type="application/json"  # Explicitly set content-type
        )

# Mount static files AFTER all routes to avoid conflicts
app.mount("/static", StaticFiles(directory="static"), name="static")
