"""Knowledge graph construction from code analysis."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import networkx as nx
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from analysis_models import DetailedFileAnalysis
from graph_models import GraphNode, GraphEdge, KnowledgeGraph

class KnowledgeGraphBuilder:
    """Builds a comprehensive knowledge graph from code analysis."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = []
        self.edges = []
    
    def build_graph(self, files_data: List[DetailedFileAnalysis]) -> KnowledgeGraph:
        """Build knowledge graph from analyzed files."""
        print("🔗 Building knowledge graph...")
        
        # Step 1: Add file nodes
        self._add_file_nodes(files_data)
        
        # Step 2: Add function and class nodes
        self._add_code_element_nodes(files_data)
        
        # Step 3: Add dependency edges
        self._add_dependency_edges(files_data)
        
        # Step 4: Add call relationships
        self._add_call_relationships(files_data)
        
        # Step 5: Add containment relationships
        self._add_containment_relationships(files_data)
        
        # Step 6: Calculate graph metrics
        self._calculate_graph_metrics()
        
        knowledge_graph = KnowledgeGraph(
            nodes=self.nodes,
            edges=self.edges,
            metadata={
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": self._get_node_type_counts(),
                "edge_types": self._get_edge_type_counts()
            }
        )
        
        print(f"✅ Knowledge graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
        return knowledge_graph
    
    def _add_file_nodes(self, files_data: List[DetailedFileAnalysis]):
        """Add file nodes to the graph."""
        for file_data in files_data:
            node_id = f"file:{file_data.file}"
            
            # Determine file category
            file_category = self._categorize_file(file_data)
            
            node = GraphNode(
                id=node_id,
                type="file",
                name=Path(file_data.file).name,
                path=file_data.file,
                metadata={
                    "language": file_data.language,
                    "category": file_category,
                    "lines_of_code": file_data.lines_of_code,
                    "complexity_score": file_data.complexity_score,
                    "function_count": len(file_data.functions),
                    "class_count": len(file_data.classes),
                    "api_endpoint_count": len(file_data.api_endpoints),
                    "service_info": file_data.service_info.__dict__ if file_data.service_info else None
                }
            )
            
            self.nodes.append(node)
            self.graph.add_node(node_id, **node.metadata)
    
    def _add_code_element_nodes(self, files_data: List[DetailedFileAnalysis]):
        """Add function and class nodes."""
        for file_data in files_data:
            file_node_id = f"file:{file_data.file}"
            
            # Add function nodes
            for func in file_data.functions:
                func_id = f"function:{file_data.file}:{func.name}"
                
                func_node = GraphNode(
                    id=func_id,
                    type="function",
                    name=func.name,
                    path=file_data.file,
                    metadata={
                        "parameters": func.params,
                        "line": func.line,
                        "is_async": func.is_async,
                        "is_exported": func.is_exported,
                        "return_type": func.return_type,
                        "complexity": getattr(func, 'complexity', 0)
                    }
                )
                
                self.nodes.append(func_node)
                self.graph.add_node(func_id, **func_node.metadata)
                
                # Add containment edge (file contains function)
                self._add_edge(file_node_id, func_id, "contains", 1.0)
            
            # Add class nodes
            for cls in file_data.classes:
                cls_id = f"class:{file_data.file}:{cls.name}"
                
                cls_node = GraphNode(
                    id=cls_id,
                    type="class",
                    name=cls.name,
                    path=file_data.file,
                    metadata={
                        "methods": cls.methods,
                        "line": cls.line,
                        "extends": cls.extends,
                        "implements": cls.implements,
                        "is_exported": cls.is_exported
                    }
                )
                
                self.nodes.append(cls_node)
                self.graph.add_node(cls_id, **cls_node.metadata)
                
                # Add containment edge (file contains class)
                self._add_edge(file_node_id, cls_id, "contains", 1.0)
    
    def _add_dependency_edges(self, files_data: List[DetailedFileAnalysis]):
        """Add import and dependency edges."""
        for file_data in files_data:
            source_id = f"file:{file_data.file}"
            
            for imp in file_data.imports:
                # Handle internal imports (relative paths)
                if imp.source.startswith('.') or imp.source.startswith('/'):
                    # Try to resolve relative import to actual file
                    target_file = self._resolve_import_path(file_data.file, imp.source)
                    if target_file:
                        target_id = f"file:{target_file}"
                        self._add_edge(source_id, target_id, "imports", 1.0, {
                            "import_line": imp.line,
                            "imported_names": imp.imported_names
                        })
                else:
                    # External dependency
                    dep_id = f"external:{imp.source.split('/')[0]}"
                    
                    # Add external dependency node if not exists
                    if not any(node.id == dep_id for node in self.nodes):
                        dep_node = GraphNode(
                            id=dep_id,
                            type="external_dependency",
                            name=imp.source.split('/')[0],
                            metadata={
                                "full_name": imp.source,
                                "is_external": True
                            }
                        )
                        self.nodes.append(dep_node)
                        self.graph.add_node(dep_id, **dep_node.metadata)
                    
                    self._add_edge(source_id, dep_id, "depends_on", 1.0, {
                        "import_line": imp.line,
                        "imported_names": imp.imported_names
                    })
    
    def _add_call_relationships(self, files_data: List[DetailedFileAnalysis]):
        """Add function call relationships (simplified)."""
        for file_data in files_data:
            # Add API call relationships
            for api in file_data.api_endpoints:
                method = api.get('method') if isinstance(api, dict) else getattr(api, 'method', 'GET')
                path = api.get('path') if isinstance(api, dict) else getattr(api, 'path', '/')
                line = api.get('line') if isinstance(api, dict) else getattr(api, 'line', 0)
                function_name = api.get('function_name') if isinstance(api, dict) else getattr(api, 'function_name', None)
                parameters = api.get('parameters', []) if isinstance(api, dict) else getattr(api, 'parameters', [])
                
                api_id = f"api:{file_data.file}:{method}:{path}"
                
                # Add API endpoint node
                api_node = GraphNode(
                    id=api_id,
                    type="api_endpoint",
                    name=f"{method} {path}",
                    path=file_data.file,
                    metadata={
                        "method": method,
                        "path": path,
                        "line": line,
                        "function_name": function_name,
                        "parameters": parameters
                    }
                )
                
                self.nodes.append(api_node)
                self.graph.add_node(api_id, **api_node.metadata)
                
                # Link API to file
                file_id = f"file:{file_data.file}"
                self._add_edge(file_id, api_id, "exposes", 1.0)
                
                # Link API to handler function if known
                if function_name:
                    func_id = f"function:{file_data.file}:{function_name}"
                    self._add_edge(api_id, func_id, "handled_by", 1.0)
    
    def _add_containment_relationships(self, files_data: List[DetailedFileAnalysis]):
        """Add folder/module containment relationships."""
        folders = {}
        
        # Group files by folder
        for file_data in files_data:
            folder_path = str(Path(file_data.file).parent)
            if folder_path == '.':
                folder_path = 'root'
            
            if folder_path not in folders:
                folders[folder_path] = []
            folders[folder_path].append(file_data.file)
        
        # Add folder nodes and containment edges
        for folder_path, files in folders.items():
            folder_id = f"folder:{folder_path}"
            
            folder_node = GraphNode(
                id=folder_id,
                type="folder",
                name=Path(folder_path).name if folder_path != 'root' else 'root',
                path=folder_path,
                metadata={
                    "file_count": len(files),
                    "files": files
                }
            )
            
            self.nodes.append(folder_node)
            self.graph.add_node(folder_id, **folder_node.metadata)
            
            # Add containment edges (folder contains files)
            for file_path in files:
                file_id = f"file:{file_path}"
                self._add_edge(folder_id, file_id, "contains", 1.0)
    
    def _add_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0, metadata: Dict = None):
        """Add an edge to the graph."""
        edge = GraphEdge(
            source=source,
            target=target,
            type=edge_type,
            weight=weight,
            metadata=metadata or {}
        )
        
        self.edges.append(edge)
        self.graph.add_edge(source, target, type=edge_type, weight=weight, **edge.metadata)
    
    def _calculate_graph_metrics(self):
        """Calculate graph metrics and add to metadata."""
        if len(self.graph.nodes()) == 0:
            return
        
        # Calculate centrality measures
        try:
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            
            # Add centrality to node metadata
            for node in self.nodes:
                node.metadata["degree_centrality"] = degree_centrality.get(node.id, 0)
                node.metadata["betweenness_centrality"] = betweenness_centrality.get(node.id, 0)
        
        except Exception as e:
            print(f"⚠️ Could not calculate centrality metrics: {e}")
    
    def _categorize_file(self, file_data: DetailedFileAnalysis) -> str:
        """Categorize file based on its content and purpose."""
        if hasattr(file_data, 'file_purpose') and file_data.file_purpose:
            return file_data.file_purpose
        
        # Fallback categorization
        if file_data.api_endpoints:
            return "API Routes"
        elif file_data.jsx_components:
            return "UI Components"
        elif file_data.classes:
            return "Classes/Models"
        elif file_data.functions:
            return "Business Logic"
        else:
            return "Configuration/Other"
    
    def _resolve_import_path(self, current_file: str, import_path: str) -> Optional[str]:
        """Resolve relative import path to actual file path."""
        # Simplified implementation - in practice, you'd need more sophisticated resolution
        current_dir = Path(current_file).parent
        
        if import_path.startswith('./'):
            resolved = current_dir / import_path[2:]
        elif import_path.startswith('../'):
            resolved = current_dir / import_path
        else:
            return None
        
        # Try common extensions
        for ext in ['.js', '.ts', '.jsx', '.tsx', '.py']:
            if (resolved.with_suffix(ext)).exists():
                return str(resolved.with_suffix(ext))
        
        return None
    
    def _get_node_type_counts(self) -> Dict[str, int]:
        """Get count of nodes by type."""
        counts = {}
        for node in self.nodes:
            counts[node.type] = counts.get(node.type, 0) + 1
        return counts
    
    def _get_edge_type_counts(self) -> Dict[str, int]:
        """Get count of edges by type."""
        counts = {}
        for edge in self.edges:
            counts[edge.type] = counts.get(edge.type, 0) + 1
        return counts