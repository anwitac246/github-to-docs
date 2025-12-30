"""Summary and LLM response models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ModuleSummary(BaseModel):
    module_name: str
    module_path: str
    folders: List[str] = []
    total_files: int = 0
    primary_languages: List[str] = []
    architecture_role: str = ""
    interfaces: List[str] = []
    responsibilities: List[str] = []
    key_components: List[str] = []
    llm_summary: Optional[str] = None

class DomainSummary(BaseModel):
    domain_name: str
    modules: List[str] = []
    architecture_overview: str = ""
    data_flow: List[str] = []
    business_logic: List[str] = []
    integration_points: List[str] = []
    key_patterns: List[str] = []
    llm_summary: Optional[str] = None

class GlobalArchitectureSummary(BaseModel):
    system_overview: str = ""
    key_patterns: List[str] = []
    architectural_decisions: List[str] = []
    data_flow_summary: str = ""
    scalability_analysis: str = ""
    security_considerations: List[str] = []
    performance_insights: List[str] = []
    recommendations: List[str] = []
    technology_stack: Dict[str, List[str]] = {}
    llm_summary: Optional[str] = None

class LLMSummaryRequest(BaseModel):
    file_path: str
    content: str
    analysis: Any  # Can be FileAnalysis or DetailedFileAnalysis
    context: Dict[str, Any] = {}

class LLMSummaryResponse(BaseModel):
    file_path: str
    summary: str
    key_insights: List[str] = []
    architectural_role: str = ""
    complexity_assessment: str = ""
    improvement_suggestions: List[str] = []