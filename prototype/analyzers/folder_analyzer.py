"""Folder-level analysis and summarization."""

from typing import List, Dict
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from analysis_models import DetailedFileAnalysis, FolderSummary

class FolderAnalyzer:
    """Analyzes folders and creates structured summaries."""
    
    def __init__(self, llm_processor=None):
        self.llm_processor = llm_processor
    
    def analyze_folders(self, files_data: List[DetailedFileAnalysis]) -> Dict[str, FolderSummary]:
        """Analyze files grouped by folders."""
        folders = {}
        
        # Group files by folder
        for file_data in files_data:
            folder_path = str(Path(file_data.file).parent)
            if folder_path == '.':
                folder_path = 'root'
            
            if folder_path not in folders:
                folders[folder_path] = []
            folders[folder_path].append(file_data)
        
        # Create folder summaries
        folder_summaries = {}
        for folder_path, files in folders.items():
            folder_summaries[folder_path] = self._create_folder_summary(folder_path, files)
        
        return folder_summaries
    
    def _create_folder_summary(self, folder_path: str, files: List[DetailedFileAnalysis]) -> FolderSummary:
        """Create a comprehensive folder summary."""
        
        # Aggregate data
        all_api_endpoints = []
        all_dependencies = set()
        languages = {}
        service_types = set()
        
        for file_data in files:
            # Collect API endpoints
            if hasattr(file_data, 'api_endpoints'):
                for api in file_data.api_endpoints:
                    # Convert to dict if it's an object
                    if hasattr(api, '__dict__'):
                        api_dict = api.__dict__
                    elif isinstance(api, dict):
                        api_dict = api
                    else:
                        # Handle DictObject or other object types
                        api_dict = {
                            'method': getattr(api, 'method', 'GET'),
                            'path': getattr(api, 'path', '/'),
                            'line': getattr(api, 'line', 0),
                            'function_name': getattr(api, 'function_name', None),
                            'parameters': getattr(api, 'parameters', [])
                        }
                    all_api_endpoints.append(api_dict)
            
            # Collect dependencies
            all_dependencies.update(file_data.dependencies)
            
            # Count languages
            lang = file_data.language
            languages[lang] = languages.get(lang, 0) + 1
            
            # Collect service types
            if hasattr(file_data, 'service_info') and file_data.service_info:
                service_types.add(file_data.service_info.type)
        
        # Determine primary language
        primary_language = max(languages.items(), key=lambda x: x[1])[0] if languages else "unknown"
        
        # Determine service type
        service_type = list(service_types)[0] if len(service_types) == 1 else "mixed" if service_types else None
        
        # Determine folder purpose
        folder_purpose = self._determine_folder_purpose(folder_path, files)
        
        # Extract key components
        key_components = self._extract_key_components(files)
        
        return FolderSummary(
            folder_path=folder_path,
            files=[f.file for f in files],
            total_files=len(files),
            primary_language=primary_language,
            service_type=service_type,
            api_endpoints=all_api_endpoints,
            shared_dependencies=list(all_dependencies),
            folder_purpose=folder_purpose,
            key_components=key_components,
            integration_patterns=self._detect_integration_patterns(files)
        )
    
    def _determine_folder_purpose(self, folder_path: str, files: List[DetailedFileAnalysis]) -> str:
        """Determine the main purpose of a folder."""
        path_lower = folder_path.lower()
        
        # Common folder patterns
        if any(pattern in path_lower for pattern in ['route', 'api', 'controller']):
            return "API Routes and Controllers"
        elif any(pattern in path_lower for pattern in ['component', 'ui', 'view']):
            return "UI Components"
        elif any(pattern in path_lower for pattern in ['model', 'schema', 'entity']):
            return "Data Models and Schemas"
        elif any(pattern in path_lower for pattern in ['service', 'business', 'logic']):
            return "Business Logic Services"
        elif any(pattern in path_lower for pattern in ['util', 'helper', 'lib']):
            return "Utilities and Helpers"
        elif any(pattern in path_lower for pattern in ['config', 'setting']):
            return "Configuration"
        elif any(pattern in path_lower for pattern in ['test', 'spec']):
            return "Tests"
        elif 'middleware' in path_lower:
            return "Middleware"
        elif 'public' in path_lower or 'static' in path_lower:
            return "Static Assets"
        
        # Analyze file contents
        api_files = sum(1 for f in files if hasattr(f, 'api_endpoints') and f.api_endpoints)
        component_files = sum(1 for f in files if f.jsx_components)
        
        if api_files > len(files) * 0.5:
            return "API Implementation"
        elif component_files > len(files) * 0.5:
            return "Frontend Components"
        elif any(hasattr(f, 'service_info') and f.service_info and f.service_info.type == 'backend' for f in files):
            return "Backend Services"
        elif any(hasattr(f, 'service_info') and f.service_info and f.service_info.type == 'frontend' for f in files):
            return "Frontend Application"
        
        return "General Purpose"
    
    def _extract_key_components(self, files: List[DetailedFileAnalysis]) -> List[str]:
        """Extract key components from files in the folder."""
        components = []
        
        for file_data in files:
            # Add main functions
            if file_data.functions:
                main_functions = [f.name for f in file_data.functions[:2]]  # Top 2 functions
                components.extend(main_functions)
            
            # Add classes
            if file_data.classes:
                class_names = [c.name for c in file_data.classes[:2]]  # Top 2 classes
                components.extend(class_names)
            
            # Add JSX components
            if file_data.jsx_components:
                components.extend(file_data.jsx_components[:2])  # Top 2 components
        
        return list(set(components))[:10]  # Limit to 10 unique components
    
    def _detect_integration_patterns(self, files: List[DetailedFileAnalysis]) -> List[str]:
        """Detect integration patterns in the folder."""
        patterns = set()
        
        for file_data in files:
            if hasattr(file_data, 'integration_points'):
                patterns.update(file_data.integration_points)
        
        return list(patterns)