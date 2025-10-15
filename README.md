# KB-RAG - AI Knowledge Base with RAG

A production-ready knowledge base system using Retrieval-Augmented Generation (RAG) with FastAPI, LangChain, and Google Gemini 2.0 Flash.

###DEMO VIDEO:
https://github.com/user-attachments/assets/ac97a2ac-840f-4877-b587-85937097f7c5
---

## ✨ Key Features

- **Multi-Document Support**: Upload multiple PDFs, TXT, or MD files and query across all documents
- **Smart Retrieval**: Automatically uses ALL document chunks for maximum accuracy
- **Latest AI Model**: Google Gemini 2.0 Flash Experimental with enhanced prompt engineering
- **Chat History**: Persistent conversation history with search functionality
- **Free to Use**: Google Gemini (generous free tier) + HuggingFace embeddings (completely free)
- **Clean UI**: Netflix-style interface with collapsible sidebar and drag-drop upload
- **Production Ready**: Optimized for Render.com deployment with memory management

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file:
```
GOOGLE_API_KEY=your-gemini-api-key-here
```

Get your free API key from: https://makersuite.google.com/app/apikey

### 3. Run Application

```bash
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000

## 📖 Usage

1. **Upload Documents**: Drag and drop multiple PDF, TXT, or MD files
2. **Ask Questions**: Type questions about your uploaded documents
3. **View Sources**: Each answer includes source document references
4. **Clear Knowledge Base**: Use "Clear All" button to reset and start fresh

## 🏗️ Architecture

```
User Query → FastAPI → FAISS Retriever → LangChain → Gemini 2.0 → Synthesized Answer
                ↓                                                           ↓
         Vector Store (All Chunks)                              Source Attribution
```

**RAG Pipeline:**
- **Chunking**: 800 chars with 150 char overlap using RecursiveCharacterTextSplitter
- **Embeddings**: HuggingFace sentence-transformers/all-MiniLM-L6-v2 (384 dim)
- **Vector DB**: FAISS for fast semantic search
- **LLM**: Google Gemini 2.0 Flash (temperature=0.0 for consistency)
- **Retrieval**: Automatic ALL-chunk retrieval for maximum accuracy

## 📁 Project Structure

```
kb-rag/
├── app/
│   ├── main.py          # FastAPI app & endpoints
│   ├── ingest.py        # Document processing & vector store
│   ├── query.py         # RAG query engine
│   ├── storage.py       # Storage management
│   └── utils.py         # File parsing utilities
├── static/
│   ├── css/            # Stylesheets
│   └── js/             # Frontend logic
├── templates/
│   ├── index.html      # Home page
│   └── app.html        # Main application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── README.md
```

## 🔧 API Endpoints

- `GET /` - Home page
- `GET /app` - Main application interface
- `POST /ingest` - Upload and process documents
- `POST /query` - Query the knowledge base
- `POST /clear` - Clear all documents from vector store
- `GET /health` - Health check endpoint

## 🎯 Technical Highlights

- **Singleton Pattern**: Embeddings model loaded once for performance
- **Memory Optimized**: Batch processing with garbage collection for 512MB limit
- **Smart Chunking**: Hierarchical text splitting preserves context
- **Error Handling**: Comprehensive try-except blocks with detailed logging
- **Lazy Loading**: Heavy imports only when needed for faster startup

## 🚀 Deployment

Configured for Render.com with:
- `/tmp` storage for ephemeral filesystem
- Uvicorn with 180s timeout
- Health check endpoint for monitoring
- Memory-efficient batch processing

## 📊 Performance

- Embedding Model Load: ~10-30s (first time only)
- Document Upload: ~2-5s per document
- Query Response: ~2-4s with source attribution
- Vector Search: <1s for 100 chunks

## 🤝 Contributing

Contributions welcome! This project demonstrates:
- Production-ready RAG implementation
- Multi-document knowledge base management
- Modern web UI with persistent chat history
- Cloud deployment best practices
