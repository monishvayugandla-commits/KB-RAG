# Start Server Script for PowerShell
Set-Location "C:\kb-rag"
& ".\\.venv\\Scripts\\Activate.ps1"
uvicorn app.main:app --reload --port 8000