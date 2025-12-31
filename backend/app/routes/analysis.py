"""API routes for documentation analysis."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Optional
import os
import zipfile
import tempfile
import shutil

from ..models import GitHubRequest, AnalysisResponse, AnalysisStatus
from ..services.analysis_service import analysis_service
from ..config import Config

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/github", response_model=AnalysisResponse)
async def analyze_github_repository(request: GitHubRequest):
    """Start analysis of a GitHub repository."""
    
    try:
        analysis_id = await analysis_service.start_github_analysis(
            str(request.github_url),
            request.groq_api_keys
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            message="Analysis started successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.post("/upload", response_model=AnalysisResponse)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    groq_api_keys: Optional[str] = None
):
    """Analyze an uploaded ZIP file."""
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    try:
        # Parse API keys
        api_keys = []
        if groq_api_keys:
            api_keys = [key.strip() for key in groq_api_keys.split(',') if key.strip()]
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="upload_")
        
        try:
            # Save uploaded file
            zip_path = os.path.join(temp_dir, file.filename)
            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract ZIP file
            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # TODO: Implement local file analysis
            # For now, return a placeholder response
            
            return AnalysisResponse(
                analysis_id="upload_placeholder",
                status=AnalysisStatus.PENDING,
                message="Upload analysis not yet implemented"
            )
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

@router.get("/status/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_status(analysis_id: str):
    """Get the status of an analysis."""
    
    status_data = analysis_service.get_analysis_status(analysis_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        status=status_data['status'],
        message=status_data['message'],
        progress=status_data.get('progress'),
        error=status_data.get('error')
    )

@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """Get the complete results of an analysis."""
    
    results = analysis_service.get_analysis_results(analysis_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Results not found or analysis not completed")
    
    return results

@router.get("/list")
async def list_analyses():
    """List all analyses with their status."""
    
    return {
        "analyses": analysis_service.list_analyses()
    }

@router.delete("/cleanup")
async def cleanup_old_analyses():
    """Clean up old analyses."""
    
    removed_count = analysis_service.cleanup_old_analyses()
    
    return {
        "message": f"Cleaned up {removed_count} old analyses"
    }