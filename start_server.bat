@echo off
cd /d "C:\kb-rag"
call .venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
pause