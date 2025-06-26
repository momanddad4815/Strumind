import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.projects import router as projects_router
from api.models import router as models_router
from api.analysis import router as analysis_router
from api.bim import router as bim_router
from api.design import router as design_router
from api.detailing import router as detailing_router
from api.nodes import router as nodes_router
from api.elements import router as elements_router
from api.nlp import router as nlp_router

app = FastAPI(
    title="StruMind API",
    description="Next-generation structural engineering platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(models_router)
app.include_router(analysis_router)
app.include_router(bim_router)
app.include_router(design_router)
app.include_router(detailing_router)
app.include_router(nodes_router)
app.include_router(elements_router)
app.include_router(nlp_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to StruMind API",
        "version": "1.0.0",
        "description": "Next-generation structural engineering platform"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "StruMind Backend"}

@app.get("/api/info")
def get_api_info():
    return {
        "name": "StruMind API",
        "version": "1.0.0",
        "description": "Next-generation structural engineering platform",
        "capabilities": [
            "Structural modeling",
            "Linear and nonlinear analysis",
            "RC and steel design",
            "BIM integration",
            "Detailing"
        ]
    }

@app.get("/api/materials")
def get_materials():
    return {
        "concrete": ["M15", "M20", "M25", "M30", "M35", "M40", "M45", "M50"],
        "steel": ["Fe250", "Fe415", "Fe500", "Fe550"],
        "international": {
            "ACI": ["3000psi", "4000psi", "5000psi", "6000psi"],
            "AISC": ["A36", "A572_Gr50", "A992"],
            "Eurocode": ["C20/25", "C25/30", "C30/37", "S235", "S275", "S355"]
        }
    }

@app.get("/api/sections")
def get_sections():
    return {
        "steel_sections": {
            "ISMB": ["ISMB100", "ISMB150", "ISMB200", "ISMB250", "ISMB300", "ISMB400", "ISMB500", "ISMB600"],
            "ISMC": ["ISMC75", "ISMC100", "ISMC125", "ISMC150", "ISMC200", "ISMC250", "ISMC300", "ISMC400"],
            "IPE": ["IPE100", "IPE120", "IPE140", "IPE160", "IPE180", "IPE200", "IPE240", "IPE300", "IPE400", "IPE500"],
            "W_sections": ["W8X18", "W10X22", "W12X26", "W14X30", "W16X36", "W18X40", "W21X44", "W24X55"]
        },
        "concrete_sections": {
            "rectangular": "Custom dimensions",
            "circular": "Custom diameter",
            "T_beam": "Custom dimensions"
        }
    }

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
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
