"""Knowledge graph models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GraphNode(BaseModel):
    id: str
    type: str  # file, function, class, module, domain
    name: str
    path: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # import, call, inheritance, dependency, contains
    weight: float = 1.0
    metadata: Dict[str, Any] = {}

class KnowledgeGraph(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    metadata: Dict[str, Any] = {}