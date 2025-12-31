"""Data models for the documentation generator."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from enum import Enum

class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class GitHubRequest(BaseModel):
    """Request model for GitHub repository analysis."""
    github_url: HttpUrl
    groq_api_keys: Optional[List[str]] = None

class UploadRequest(BaseModel):
    """Request model for file upload analysis."""
    groq_api_keys: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    analysis_id: str
    status: AnalysisStatus
    message: str
    progress: Optional[int] = None
    results_url: Optional[str] = None
    error: Optional[str] = None

class FileAnalysis(BaseModel):
    """Model for individual file analysis."""
    file_path: str
    language: str
    lines_of_code: int
    function_count: int
    api_count: int
    is_backend: bool
    file_purpose: str
    dependencies: List[str]

class ProjectSummary(BaseModel):
    """Model for project analysis summary."""
    total_files: int
    backend_files: int
    total_apis: int
    total_functions: int
    languages: List[str]
    analysis_time: float

class AnalysisResults(BaseModel):
    """Complete analysis results model."""
    analysis_id: str
    repository_url: str
    repository_info: Dict[str, Any]
    summary: ProjectSummary
    backend_files: List[FileAnalysis]
    all_files: List[FileAnalysis]
    output_directory: str
    documentation_files: List[str]
    created_at: str