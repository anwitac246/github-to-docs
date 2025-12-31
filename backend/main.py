"""
Main FastAPI application + startup logic
for the GitHub Documentation Generator backend.
"""

import os
import sys
import subprocess
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import Config
from app.routes.analysis import router as analysis_router

# ============================================================
# -------------------- Startup Utilities ---------------------
# ============================================================

def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_env_file():
    env_file = Path("../.env")
    if not env_file.exists():
        print("⚠️ .env file not found in parent directory")
        return False

    content = env_file.read_text()
    if "GROQ_API_KEYS" not in content:
        print("⚠️ GROQ_API_KEYS not found in .env file")
        return False

    print("✅ Environment configuration found")
    return True


def create_directories():
    for directory in ["results", "temp"]:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Ensured directory exists: {directory}")


def startup_checks():
    print("🚀 GitHub Documentation Generator - Backend Startup")
    print("=" * 60)

    check_python_version()
    check_env_file()
    create_directories()

    print("✅ Startup checks complete")
    print("=" * 60)


# ============================================================
# -------------------- FastAPI App ----------------------------
# ============================================================

app = FastAPI(
    title="GitHub Documentation Generator API",
    description="Generate comprehensive documentation from GitHub repositories",
    version="1.0.0"
)

# CORS (Next.js / frontend ready)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analysis_router)

# Static results
if os.path.exists(Config.RESULTS_DIR):
    app.mount(
        "/results",
        StaticFiles(directory=Config.RESULTS_DIR),
        name="results"
    )


# ============================================================
# -------------------- API Endpoints --------------------------
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "GitHub Documentation Generator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze_github": "/api/analysis/github",
            "analyze_upload": "/api/analysis/upload",
            "get_status": "/api/analysis/status/{analysis_id}",
            "get_results": "/api/analysis/results/{analysis_id}",
            "list_analyses": "/api/analysis/list"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "groq_api_configured": len(Config.GROQ_API_KEYS) > 0,
        "groq_keys_count": len(Config.GROQ_API_KEYS),
        "results_directory": Config.RESULTS_DIR,
        "temp_directory": Config.TEMP_DIR
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


# ============================================================
# -------------------- Entrypoint -----------------------------
# ============================================================

if __name__ == "__main__":
    # Move to backend directory
    os.chdir(Path(__file__).parent)

    # Run startup logic
    startup_checks()

    # Load configuration
    Config.load_config()

    print("🚀 Starting GitHub Documentation Generator API")
    print(f"📁 Results directory: {Config.RESULTS_DIR}")
    print(f"🔑 Groq API keys configured: {len(Config.GROQ_API_KEYS)}")
    print("📍 Server: http://localhost:8000")
    print("📖 Docs:   http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
