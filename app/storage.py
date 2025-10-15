# app/storage.py
"""
Persistent storage handler for Render deployment.
Render has ephemeral filesystem - this provides persistence options.
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import tempfile

# Storage configuration
STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # local, s3, gcs
PERSISTENT_DIR = os.getenv("PERSISTENT_DIR", "/opt/render/project/.data")

# Local paths (ephemeral on Render)
UPLOADS_DIR = "uploads"
VECTOR_STORE_DIR = "app/vector_store/faiss_index"

def init_storage():
    """Initialize storage directories"""
    # Try to use persistent directory if available
    if STORAGE_MODE == "local":
        base_dir = PERSISTENT_DIR if os.path.exists(os.path.dirname(PERSISTENT_DIR)) else "."
        
        uploads_path = os.path.join(base_dir, "uploads") if base_dir != "." else UPLOADS_DIR
        vector_path = os.path.join(base_dir, "vector_store", "faiss_index") if base_dir != "." else VECTOR_STORE_DIR
        
        os.makedirs(uploads_path, exist_ok=True)
        os.makedirs(vector_path, exist_ok=True)
        
        # Create symlinks if using persistent directory
        if base_dir != ".":
            if not os.path.exists(UPLOADS_DIR):
                try:
                    os.symlink(uploads_path, UPLOADS_DIR, target_is_directory=True)
                except (OSError, NotImplementedError):
                    # Fallback: just use the local directories
                    os.makedirs(UPLOADS_DIR, exist_ok=True)
            
            vector_parent = os.path.dirname(VECTOR_STORE_DIR)
            os.makedirs(vector_parent, exist_ok=True)
            if not os.path.exists(VECTOR_STORE_DIR):
                try:
                    os.symlink(vector_path, VECTOR_STORE_DIR, target_is_directory=True)
                except (OSError, NotImplementedError):
                    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        
        return {
            "uploads": uploads_path if base_dir != "." else UPLOADS_DIR,
            "vector_store": vector_path if base_dir != "." else VECTOR_STORE_DIR
        }
    
    # For other storage modes (S3, GCS), implement as needed
    raise NotImplementedError(f"Storage mode {STORAGE_MODE} not implemented yet")

def get_storage_info():
    """Get storage information for debugging"""
    info = {
        "storage_mode": STORAGE_MODE,
        "uploads_dir": UPLOADS_DIR,
        "vector_store_dir": VECTOR_STORE_DIR,
        "persistent_dir": PERSISTENT_DIR,
        "uploads_exists": os.path.exists(UPLOADS_DIR),
        "vector_store_exists": os.path.exists(VECTOR_STORE_DIR),
    }
    
    if os.path.exists(VECTOR_STORE_DIR):
        info["vector_store_files"] = os.listdir(VECTOR_STORE_DIR)
    
    if os.path.exists(UPLOADS_DIR):
        info["uploaded_files"] = os.listdir(UPLOADS_DIR)
    
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
