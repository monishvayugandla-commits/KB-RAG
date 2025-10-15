#!/usr/bin/env python3
"""
Keep-alive script for Render.com free tier.
Pings the service every 10 minutes to prevent it from sleeping.

Run this on your local machine or use a free cron service:
- cron-job.org
- UptimeRobot
- freshping.io
"""

import requests
import time
from datetime import datetime

# Your Render service URL
SERVICE_URL = "https://kb-rag-fbv7.onrender.com"

def ping_service():
    """Ping the health endpoint"""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✓ Service is alive: {response.json()}")
            return True
        else:
            print(f"[{datetime.now()}] ✗ Service returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now()}] ✗ Error: {e}")
        return False

def check_storage():
    """Check storage status"""
    try:
        response = requests.get(f"{SERVICE_URL}/storage-info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            print(f"   Vector store: {'✓' if info.get('vector_store_initialized') else '✗'}")
            print(f"   Uploaded files: {len(info.get('uploaded_files', []))}")
            return info
        return None
    except Exception as e:
        print(f"   Could not check storage: {e}")
        return None

if __name__ == "__main__":
    print("=== Render Keep-Alive Service ===")
    print(f"Target: {SERVICE_URL}")
    print("Interval: 10 minutes")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            ping_service()
            check_storage()
            print("Sleeping for 10 minutes...\n")
            time.sleep(600)  # 10 minutes
        except KeyboardInterrupt:
            print("\nStopping keep-alive service.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(60)  # Wait 1 minute on error
