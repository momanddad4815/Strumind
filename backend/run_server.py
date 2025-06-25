#!/usr/bin/env python3

import uvicorn
from main import app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏗️  STRUMIND - STRUCTURAL ENGINEERING PLATFORM")
    print("="*60)
    print("🚀 Starting StruMind Backend Server...")
    print("📡 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs") 
    print("🔍 Health: http://localhost:8000/health")
    print("ℹ️  Info: http://localhost:8000/api/info")
    print("="*60)
    print("✅ Server is ready for frontend connection!")
    print("✅ All structural engineering APIs are operational")
    print("="*60 + "\n")
    
    uvicorn.run(
        "run_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # Set to False for stability
    )
