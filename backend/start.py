import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="StruMind API",
    description="Next-generation structural engineering platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to StruMind API",
        "version": "1.0.0",
        "description": "Next-generation structural engineering platform",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "StruMind Backend"}

if __name__ == "__main__":
    print("🚀 Starting StruMind Backend Server...")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("🌐 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "start:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
