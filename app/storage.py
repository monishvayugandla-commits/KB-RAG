# app/storage.py
"""
Storage handler for Render deployment.
Uses /tmp directory which is writable on Render.
"""
import os
import shutil
from pathlib import Path
from typing import Optional

# Storage configuration - use /tmp on Render
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")
UPLOADS_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads")
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "/tmp/vector_store/faiss_index")

def init_storage():
    """Initialize storage directories"""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    
    return {
        "uploads": UPLOADS_DIR,
        "vector_store": VECTOR_STORE_DIR
    }

def get_storage_info():
    """Get storage information for debugging"""
    info = {
        "storage_mode": STORAGE_MODE,
        "uploads_dir": UPLOADS_DIR,
        "vector_store_dir": VECTOR_STORE_DIR,
        "uploads_exists": os.path.exists(UPLOADS_DIR),
        "vector_store_exists": os.path.exists(VECTOR_STORE_DIR),
    }
    
    if os.path.exists(VECTOR_STORE_DIR):
        try:
            info["vector_store_files"] = os.listdir(VECTOR_STORE_DIR)
        except:
            info["vector_store_files"] = []
    
    if os.path.exists(UPLOADS_DIR):
        try:
            info["uploaded_files"] = os.listdir(UPLOADS_DIR)
        except:
            info["uploaded_files"] = []
    
    return info

def check_vector_store_exists():
    """Check if vector store has been initialized"""
    index_path = os.path.join(VECTOR_STORE_DIR, "index.faiss")
    pkl_path = os.path.join(VECTOR_STORE_DIR, "index.pkl")
    return os.path.exists(index_path) and os.path.exists(pkl_path)

def get_vector_store_path():
    """Get the vector store directory path"""
    return VECTOR_STORE_DIR

def get_uploads_path():
    """Get the uploads directory path"""
    return UPLOADS_DIR

def cleanup_old_uploads(max_files: int = 10):
    """Clean up old uploaded files to save space"""
    try:
        if not os.path.exists(UPLOADS_DIR):
            return
        
        files = []
        for f in os.listdir(UPLOADS_DIR):
            file_path = os.path.join(UPLOADS_DIR, f)
            if os.path.isfile(file_path):
                files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[1])
        
        # Remove oldest files if we exceed max_files
        if len(files) > max_files:
            for file_path, _ in files[:len(files) - max_files]:
                try:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")
    
    except Exception as e:
        print(f"Error in cleanup_old_uploads: {e}")
