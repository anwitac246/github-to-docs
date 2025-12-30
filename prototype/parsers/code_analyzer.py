"""Enhanced code analyzer for detailed file analysis."""

import re
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from config import get_file_language
from base_models import FunctionInfo, ClassInfo, ImportInfo, ServiceInfo, EnvironmentVariable
from analysis_models import DetailedFileAnalysis

class DetailedCodeAnalyzer:
    """Enhanced analyzer for detailed code analysis."""
    
    def __init__(self):
        pass
    
    def analyze_file_detailed(self, file_path: str, rel_path: str, content: str) -> DetailedFileAnalysis:
        """Perform detailed analysis of a single file."""
        language = get_file_language(rel_path)
        if not language:
            return None
        
        # Create detailed analysis
        detailed = DetailedFileAnalysis(
            file=rel_path,
            language=language,
            functions=[],
            classes=[],
            imports=[],
            lines_of_code=len([line for line in content.split('\n') if line.strip()])
        )
        
        # Basic parsing using existing logic
        if language in ['javascript', 'jsx', 'typescript', 'tsx']:
            self._parse_javascript_content(content, detailed)
        elif language == 'python':
            self._parse_python_content(content, detailed)
        
        # Enhanced analysis
        detailed.service_info = self._detect_service_type(content, rel_path)
        detailed.api_endpoints = self._extract_detailed_api_endpoints(content, language)
        detailed.environment_variables = self._extract_environment_variables(content)
        detailed.integration_points = self._detect_integration_points(content, language)
        detailed.file_purpose = self._determine_file_purpose(rel_path, content, detailed)
        
        return detailed
    
    def _parse_javascript_content(self, content: str, detailed: DetailedFileAnalysis):
        """Parse JavaScript content and extract basic information."""
        # Extract functions
        func_matches = re.finditer(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))', content)
        for match in func_matches:
            func_name = match.group(1) or match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            is_async = 'async' in match.group(0)
            
            detailed.functions.append(FunctionInfo(
                name=func_name,
                params=[],  # Could be enhanced to extract actual params
                line=line_num,
                is_async=is_async
            ))
        
        # Extract classes
        class_matches = re.finditer(r'class\s+(\w+)', content)
        for match in class_matches:
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            detailed.classes.append(ClassInfo(
                name=class_name,
                line=line_num
            ))
        
        # Extract imports
        import_matches = re.finditer(r'import\s+(?:[\s\S]+?)\s+from\s+["\']([^"\']+)["\']', content)
        for match in import_matches:
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            detailed.imports.append(ImportInfo(
                source=source,
                line=line_num
            ))
            
            if not source.startswith('.') and not source.startswith('/'):
                dep_name = source.split('/')[0]
                if dep_name not in detailed.dependencies:
                    detailed.dependencies.append(dep_name)
        
        # Extract JSX components
        jsx_matches = re.finditer(r'<(\w+)', content)
        for match in jsx_matches:
            component = match.group(1)
            if component[0].isupper() and component not in detailed.jsx_components:
                detailed.jsx_components.append(component)
    
    def _parse_python_content(self, content: str, detailed: DetailedFileAnalysis):
        """Parse Python content and extract basic information."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    detailed.functions.append(FunctionInfo(
                        name=node.name,
                        params=[arg.arg for arg in node.args.args],
                        line=node.lineno,
                        is_async=isinstance(node, ast.AsyncFunctionDef)
                    ))
                
                elif isinstance(node, ast.ClassDef):
                    methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
                    detailed.classes.append(ClassInfo(
                        name=node.name,
                        methods=methods,
                        line=node.lineno
                    ))
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            detailed.imports.append(ImportInfo(
                                source=alias.name,
                                line=node.lineno
                            ))
                            dep_name = alias.name.split('.')[0]
                            if dep_name not in detailed.dependencies:
                                detailed.dependencies.append(dep_name)
                    
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        detailed.imports.append(ImportInfo(
                            source=node.module,
                            line=node.lineno
                        ))
                        if not node.module.startswith('.'):
                            dep_name = node.module.split('.')[0]
                            if dep_name not in detailed.dependencies:
                                detailed.dependencies.append(dep_name)
        
        except Exception as e:
            print(f"⚠️ Python AST parsing failed: {e}")
    
    def _detect_service_type(self, content: str, file_path: str) -> Optional[ServiceInfo]:
        """Detect what type of service this file represents."""
        service_info = ServiceInfo(type="unknown")
        
        # Frontend detection
        if any(framework in content.lower() for framework in ['react', 'vue', 'angular', 'next']):
            service_info.type = "frontend"
            if 'react' in content.lower() or 'jsx' in file_path:
                service_info.framework = "React"
            elif 'next' in content.lower():
                service_info.framework = "Next.js"
            elif 'vue' in content.lower():
                service_info.framework = "Vue.js"
        
        # Backend detection
        elif any(framework in content.lower() for framework in ['express', 'fastapi', 'flask', 'django']):
            service_info.type = "backend"
            if 'express' in content.lower():
                service_info.framework = "Express.js"
            elif 'fastapi' in content.lower():
                service_info.framework = "FastAPI"
            elif 'flask' in content.lower():
                service_info.framework = "Flask"
            elif 'django' in content.lower():
                service_info.framework = "Django"
        
        # Extract port information
        port_match = re.search(r'port[:\s=]+(\d+)', content.lower())
        if port_match:
            service_info.port = int(port_match.group(1))
        
        return service_info if service_info.type != "unknown" else None
    
    def _extract_detailed_api_endpoints(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract detailed API endpoint information."""
        endpoints = []
        
        if language in ['javascript', 'typescript']:
            endpoints.extend(self._extract_js_api_endpoints(content))
        elif language == 'python':
            endpoints.extend(self._extract_python_api_endpoints(content))
        
        return endpoints
    
    def _extract_js_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract JavaScript/Node.js API endpoints."""
        endpoints = []
        
        # Express.js route patterns
        express_patterns = [
            r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in express_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                # Extract parameters from path
                path_params = re.findall(r':(\w+)', path)
                parameters = [{"name": param, "type": "path", "required": True} for param in path_params]
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "line": line_num,
                    "parameters": parameters,
                    "description": f"{method} endpoint for {path}"
                })
        
        return endpoints
    
    def _extract_python_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract Python API endpoints (FastAPI, Flask, Django)."""
        endpoints = []
        
        # FastAPI patterns
        fastapi_patterns = [
            r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        ]
        
        # Process FastAPI patterns
        for pattern in fastapi_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "line": line_num,
                    "description": f"FastAPI {method} endpoint for {path}"
                })
        
        return endpoints
    
    def _extract_environment_variables(self, content: str) -> List[EnvironmentVariable]:
        """Extract environment variable usage."""
        env_vars = []
        
        # Common environment variable patterns
        patterns = [
            r'process\.env\.(\w+)',  # Node.js
            r'os\.environ\.get\s*\(\s*["\'](\w+)["\']',  # Python os.environ.get
            r'os\.getenv\s*\(\s*["\'](\w+)["\']',  # Python os.getenv
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check if already added
                if not any(env.name == var_name for env in env_vars):
                    env_vars.append(EnvironmentVariable(
                        name=var_name,
                        line=line_num
                    ))
        
        return env_vars
    
    def _detect_integration_points(self, content: str, language: str) -> List[str]:
        """Detect integration points in the code."""
        integration_points = []
        
        # Database integrations
        if any(db in content.lower() for db in ['mongoose', 'sequelize', 'prisma', 'sqlalchemy']):
            integration_points.append("Database Integration")
        
        # External API calls
        if any(api in content.lower() for api in ['fetch(', 'axios', 'requests.', 'http.']):
            integration_points.append("External API Calls")
        
        # Authentication
        if any(auth in content.lower() for auth in ['jwt', 'passport', 'auth', 'login']):
            integration_points.append("Authentication System")
        
        return integration_points
    
    def _determine_file_purpose(self, file_path: str, content: str, detailed: DetailedFileAnalysis) -> str:
        """Determine the main purpose of the file."""
        path_lower = file_path.lower()
        
        # Check file path patterns
        if any(pattern in path_lower for pattern in ['route', 'api', 'controller']):
            return "API Routes and Controllers"
        elif any(pattern in path_lower for pattern in ['component', 'ui']):
            return "UI Components"
        elif any(pattern in path_lower for pattern in ['model', 'schema']):
            return "Data Models"
        elif any(pattern in path_lower for pattern in ['service', 'business']):
            return "Business Logic"
        elif any(pattern in path_lower for pattern in ['util', 'helper']):
            return "Utilities"
        elif any(pattern in path_lower for pattern in ['config', 'setting']):
            return "Configuration"
        elif any(pattern in path_lower for pattern in ['test', 'spec']):
            return "Tests"
        
        # Check content patterns
        if detailed.api_endpoints:
            return "API Implementation"
        elif detailed.jsx_components:
            return "Frontend Components"
        elif detailed.classes and detailed.functions:
            return "Business Logic"
        elif detailed.functions:
            return "Utility Functions"
        
        return "General Purpose"