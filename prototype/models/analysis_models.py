"""Analysis result models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from base_models import FunctionInfo, ClassInfo, ImportInfo, APIEndpoint, DatabaseQuery, EnvironmentVariable, ServiceInfo

class FileAnalysis(BaseModel):
    file: str
    language: str
    functions: List[FunctionInfo] = []
    classes: List[ClassInfo] = []
    imports: List[ImportInfo] = []
    exports: List[str] = []
    api_endpoints: List[APIEndpoint] = []
    database_queries: List[DatabaseQuery] = []
    jsx_components: List[str] = []
    dependencies: List[str] = []
    complexity_score: int = 0
    lines_of_code: int = 0
    doc: str = ""
    llm_summary: Optional[str] = None
    key_patterns: List[str] = []
    error_handling: List[str] = []

class DetailedFileAnalysis(BaseModel):
    file: str
    language: str
    service_info: Optional[ServiceInfo] = None
    functions: List[FunctionInfo] = []
    classes: List[ClassInfo] = []
    imports: List[ImportInfo] = []
    api_endpoints: List[Dict[str, Any]] = []
    database_queries: List[DatabaseQuery] = []
    environment_variables: List[EnvironmentVariable] = []
    jsx_components: List[str] = []
    dependencies: List[str] = []
    complexity_score: int = 0
    lines_of_code: int = 0
    file_purpose: Optional[str] = None
    key_patterns: List[str] = []
    integration_points: List[str] = []
    llm_summary: Optional[str] = None
    detailed_analysis: Optional[Dict[str, Any]] = None

class FolderSummary(BaseModel):
    folder_path: str
    files: List[str] = []
    total_files: int = 0
    primary_language: str = ""
    service_type: Optional[str] = None
    api_endpoints: List[Dict[str, Any]] = []
    shared_dependencies: List[str] = []
    folder_purpose: Optional[str] = None
    key_components: List[str] = []
    integration_patterns: List[str] = []
    llm_summary: Optional[str] = None