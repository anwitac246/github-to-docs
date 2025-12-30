"""Base data models for code analysis."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FunctionInfo(BaseModel):
    name: str
    params: List[str] = []
    return_type: Optional[str] = None
    line: int
    complexity: int = 0
    docstring: Optional[str] = None
    is_async: bool = False
    is_exported: bool = False

class ClassInfo(BaseModel):
    name: str
    methods: List[str] = []
    line: int
    extends: Optional[str] = None
    implements: List[str] = []
    is_exported: bool = False

class ImportInfo(BaseModel):
    source: str
    line: int
    imported_names: List[str] = []
    is_default: bool = False
    is_dynamic: bool = False

class APIEndpoint(BaseModel):
    method: str
    path: str
    line: int
    handler: Optional[str] = None
    middleware: List[str] = []

class DatabaseQuery(BaseModel):
    type: str  # SELECT, INSERT, UPDATE, DELETE
    table: Optional[str] = None
    line: int
    raw_query: str

class APIEndpointDetail(BaseModel):
    method: str
    path: str
    line: int
    function_name: Optional[str] = None
    parameters: List[Dict[str, Any]] = []
    response_type: Optional[str] = None
    middleware: List[str] = []
    description: Optional[str] = None
    usage_example: Optional[str] = None

class EnvironmentVariable(BaseModel):
    name: str
    line: int
    default_value: Optional[str] = None
    description: Optional[str] = None
    required: bool = True

class ServiceInfo(BaseModel):
    type: str  # frontend, backend, database, etc.
    framework: Optional[str] = None
    port: Optional[int] = None
    dependencies: List[str] = []
    entry_point: Optional[str] = None