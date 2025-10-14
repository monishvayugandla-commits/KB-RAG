# app/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from app.ingest import ingest_file
from app.query import answer_query

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

@app.get("/")
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
    """
    try:
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"error": "No filename provided"}
            )
        
        # Save uploaded file
        file_path = os.path.join("uploads", file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest the document
        result = ingest_file(file_path)
        return JSONResponse(content=result)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/query")
async def query(question: str = Form(...), k: int = Form(3)):
    """
    Query the RAG system with a question.
    """
    try:
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
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
