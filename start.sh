#!/bin/bash
# start.sh - For Linux/Mac deployment

echo "Starting KB-RAG Application..."
echo "================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set default port
PORT=${PORT:-8000}

# Start the server
echo "Server starting on port $PORT"
uvicorn app.main:app --host 0.0.0.0 --port $PORT
