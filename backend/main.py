import os
import sys
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
import io
import zipfile

from fastapi.responses import StreamingResponse, FileResponse


import uvicorn

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import Config
from app.routes.analysis import router as analysis_router
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath("../prototype"))

def check_python_version():
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_env_file():
    env_file = Path("../.env")
    if not env_file.exists():
        print(".env file not found in parent directory")
        return False

    content = env_file.read_text()
    if "GROQ_API_KEYS" not in content:
        print("GROQ_API_KEYS not found in .env file")
        return False

    print("Environment configuration found")
    return True


def create_directories():
    for directory in ["results", "temp"]:
        Path(directory).mkdir(exist_ok=True)
        print(f"Ensured directory exists: {directory}")


def startup_checks():
    print("GitHub Documentation Generator - Backend Startup")
    print("=" * 60)

    check_python_version()
    check_env_file()
    create_directories()

    print("Startup checks complete")
    print("=" * 60)



app = FastAPI(
    title="GitHub Documentation Generator API",
    description="Generate comprehensive documentation from GitHub repositories",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:56769"
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
@app.get("/api/analysis/file/{output_dir}/{file_name}")
async def get_file_content(output_dir: str, file_name: str):
    """
    Fetch the content of a specific documentation file.
    """
    try:
        # Construct file path
        file_path = os.path.join(output_dir, file_name)
        
        # Security check: prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(output_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_name}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "file_name": file_name,
            "content": content,
            "size": len(content)
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


# Download documentation as ZIP
@app.get("/api/analysis/download/{output_dir}")
async def download_docs(output_dir: str):
    """
    Download the entire documentation folder as a ZIP file.
    """
    try:
        # Check if directory exists
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail="Documentation directory not found")
        
        if not os.path.isdir(output_dir):
            raise HTTPException(status_code=400, detail="Invalid directory")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Walk through the directory
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Get relative path for the archive
                    arcname = os.path.relpath(file_path, output_dir)
                    zip_file.write(file_path, arcname)
        
        # Seek to beginning of buffer
        zip_buffer.seek(0)
        
        # Return ZIP file as download
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={output_dir}.zip"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP: {str(e)}")


# List all files in documentation directory (optional but useful)
@app.get("/api/analysis/files/{output_dir}")
async def list_files(output_dir: str):
    """
    List all files in the documentation directory.
    """
    try:
        if not os.path.exists(output_dir):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        files = []
        for root, dirs, filenames in os.walk(output_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, output_dir)
                file_size = os.path.getsize(file_path)
                
                files.append({
                    "name": filename,
                    "path": rel_path,
                    "size": file_size,
                    "type": "file"
                })
        
        return {
            "success": True,
            "directory": output_dir,
            "files": files,
            "total": len(files)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


# If you're using Flask instead of FastAPI:
"""
from flask import Flask, jsonify, send_file
import os

app = Flask(__name__)

@app.route('/api/analysis/file/<output_dir>/<file_name>')
def get_file_content(output_dir, file_name):
    try:
        file_path = os.path.join(output_dir, file_name)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "file_name": file_name,
            "content": content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/download/<output_dir>')
def download_docs(output_dir):
    try:
        if not os.path.exists(output_dir):
            return jsonify({"error": "Directory not found"}), 404
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{output_dir}.zip'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""

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


if __name__ == "__main__":
    # Move to backend directory
    os.chdir(Path(__file__).parent)

    # Run startup logic
    startup_checks()

    # Load configuration
    Config.load_config()

    print("Starting GitHub Documentation Generator API")
    print(f"Results directory: {Config.RESULTS_DIR}")
    print(f"Groq API keys configured: {len(Config.GROQ_API_KEYS)}")
    print("Server: http://localhost:8000")
    print("Docs:   http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
