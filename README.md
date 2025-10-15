# KB-RAG Demo

A knowledge base with Retrieval-Augmented Generation (RAG) using FastAPI, LangChain, and Google Gemini.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
GOOGLE_API_KEY=your-gemini-api-key-here
```

4. Get your Gemini API key:
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy and paste into your `.env` file

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

2. Upload documents via POST to `/ingest`
3. Query the knowledge base via POST to `/query`

## Features

- **Free to Use**: Uses Google Gemini Pro (generous free tier) and HuggingFace embeddings (completely free)
- **No OpenAI Required**: Runs entirely on Google's Gemini API
- **Fast Embeddings**: Local HuggingFace sentence transformers for vector embeddings
- **Multiple Formats**: Supports Multiple PDF, TXT, and MD file uploads

## API Endpoints

- `POST /ingest` - Upload and ingest documents (PDF, TXT, MD)
- `POST /query` - Query the knowledge base with Gemini Pro

## Project Structure

```
kb-rag/
├─ .env
├─ .gitignore
├─ README.md
├─ requirements.txt
├─ app/
│  ├─ main.py             # FastAPI app
│  ├─ ingest.py           # ingestion functions
│  ├─ query.py            # query / RAG functions
│  ├─ utils.py            # helpers (pdf parsing, chunking)
│  └─ vector_store/       # saved FAISS index + metadata
└─ demo/                  # optional frontend or demo scripts
   └─ index.html
```