# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import traceback

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

# Ensure directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("app/vector_store/faiss_index", exist_ok=True)

# Health check endpoint
@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint for Render"""
    return JSONResponse({"status": "healthy", "message": "KB-RAG is running"})

@app.get("/")
@app.head("/")
async def home():
    """Serve the home page"""
    return FileResponse("templates/index.html")

@app.get("/app")
async def app_page():
    """Serve the application page"""
    return FileResponse("templates/app.html")

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    Upload and ingest a document into the vector store.
    OPTIMIZED for speed and reliability.
    """
    try:
        # LAZY IMPORT - only load when endpoint is called!
        from app.ingest import ingest_file
        
        print(f"\n{'='*50}")
        print(f"INGEST REQUEST STARTED")
        print(f"{'='*50}")
        print(f"Filename: {file.filename}")
        print(f"Content Type: {file.content_type}")
        
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"error": "No filename provided"}
            )
        
        # Save uploaded file using efficient streaming
        file_path = os.path.join("uploads", file.filename)
        print(f"Saving to: {file_path}")
        
        # Use shutil.copyfileobj for faster file operations
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✓ File saved: {file_path}")
        
        # Ingest the document
        print("Starting document ingestion...")
        result = ingest_file(file_path)
        
        # Check if there was an error in ingest_file
        if "error" in result:
            print(f"✗ Ingestion failed: {result['error']}")
            return JSONResponse(
                status_code=500,
                content=result
            )
        
        print(f"✓ SUCCESS: Ingested {result['ingested']} chunks")
        print(f"{'='*50}\n")
        
        return JSONResponse(content=result)
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n{'='*50}")
        print(f"✗ CRITICAL ERROR in /ingest endpoint")
        print(f"✗ Error: {error_msg}")
        traceback.print_exc()
        print(f"{'='*50}\n")
        return JSONResponse(
            status_code=500,
            content={"error": error_msg, "ingested": 0}
        )

@app.post("/query")
async def query(question: str = Form(...), k: int = Form(3)):
    """
    Query the RAG system with a question.
    """
    try:
        # LAZY IMPORT - only load when endpoint is called!
        from app.query import answer_query
        
        print(f"\n=== Query Request ===")
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
        
        print(f"Formatted response: {response}")
        print("===================\n")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        print(f"ERROR in query endpoint: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Mount static files AFTER all routes to avoid conflicts
app.mount("/static", StaticFiles(directory="static"), name="static")
