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

# Check environment variables at startup
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    print("=" * 70)
    print("⚠️  CRITICAL: GOOGLE_API_KEY not set!")
    print("=" * 70)
    print("Document upload will work, but queries will fail.")
    print("To fix this:")
    print("1. Go to Render Dashboard")
    print("2. Select your KB-RAG service")
    print("3. Go to Environment tab")
    print("4. Add: GOOGLE_API_KEY = AIzaSyCeRGwIg6V0_oYcaTeafSdbeBs3wwkk5f4")
    print("5. Save and redeploy")
    print("=" * 70)
else:
    print(f"✓ GOOGLE_API_KEY is set (starts with: {GOOGLE_API_KEY[:20]}...)")

print("\n" + "=" * 70)
print("⏱️  IMPORTANT TIMING INFORMATION:")
print("=" * 70)
print("• First upload (cold start): 60-120 seconds")
print("  - Model download: 40-60s")
print("  - Document processing: 20-40s")
print("• Subsequent uploads: 8-15 seconds (model cached)")
print("• Queries: 3-8 seconds")
print("=" * 70 + "\n")

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
    """
    global upload_progress
    
    try:
        upload_progress = {"status": "starting", "message": "Initializing upload...", "progress": 5}
        
        # LAZY IMPORT - only load when endpoint is called!
        from app.ingest import ingest_file
        
        print(f"\n{'='*60}")
        print(f"INGEST REQUEST STARTED")
        print(f"{'='*60}")
        print(f"Filename: {file.filename}")
        print(f"Content Type: {file.content_type}")
        print(f"Source: {source}")
        print(f"Upload directory: {UPLOAD_DIR}")
        
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
        print(f"Saving to: {file_path}")
        
        # Save file with error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"✓ File saved successfully: {file_path}")
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
        print(f"✓ File verified: {file_size} bytes")
        
        # Ingest the document
        upload_progress = {"status": "processing", "message": "Processing document...", "progress": 40}
        print("Starting document ingestion...")
        
        result = ingest_file(file_path, source=source or file.filename)
        
        # Check if there was an error in ingest_file
        if isinstance(result, dict) and "error" in result:
            print(f"✗ Ingestion failed: {result['error']}")
            upload_progress = {"status": "error", "message": result['error'], "progress": 0}
            return JSONResponse(
                status_code=500,
                content=result
            )
        
        print(f"✓ SUCCESS: Ingested {result.get('ingested', 0)} chunks")
        print(f"{'='*60}\n")
        
        upload_progress = {"status": "complete", "message": "Upload successful!", "progress": 100}
        
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
            }
        )

@app.post("/query")
async def query(question: str = Form(...), k: int = Form(3)):
    """
    Query the RAG system with a question.
    ROBUST error handling - always returns JSON.
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
        
        print(f"\n{'='*60}")
        print(f"QUERY REQUEST")
        print(f"{'='*60}")
        print(f"Question: {question}")
        print(f"K: {k}")
        
        result = answer_query(question, k=k)
        print(f"Raw result from answer_query: {result}")
        
        # Format response for frontend
        response = {
            "answer": result.get("result", "No answer generated"),
            "sources": []
        }
        
        # Extract source documents
        if "source_documents" in result:
            print(f"Found {len(result['source_documents'])} source documents")
            for i, doc in enumerate(result["source_documents"]):
                response["sources"].append({
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        
        print(f"✓ Query completed successfully")
        print(f"{'='*60}\n")
        
        return JSONResponse(
            status_code=200,
            content=response
        )
    
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        
        print(f"\n{'='*60}")
        print(f"✗ ERROR in /query endpoint")
        print(f"✗ Error type: {type(e).__name__}")
        print(f"✗ Error message: {error_msg}")
        print(f"✗ Full traceback:")
        print(tb)
        print(f"{'='*60}\n")
        
        # ALWAYS return JSON, never HTML
        return JSONResponse(
            status_code=500,
            content={
                "error": f"{type(e).__name__}: {error_msg}",
                "answer": "An error occurred while processing your query.",
                "details": tb.split('\n')[-3:-1]
            }
        )

# Mount static files AFTER all routes to avoid conflicts
app.mount("/static", StaticFiles(directory="static"), name="static")
