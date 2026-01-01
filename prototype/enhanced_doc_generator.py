"""Enhanced GitHub documentation generator - creates comprehensive documentation files."""

import os
import sys
import subprocess
import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import threading

# Install required packages quickly
REQUIRED_PACKAGES = ['requests', 'aiohttp', 'pydantic', 'gitpython', 'markdown']

def install_packages():
    """Install packages in background."""
    print('Installing packages in background...')
    for pkg in REQUIRED_PACKAGES:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], 
                      capture_output=True, check=False)

# Start package installation in background
install_thread = threading.Thread(target=install_packages)
install_thread.start()

import re
import tempfile
import shutil
from urllib.parse import urlparse
from dataclasses import dataclass
from git import Repo
import aiohttp

@dataclass
class EnhancedAPIEndpoint:
    method: str
    path: str
    function_name: str = ""
    line: int = 0
    file_path: str = ""
    code_snippet: str = ""
    parameters: List[Dict] = None
    description: str = ""
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []

@dataclass
class EnhancedFunction:
    name: str
    params: List[str]
    file_path: str
    line: int
    language: str
    code_snippet: str = ""
    is_api_handler: bool = False
    return_type: str = ""
    docstring: str = ""
    complexity: str = "Medium"

@dataclass
class EnhancedFileAnalysis:
    file_path: str
    language: str
    functions: List[EnhancedFunction]
    api_endpoints: List[EnhancedAPIEndpoint]
    lines_of_code: int
    is_backend: bool = False
    file_purpose: str = ""
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
class ProgressTracker:
    """Track and display progress of analysis."""
    
    def __init__(self):
        self.total_files = 0
        self.processed_files = 0
        self.start_time = time.time()
        self.current_stage = "Initializing"
        self.lock = threading.Lock()
    
    def set_total_files(self, total: int):
        with self.lock:
            self.total_files = total
    
    def update_stage(self, stage: str):
        with self.lock:
            self.current_stage = stage
            print(f"🔄 {stage}")
    
    def increment_processed(self):
        with self.lock:
            self.processed_files += 1
            if self.total_files > 0:
                progress = (self.processed_files / self.total_files) * 100
                elapsed = time.time() - self.start_time
                if self.processed_files > 0:
                    eta = (elapsed / self.processed_files) * (self.total_files - self.processed_files)
                    print(f"Progress: {self.processed_files}/{self.total_files} ({progress:.1f}%) - ETA: {eta:.0f}s")

class EnhancedCodeExtractor:
    """Enhanced code extraction with detailed analysis."""
    
    def __init__(self):
        self.progress = ProgressTracker()
    
    def extract_enhanced_analysis(self, file_path: str, content: str, language: str) -> EnhancedFileAnalysis:
        """Extract enhanced analysis with detailed information."""
        
        functions = []
        api_endpoints = []
        dependencies = []
        lines = content.split('\n')
        
        if language in ['javascript', 'typescript']:
            functions, api_endpoints, dependencies = self._extract_js_enhanced(lines, file_path, language, content)
        elif language == 'python':
            functions, api_endpoints, dependencies = self._extract_python_enhanced(lines, file_path, language, content)
        
        # Determine file purpose
        file_purpose = self._determine_file_purpose(file_path, content, api_endpoints, functions)
        
        # Determine if this is a backend file
        is_backend = (
            len(api_endpoints) > 0 or
            any(keyword in content.lower() for keyword in ['express', 'fastapi', 'flask', 'router', 'app.']) or
            any(keyword in file_path.lower() for keyword in ['api', 'server', 'route', 'controller'])
        )
        
        return EnhancedFileAnalysis(
            file_path=file_path,
            language=language,
            functions=functions,
            api_endpoints=api_endpoints,
            lines_of_code=len([line for line in lines if line.strip()]),
            is_backend=is_backend,
            file_purpose=file_purpose,
            dependencies=dependencies
        )
    
    def _extract_js_enhanced(self, lines: List[str], file_path: str, language: str, content: str):
        """Extract enhanced JavaScript/TypeScript analysis."""
        functions = []
        api_endpoints = []
        dependencies = []
        
        # Extract dependencies
        for line in lines:
            import_match = re.search(r'import.*from\s+["\']([^"\']+)["\']', line)
            if import_match:
                dep = import_match.group(1)
                if not dep.startswith('.') and not dep.startswith('/'):
                    dependencies.append(dep.split('/')[0])
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Enhanced API endpoint detection
            api_match = re.search(r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line_stripped, re.IGNORECASE)
            if api_match:
                method = api_match.group(2).upper()
                path = api_match.group(3)
                
                # Extract parameters from path
                path_params = re.findall(r':(\w+)', path)
                parameters = [{"name": param, "type": "path", "required": True, "description": f"Path parameter {param}"} for param in path_params]
                
                # Get enhanced code snippet
                snippet_lines = lines[i:i+8]
                code_snippet = '\n'.join(snippet_lines)
                
                # Generate description
                description = f"API endpoint for {method} requests to {path}"
                
                api_endpoints.append(EnhancedAPIEndpoint(
                    method=method,
                    path=path,
                    line=i+1,
                    file_path=file_path,
                    code_snippet=code_snippet,
                    parameters=parameters,
                    description=description
                ))
            
            # Next.js API routes
            nextjs_api_match = re.search(r'export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)?\s*\([^)]*(?:req|request)[^)]*(?:res|response)[^)]*\)', line_stripped, re.IGNORECASE)
            if nextjs_api_match and ('api' in file_path.lower() or 'pages' in file_path.lower()):
                func_name = nextjs_api_match.group(1) or "handler"
                
                snippet_lines = lines[i:i+10]
                code_snippet = '\n'.join(snippet_lines)
                
                # Next.js API routes handle multiple methods
                for method in ['GET', 'POST', 'PUT', 'DELETE']:
                    api_endpoints.append(EnhancedAPIEndpoint(
                        method=method,
                        path=f"/api/{Path(file_path).stem}",
                        function_name=func_name,
                        line=i+1,
                        file_path=file_path,
                        code_snippet=code_snippet,
                        description=f"Next.js API route handler for {method} requests"
                    ))
                break
            
            # Enhanced function detection
            func_match = re.search(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))', line_stripped)
            if func_match:
                func_name = func_match.group(1) or func_match.group(2)
                
                # Extract parameters with better parsing
                param_match = re.search(r'\(([^)]*)\)', line_stripped)
                params = []
                if param_match:
                    param_str = param_match.group(1).strip()
                    if param_str:
                        params = [p.strip().split('=')[0].strip() for p in param_str.split(',')]
                
                # Extract docstring/comments
                docstring = ""
                for j in range(max(0, i-3), i):
                    if lines[j].strip().startswith('//') or lines[j].strip().startswith('/*'):
                        docstring += lines[j].strip() + " "
                
                # Determine complexity
                complexity = self._determine_complexity(lines[i:i+20])
                
                snippet_lines = lines[i:i+10]
                code_snippet = '\n'.join(snippet_lines)
                
                functions.append(EnhancedFunction(
                    name=func_name,
                    params=params,
                    file_path=file_path,
                    line=i+1,
                    language=language,
                    code_snippet=code_snippet,
                    is_api_handler='req' in line_stripped and 'res' in line_stripped,
                    docstring=docstring.strip(),
                    complexity=complexity
                ))
        
        return functions, api_endpoints, list(set(dependencies))
    
    def _extract_python_enhanced(self, lines: List[str], file_path: str, language: str, content: str):
        """Extract enhanced Python analysis."""
        functions = []
        api_endpoints = []
        dependencies = []
        
        # Extract dependencies
        for line in lines:
            import_matches = [
                re.search(r'from\s+(\w+)', line),
                re.search(r'import\s+(\w+)', line)
            ]
            for match in import_matches:
                if match:
                    dep = match.group(1)
                    if dep not in ['os', 'sys', 'json', 're', 'time']:  # Skip standard library
                        dependencies.append(dep)
        
        i = 0
        while i < len(lines):
            line_stripped = lines[i].strip()
            
            # Enhanced Flask route detection
            flask_route_match = re.search(r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:[^)]*methods\s*=\s*\[([^\]]+)\])?', line_stripped, re.IGNORECASE)
            if flask_route_match:
                path = flask_route_match.group(1)
                methods_str = flask_route_match.group(2)
                
                methods = ['GET']
                if methods_str:
                    methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
                
                # Find function definition
                func_name = ""
                for j in range(i+1, min(i+5, len(lines))):
                    func_match = re.search(r'def\s+(\w+)\s*\(', lines[j].strip())
                    if func_match:
                        func_name = func_match.group(1)
                        break
                
                # Extract parameters from path
                path_params = re.findall(r'<(\w+)>', path)
                parameters = [{"name": param, "type": "path", "required": True, "description": f"Path parameter {param}"} for param in path_params]
                
                snippet_lines = lines[i:i+12]
                code_snippet = '\n'.join(snippet_lines)
                
                for method in methods:
                    api_endpoints.append(EnhancedAPIEndpoint(
                        method=method.upper(),
                        path=path,
                        function_name=func_name,
                        line=i+1,
                        file_path=file_path,
                        code_snippet=code_snippet,
                        parameters=parameters,
                        description=f"Flask route for {method} requests to {path}"
                    ))
            
            # FastAPI endpoints
            api_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line_stripped, re.IGNORECASE)
            if api_match:
                method = api_match.group(1).upper()
                path = api_match.group(2)
                
                func_name = ""
                for j in range(i+1, min(i+5, len(lines))):
                    func_match = re.search(r'def\s+(\w+)\s*\(', lines[j].strip())
                    if func_match:
                        func_name = func_match.group(1)
                        break
                
                snippet_lines = lines[i:i+12]
                code_snippet = '\n'.join(snippet_lines)
                
                api_endpoints.append(EnhancedAPIEndpoint(
                    method=method,
                    path=path,
                    function_name=func_name,
                    line=i+1,
                    file_path=file_path,
                    code_snippet=code_snippet,
                    description=f"FastAPI endpoint for {method} requests to {path}"
                ))
            
            # Enhanced function detection
            func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if func_match:
                func_name = func_match.group(1)
                param_str = func_match.group(2).strip()
                
                params = []
                if param_str:
                    params = [p.strip().split(':')[0].strip() for p in param_str.split(',') if p.strip()]
                
                # Extract docstring
                docstring = ""
                if i+1 < len(lines) and '"""' in lines[i+1]:
                    for j in range(i+1, min(i+10, len(lines))):
                        if '"""' in lines[j]:
                            docstring += lines[j].strip() + " "
                            if lines[j].count('"""') == 2 or (j > i+1 and '"""' in lines[j]):
                                break
                
                # Determine return type
                return_type = ""
                return_match = re.search(r'->\s*([^:]+):', line_stripped)
                if return_match:
                    return_type = return_match.group(1).strip()
                
                complexity = self._determine_complexity(lines[i:i+20])
                
                snippet_lines = lines[i:i+12]
                code_snippet = '\n'.join(snippet_lines)
                
                functions.append(EnhancedFunction(
                    name=func_name,
                    params=params,
                    file_path=file_path,
                    line=i+1,
                    language=language,
                    code_snippet=code_snippet,
                    is_api_handler=any(keyword in line_stripped.lower() for keyword in ['request', 'response', 'req', 'res']),
                    return_type=return_type,
                    docstring=docstring.strip(),
                    complexity=complexity
                ))
            
            i += 1
        
        return functions, api_endpoints, list(set(dependencies))
    
    def _determine_complexity(self, lines: List[str]) -> str:
        """Determine function complexity based on code patterns."""
        code_text = '\n'.join(lines)
        
        # Count complexity indicators
        complexity_score = 0
        complexity_score += len(re.findall(r'\bif\b', code_text))
        complexity_score += len(re.findall(r'\bfor\b', code_text))
        complexity_score += len(re.findall(r'\bwhile\b', code_text))
        complexity_score += len(re.findall(r'\btry\b', code_text))
        complexity_score += len(re.findall(r'\bexcept\b', code_text))
        
        if complexity_score <= 2:
            return "Low"
        elif complexity_score <= 5:
            return "Medium"
        else:
            return "High"
    
    def _determine_file_purpose(self, file_path: str, content: str, api_endpoints: List, functions: List) -> str:
        """Determine the main purpose of the file."""
        path_lower = file_path.lower()
        
        # Check file path patterns
        if any(pattern in path_lower for pattern in ['route', 'api', 'controller']):
            return "API Routes and Controllers"
        elif any(pattern in path_lower for pattern in ['component', 'ui', 'page']):
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
        if api_endpoints:
            return "API Implementation"
        elif 'component' in content.lower() or 'jsx' in content.lower():
            return "Frontend Components"
        elif len(functions) > 5:
            return "Business Logic"
        elif 'config' in content.lower():
            return "Configuration"
        
        return "General Purpose"

class EnhancedLLMProcessor:
    """Enhanced LLM processor for comprehensive documentation."""
    """Enhanced LLM processor for comprehensive documentation."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
    
    async def process_files_comprehensive(self, files_data: List[EnhancedFileAnalysis]) -> Dict[str, Any]:
        """Process files with comprehensive LLM analysis."""
        
        if not self.api_keys:
            return {"error": "No API keys provided"}
        
        print(f"Processing {len(files_data)} files with comprehensive LLM analysis...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for file_analysis in files_data:
                try:
                    # Create comprehensive prompt
                    prompt = self._create_comprehensive_prompt(file_analysis)
                    
                    # Call LLM
                    response = await self._call_llm_comprehensive(session, prompt)
                    
                    results[file_analysis.file_path] = {
                        "comprehensive_documentation": response,
                        "file_analysis": {
                            "purpose": file_analysis.file_purpose,
                            "api_count": len(file_analysis.api_endpoints),
                            "function_count": len(file_analysis.functions),
                            "language": file_analysis.language,
                            "lines_of_code": file_analysis.lines_of_code,
                            "dependencies": file_analysis.dependencies,
                            "is_backend": file_analysis.is_backend
                        },
                        "apis": [
                            {
                                "method": api.method,
                                "path": api.path,
                                "function": api.function_name,
                                "description": api.description,
                                "parameters": api.parameters
                            } for api in file_analysis.api_endpoints
                        ],
                        "functions": [
                            {
                                "name": func.name,
                                "params": func.params,
                                "return_type": func.return_type,
                                "complexity": func.complexity,
                                "docstring": func.docstring,
                                "is_api_handler": func.is_api_handler
                            } for func in file_analysis.functions
                        ]
                    }
                    
                    print(f"Processed {file_analysis.file_path}")
                    
                except Exception as e:
                    print(f"Error processing {file_analysis.file_path}: {e}")
                    results[file_analysis.file_path] = {"error": str(e)}
        
        return results
    
    def _create_comprehensive_prompt(self, file_analysis: EnhancedFileAnalysis) -> str:
        """Create comprehensive prompt for detailed documentation."""
        
        prompt = f"""Create COMPREHENSIVE documentation for this {file_analysis.language} file:

FILE: {file_analysis.file_path}
PURPOSE: {file_analysis.file_purpose}
LANGUAGE: {file_analysis.language}
LINES OF CODE: {file_analysis.lines_of_code}
API ENDPOINTS: {len(file_analysis.api_endpoints)}
FUNCTIONS: {len(file_analysis.functions)}
DEPENDENCIES: {', '.join(file_analysis.dependencies[:10])}

"""
        
        # Add detailed API information
        if file_analysis.api_endpoints:
            prompt += "DETAILED API ENDPOINTS:\n"
            for api in file_analysis.api_endpoints:
                prompt += f"\n{api.method} {api.path}\n"
                prompt += f"Function: {api.function_name}\n"
                prompt += f"Description: {api.description}\n"
                if api.parameters:
                    prompt += f"Parameters: {api.parameters}\n"
                prompt += f"Code:\n```{file_analysis.language}\n{api.code_snippet}\n```\n"
        
        # Add detailed function information
        if file_analysis.functions:
            prompt += "\nDETAILED FUNCTIONS:\n"
            for func in file_analysis.functions[:8]:  # Limit to 8 functions
                prompt += f"\n{func.name}({', '.join(func.params)})\n"
                prompt += f"Return Type: {func.return_type}\n"
                prompt += f"Complexity: {func.complexity}\n"
                prompt += f"Docstring: {func.docstring}\n"
                prompt += f"Code:\n```{file_analysis.language}\n{func.code_snippet}\n```\n"
        
        prompt += """
Create COMPREHENSIVE documentation with these sections:

## FILE_OVERVIEW
- Complete description of file purpose and role
- Architecture context and relationships
- Key responsibilities and functionality

## API_DOCUMENTATION (if applicable)
For each API endpoint provide:
- Complete purpose and business logic
- Detailed parameter documentation with types, validation, examples
- Complete request/response examples with real data
- Authentication and authorization requirements
- Error handling with all possible error codes and responses
- Rate limiting and usage guidelines
- Integration examples with frontend code

## FUNCTION_DOCUMENTATION
For each function provide:
- Complete purpose and algorithm description
- Detailed parameter documentation with types and constraints
- Return value documentation with examples
- Usage examples and integration patterns
- Error handling and edge cases
- Performance considerations

## SETUP_AND_DEPLOYMENT
- Complete environment setup instructions
- All required dependencies with versions
- Environment variables with descriptions and examples
- Database setup and configuration (if applicable)
- Step-by-step deployment instructions
- Docker configuration (if applicable)
- Testing instructions

## USAGE_EXAMPLES
- Complete working examples for all major functionality
- cURL commands for all API endpoints
- JavaScript/Python client examples
- Integration examples with popular frameworks
- Real-world usage scenarios

## TROUBLESHOOTING
- Common issues and solutions
- Error message explanations
- Performance optimization tips
- Debugging guidelines

## SECURITY_CONSIDERATIONS
- Authentication and authorization details
- Input validation and sanitization
- Security best practices
- Vulnerability prevention

Focus on creating PRODUCTION-READY documentation that allows developers to immediately understand, use, and deploy this code.
"""
        
        return prompt
    
    async def _call_llm_comprehensive(self, session: aiohttp.ClientSession, prompt: str) -> str:
        """Call LLM API with comprehensive prompt."""
        
        api_key = self.api_keys[self.current_key_index % len(self.api_keys)]
        self.current_key_index += 1
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert technical documentation writer. Create comprehensive, production-ready documentation with complete examples and detailed explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,  # Increased for comprehensive docs
            "temperature": 0.1
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=45)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    return f"API Error {response.status}: {error_text[:300]}"
        
        except Exception as e:
            return f"Request failed: {str(e)}"

class DocumentationFileGenerator:
    """Generate multiple documentation file formats."""
    
    def __init__(self, output_dir: str = "docs_output"):
        self.output_dir = output_dir
        
        # Clean up old documentation directories (keep only last 3)
        self._cleanup_old_docs()
        
        # Create new output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def _cleanup_old_docs(self):
        """Clean up old documentation directories to keep workspace tidy."""
        try:
            # Find all docs directories
            docs_dirs = []
            for item in os.listdir('.'):
                if os.path.isdir(item) and item.startswith('docs_'):
                    # Extract timestamp from directory name
                    try:
                        timestamp = int(item.split('_')[-1])
                        docs_dirs.append((timestamp, item))
                    except (ValueError, IndexError):
                        continue
            
            # Sort by timestamp and keep only the 3 most recent
            docs_dirs.sort(reverse=True)
            
            # Remove old directories (keep only 3 most recent)
            for _, old_dir in docs_dirs[3:]:
                try:
                    shutil.rmtree(old_dir)
                    print(f"Cleaned up old documentation: {old_dir}")
                except Exception as e:
                    print(f"Could not remove old docs directory {old_dir}: {e}")
                    
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def generate_all_documentation_files(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate comprehensive documentation files."""
        
        print(f"Generating comprehensive documentation files in {self.output_dir}/")
        
        # 1. Generate comprehensive README
        self._generate_comprehensive_readme(analysis_results, repo_info)
        
        # 2. Generate comprehensive API documentation
        self._generate_comprehensive_api_docs(analysis_results, repo_info)
        
        # 3. Generate Code of Conduct
        self._generate_code_of_conduct(repo_info)
        
        # 4. Generate Project Summary
        self._generate_project_summary(analysis_results, repo_info)
        
        # 5. Generate setup guide
        self._generate_setup_guide(analysis_results, repo_info)
        
        # 6. Generate function reference
        self._generate_function_reference(analysis_results)
        
        # 7. Generate architecture overview
        self._generate_architecture_overview(analysis_results)
        
        # 8. Generate deployment guide
        self._generate_deployment_guide(analysis_results)
        
        # 9. Generate troubleshooting guide
        self._generate_troubleshooting_guide(analysis_results)
        
        # 10. Generate individual file docs
        self._generate_individual_file_docs(analysis_results)
        
        print(f"Generated comprehensive documentation in {self.output_dir}/")
    
    def _generate_main_readme(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate main README.md file."""
        
        readme_content = f"""# {repo_info.get('name', 'Repository')} Documentation

{repo_info.get('description', 'Comprehensive API and code documentation')}

## Repository Overview

- **Total Files Analyzed**: {analysis_results.get('summary', {}).get('total_files', 0)}
- **Backend Files**: {analysis_results.get('summary', {}).get('backend_files', 0)}
- **API Endpoints**: {analysis_results.get('summary', {}).get('total_apis', 0)}
- **Functions**: {analysis_results.get('summary', {}).get('total_functions', 0)}
- **Languages**: {', '.join(analysis_results.get('summary', {}).get('languages', []))}

## Quick Start

1. **Setup**: See [Setup Guide](./SETUP.md)
2. **API Reference**: See [API Documentation](./API.md)
3. **Deployment**: See [Deployment Guide](./DEPLOYMENT.md)
4. **Troubleshooting**: See [Troubleshooting Guide](./TROUBLESHOOTING.md)

## Documentation Structure

- [`API.md`](./API.md) - Complete API documentation with examples
- [`SETUP.md`](./SETUP.md) - Environment setup and installation
- [`FUNCTIONS.md`](./FUNCTIONS.md) - Function reference documentation
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) - System architecture overview
- [`DEPLOYMENT.md`](./DEPLOYMENT.md) - Deployment and production setup
- [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) - Common issues and solutions
- [`files/`](./files/) - Individual file documentation

## API Endpoints Summary

"""
        
        # Add API endpoints summary
        backend_files = analysis_results.get('backend_files', [])
        for file_data in backend_files:
            if file_data.get('api_count', 0) > 0:
                readme_content += f"\n### {file_data['file_path']}\n"
                for api in file_data.get('apis', []):
                    readme_content += f"- `{api['method']} {api['path']}` - {api.get('function', 'Handler')}\n"
        
        readme_content += f"""

## 🛠 Technology Stack

{', '.join(analysis_results.get('summary', {}).get('languages', []))}

## Analysis Statistics

- Analysis completed in {analysis_results.get('analysis_time', 0):.1f} seconds
- Documentation generated with LLM assistance
- Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

*This documentation was automatically generated by the Enhanced GitHub Documentation Analyzer.*
"""
        
        with open(f"{self.output_dir}/README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _generate_api_documentation(self, analysis_results: Dict[str, Any]):
        """Generate comprehensive API documentation."""
        
        api_content = """# API Documentation

Complete API reference with examples and usage instructions.

## Table of Contents

"""
        
        # Generate table of contents
        backend_files = analysis_results.get('backend_files', [])
        for file_data in backend_files:
            if file_data.get('api_count', 0) > 0:
                api_content += f"- [{file_data['file_path']}](#{file_data['file_path'].replace('/', '').replace('.', '').lower()})\n"
        
        api_content += "\n---\n\n"
        
        # Generate detailed API documentation
        api_docs = analysis_results.get('api_documentation', {})
        for file_path, doc_data in api_docs.items():
            if isinstance(doc_data, dict) and 'comprehensive_documentation' in doc_data:
                api_content += f"## {file_path}\n\n"
                api_content += doc_data['comprehensive_documentation']
                api_content += "\n\n---\n\n"
        
        with open(f"{self.output_dir}/API.md", 'w', encoding='utf-8') as f:
            f.write(api_content)
    
    def _generate_setup_guide(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate setup and installation guide."""
        
        setup_content = f"""# Setup Guide

Complete setup instructions for {repo_info.get('name', 'this project')}.

## Prerequisites

Based on the analysis, this project uses:
{', '.join(analysis_results.get('summary', {}).get('languages', []))}

### System Requirements

"""
        
        languages = analysis_results.get('summary', {}).get('languages', [])
        
        if 'python' in languages:
            setup_content += """
#### Python Requirements
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On macOS/Linux:
source venv/bin/activate
```
"""
        
        if 'javascript' in languages:
            setup_content += """
#### Node.js Requirements
- Node.js 16.0 or higher
- npm or yarn package manager

```bash
# Check Node.js version
node --version

# Check npm version
npm --version
```
"""
        
        setup_content += """
## Installation Steps

### 1. Clone the Repository

```bash
git clone [repository-url]
cd [repository-name]
```

### 2. Install Dependencies

"""
        
        if 'python' in languages:
            setup_content += """
#### Python Dependencies
```bash
pip install -r requirements.txt
```
"""
        
        if 'javascript' in languages:
            setup_content += """
#### Node.js Dependencies
```bash
npm install
# or
yarn install
```
"""
        
        setup_content += """
### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Add your environment variables here
# Example:
# DATABASE_URL=your_database_url
# API_KEY=your_api_key
```

### 4. Database Setup (if applicable)

```bash
# Run database migrations
# Add specific commands based on your database setup
```

### 5. Start the Application

"""
        
        if 'python' in languages:
            setup_content += """
#### Python Application
```bash
python app.py
# or
flask run
# or
uvicorn main:app --reload
```
"""
        
        if 'javascript' in languages:
            setup_content += """
#### Node.js Application
```bash
npm start
# or
npm run dev
# or
yarn start
```
"""
        
        setup_content += """
## Verification

After setup, verify the installation:

1. Check if the application starts without errors
2. Test API endpoints (see [API Documentation](./API.md))
3. Run any available tests

## Next Steps

- Review the [API Documentation](./API.md)
- Check the [Architecture Overview](./ARCHITECTURE.md)
- See [Deployment Guide](./DEPLOYMENT.md) for production setup
"""
        
        with open(f"{self.output_dir}/SETUP.md", 'w', encoding='utf-8') as f:
            f.write(setup_content)
    
    def _generate_function_reference(self, analysis_results: Dict[str, Any]):
        """Generate function reference documentation."""
        
        func_content = """# Function Reference

Complete reference for all functions in the codebase.

## Table of Contents

"""
        
        # Generate function documentation
        all_files = analysis_results.get('all_files', [])
        for file_data in all_files:
            if file_data.get('function_count', 0) > 0:
                func_content += f"- [{file_data['file_path']}](#{file_data['file_path'].replace('/', '').replace('.', '').lower()})\n"
        
        func_content += "\n---\n\n"
        
        # Add detailed function documentation
        backend_files = analysis_results.get('backend_files', [])
        for file_data in backend_files:
            if file_data.get('function_count', 0) > 0:
                func_content += f"## {file_data['file_path']}\n\n"
                
                for func in file_data.get('functions', []):
                    func_content += f"### `{func['name']}({', '.join(func['params'])})`\n\n"
                    
                    if func.get('docstring'):
                        func_content += f"**Description**: {func['docstring']}\n\n"
                    
                    func_content += f"**Parameters**: {', '.join(func['params']) if func['params'] else 'None'}\n\n"
                    
                    if func.get('return_type'):
                        func_content += f"**Returns**: {func['return_type']}\n\n"
                    
                    func_content += f"**Complexity**: {func.get('complexity', 'Medium')}\n\n"
                    
                    if func.get('is_api_handler'):
                        func_content += "**Type**: API Handler Function\n\n"
                    
                    func_content += "---\n\n"
        
        with open(f"{self.output_dir}/FUNCTIONS.md", 'w', encoding='utf-8') as f:
            f.write(func_content)
    
    def _generate_architecture_overview(self, analysis_results: Dict[str, Any]):
        """Generate architecture overview."""
        
        arch_content = f"""# Architecture Overview

System architecture and component relationships.

## System Statistics

- **Total Files**: {analysis_results.get('summary', {}).get('total_files', 0)}
- **Backend Components**: {analysis_results.get('summary', {}).get('backend_files', 0)}
- **API Endpoints**: {analysis_results.get('summary', {}).get('total_apis', 0)}
- **Functions**: {analysis_results.get('summary', {}).get('total_functions', 0)}

## Technology Stack

{', '.join(analysis_results.get('summary', {}).get('languages', []))}

## Component Overview

### Backend Components

"""
        
        backend_files = analysis_results.get('backend_files', [])
        for file_data in backend_files:
            arch_content += f"#### {file_data['file_path']}\n"
            arch_content += f"- **Language**: {file_data['language']}\n"
            arch_content += f"- **API Endpoints**: {file_data.get('api_count', 0)}\n"
            arch_content += f"- **Functions**: {file_data.get('function_count', 0)}\n"
            arch_content += f"- **Lines of Code**: {file_data.get('lines_of_code', 0)}\n\n"
        
        arch_content += """
### Frontend Components

"""
        
        all_files = analysis_results.get('all_files', [])
        frontend_files = [f for f in all_files if not f.get('is_backend', False)]
        
        for file_data in frontend_files:
            if file_data.get('function_count', 0) > 0:
                arch_content += f"#### {file_data['file_path']}\n"
                arch_content += f"- **Language**: {file_data['language']}\n"
                arch_content += f"- **Functions**: {file_data.get('function_count', 0)}\n"
                arch_content += f"- **Lines of Code**: {file_data.get('lines_of_code', 0)}\n\n"
        
        arch_content += """
## Data Flow

[Describe the data flow between components]

## Security Architecture

[Describe security measures and authentication flow]

## Scalability Considerations

[Describe how the system can scale]
"""
        
        with open(f"{self.output_dir}/ARCHITECTURE.md", 'w', encoding='utf-8') as f:
            f.write(arch_content)
    
    def _generate_deployment_guide(self, analysis_results: Dict[str, Any]):
        """Generate deployment guide."""
        
        deploy_content = """# Deployment Guide

Production deployment instructions and best practices.

## Production Environment Setup

### Environment Variables

Create a production `.env` file with:

```env
NODE_ENV=production
# Add your production environment variables
```

### Database Configuration

[Add database setup instructions]

### Security Configuration

[Add security setup instructions]

## Deployment Options

### Option 1: Traditional Server Deployment

### Option 2: Docker Deployment

### Option 3: Cloud Platform Deployment

## Monitoring and Logging

[Add monitoring setup instructions]

## Backup and Recovery

[Add backup procedures]
"""
        
        with open(f"{self.output_dir}/DEPLOYMENT.md", 'w', encoding='utf-8') as f:
            f.write(deploy_content)
    
    def _generate_troubleshooting_guide(self, analysis_results: Dict[str, Any]):
        """Generate troubleshooting guide."""
        
        trouble_content = """# Troubleshooting Guide

Common issues and solutions.

## Common Issues

### Installation Issues

### Runtime Issues

### API Issues

### Database Issues

## Error Messages

### Common Error Codes

### Debugging Steps

## Performance Issues

### Optimization Tips

## Getting Help

- Check the logs
- Review the API documentation
- Contact support
"""
        
        with open(f"{self.output_dir}/TROUBLESHOOTING.md", 'w', encoding='utf-8') as f:
            f.write(trouble_content)
    
    def _generate_individual_file_docs(self, analysis_results: Dict[str, Any]):
        """Generate individual file documentation."""
        
        files_dir = f"{self.output_dir}/files"
        os.makedirs(files_dir, exist_ok=True)
        
        api_docs = analysis_results.get('api_documentation', {})
        
        for file_path, doc_data in api_docs.items():
            if isinstance(doc_data, dict) and 'comprehensive_documentation' in doc_data:
                # Create safe filename
                safe_filename = file_path.replace('/', '_').replace('\\', '_').replace('.', '_') + '.md'
                
                file_content = f"""# {file_path}

{doc_data['comprehensive_documentation']}

---

*Generated automatically from code analysis*
"""
                
                with open(f"{files_dir}/{safe_filename}", 'w', encoding='utf-8') as f:
                    f.write(file_content)
    
    def _generate_comprehensive_readme(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate comprehensive README.md with full project documentation."""
        
        # Determine project type and features based on analysis
        languages = analysis_results.get('summary', {}).get('languages', [])
        backend_files = analysis_results.get('backend_files', [])
        total_apis = analysis_results.get('summary', {}).get('total_apis', 0)
        
        # Detect project type
        project_type = "Software Project"
        if any("healthcare" in f.get('file_path', '').lower() or 
               "medical" in f.get('file_path', '').lower() for f in backend_files):
            project_type = "Healthcare AI Agent"
        elif any("chat" in f.get('file_path', '').lower() or 
                 "bot" in f.get('file_path', '').lower() for f in backend_files):
            project_type = "AI Chatbot Platform"
        elif total_apis > 10:
            project_type = "API Platform"
        
        readme_content = f"""# {repo_info.get('name', 'Project')} 

<!-- GitHub Badges -->
<div align="center">

[![Stars](https://img.shields.io/github/stars/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/stargazers)
[![Forks](https://img.shields.io/github/forks/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/network/members)
[![Issues](https://img.shields.io/github/issues/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/issues)
[![License](https://img.shields.io/github/license/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/commits)

<!-- Technology Badges -->
"""
        
        # Add technology badges based on detected languages and dependencies
        tech_badges = []
        
        if 'python' in languages:
            tech_badges.append("![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)")
        if 'javascript' in languages or 'typescript' in languages:
            tech_badges.append("![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)")
        if 'typescript' in languages:
            tech_badges.append("![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)")
        
        # Add framework badges based on dependencies
        all_dependencies = set()
        for file_data in backend_files:
            all_dependencies.update(file_data.get('dependencies', []))
        
        if 'flask' in all_dependencies:
            tech_badges.append("![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)")
        if 'fastapi' in all_dependencies:
            tech_badges.append("![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)")
        if 'react' in str(all_dependencies).lower():
            tech_badges.append("![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)")
        if 'next' in str(all_dependencies).lower():
            tech_badges.append("![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)")
        if 'firebase' in all_dependencies:
            tech_badges.append("![Firebase](https://img.shields.io/badge/Firebase-039BE5?style=for-the-badge&logo=Firebase&logoColor=white)")
        if 'tensorflow' in all_dependencies:
            tech_badges.append("![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)")
        if 'docker' in str(all_dependencies).lower():
            tech_badges.append("![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)")
        
        # Add tech badges to README
        for badge in tech_badges:
            readme_content += f"{badge}\n"
        
        readme_content += f"""
<!-- Project Stats -->
![Code Size](https://img.shields.io/github/languages/code-size/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})
![Repo Size](https://img.shields.io/github/repo-size/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})
![Contributors](https://img.shields.io/github/contributors/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})

</div>

---

## Project Statistics

<div align="center">

| Metric | Value |
|-----------|----------|
| **Total Files** | {analysis_results.get('summary', {}).get('total_files', 0)} |
| **Backend Services** | {len(backend_files)} |
| **API Endpoints** | {total_apis} |
| **Functions** | {analysis_results.get('summary', {}).get('total_functions', 0)} |
| **Languages** | {', '.join([lang.title() for lang in languages])} |
| **Analysis Time** | {analysis_results.get('analysis_time', 0):.1f}s |

</div>

## Overview

{repo_info.get('description', f'A comprehensive {project_type.lower()} with advanced features and modern architecture.')}

This is a full-stack {project_type.lower()} that combines modern technologies to provide a robust and scalable solution. The platform includes **{total_apis} API endpoints** across **{len(backend_files)} backend services**, implementing **{analysis_results.get('summary', {}).get('total_functions', 0)} functions** with comprehensive functionality.

## Key Features

"""
        
        # Generate features based on detected APIs and files
        features = []
        
        for file_data in backend_files:
            file_path = file_data.get('file_path', '').lower()
            apis = file_data.get('apis', [])
            
            if 'chat' in file_path or 'bot' in file_path:
                features.append("**AI-Powered Conversations**: Advanced chatbot with natural language processing")
            if 'ambulance' in file_path or 'emergency' in file_path:
                features.append("**Emergency Services**: Real-time ambulance location and dispatch system")
            if 'location' in file_path or 'doctor' in file_path:
                features.append("***Healthcare Provider Network**: Find and connect with medical professionals")
            if 'document' in file_path:
                features.append("**Document Processing**: AI-powered document analysis and extraction")
            if 'yoga' in file_path or 'exercise' in file_path:
                features.append("**Wellness Tracking**: Exercise monitoring and pose detection")
            if 'video' in file_path or 'room' in file_path:
                features.append("**Video Consultations**: Real-time video calls and telemedicine")
            if 'appointment' in file_path:
                features.append("**Appointment Management**: Comprehensive scheduling system")
            if 'auth' in file_path or 'login' in file_path:
                features.append("**Secure Authentication**: Multi-factor authentication and user management")
        
        # Add generic features if none detected
        if not features:
            features = [
                f"**{len(backend_files)} Backend Services**: Microservices architecture with specialized functionality",
                f"**{total_apis} API Endpoints**: Comprehensive REST API with full documentation",
                f"**High Performance**: Optimized code with {analysis_results.get('summary', {}).get('total_functions', 0)} functions",
                "**Security First**: Built-in security measures and best practices"
            ]
        
        for feature in features[:8]:  # Limit to 8 features
            readme_content += f"### {feature}\n"
        
        readme_content += f"""

## 🛠 Technology Stack

### Backend ({', '.join([lang.title() for lang in languages if lang == 'python'])})
"""
        
        # Detect backend technologies
        backend_techs = []
        dependencies = set()
        
        for file_data in backend_files:
            dependencies.update(file_data.get('dependencies', []))
        
        if 'flask' in dependencies:
            backend_techs.append("**Flask**: Web framework for API development")
        if 'fastapi' in dependencies:
            backend_techs.append("**FastAPI**: Modern, fast web framework for building APIs")
        if 'groq' in dependencies or 'Groq' in dependencies:
            backend_techs.append("**Groq**: AI/ML model integration for natural language processing")
        if 'mediapipe' in dependencies:
            backend_techs.append("**MediaPipe**: Computer vision for pose detection and tracking")
        if 'firebase' in dependencies:
            backend_techs.append("**Firebase**: Authentication and database services")
        if 'tensorflow' in dependencies:
            backend_techs.append("**TensorFlow**: Machine learning framework")
        if 'opencv' in dependencies or 'cv2' in dependencies:
            backend_techs.append("**OpenCV**: Computer vision processing")
        
        for tech in backend_techs:
            readme_content += f"- {tech}\n"
        
        if 'javascript' in languages:
            readme_content += f"""
### Frontend (Next.js/React)
- **Next.js 14**: React framework with App Router
- **React**: Component-based UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Socket.io**: Real-time communication
"""
        
        readme_content += f"""

## Project Structure

<details>
<summary><strong>Click to expand project structure</strong></summary>

```
{repo_info.get('name', 'project')}/
├── Backend Services ({len([f for f in backend_files if f.get('language') == 'python'])})
"""
        
        # Add backend files structure with better formatting
        for file_data in backend_files:
            if file_data.get('language') == 'python':
                api_count = file_data.get('api_count', 0)
                func_count = file_data.get('function_count', 0)
                purpose_emoji = ""
                if 'auth' in file_data['file_path'].lower():
                    purpose_emoji = ""
                elif 'api' in file_data['file_path'].lower():
                    purpose_emoji = ""
                elif 'service' in file_data['file_path'].lower():
                    purpose_emoji = ""
                
                readme_content += f"│   ├── {purpose_emoji} {file_data['file_path']:<25} # {file_data.get('file_purpose', 'Service')} ({api_count} APIs, {func_count} funcs)\n"
        
        # Add frontend structure if JavaScript files exist
        frontend_files = [f for f in analysis_results.get('all_files', []) if not f.get('is_backend', False)]
        if frontend_files:
            readme_content += f"├── Frontend Application ({len(frontend_files)} files)\n"
            
            # Group frontend files by type
            pages = [f for f in frontend_files if 'page' in f.get('file_path', '').lower()]
            components = [f for f in frontend_files if 'component' in f.get('file_path', '').lower()]
            
            if pages:
                readme_content += f"│   ├── Pages ({len(pages)} files)\n"
                for file_data in pages[:3]:  # Show first 3
                    readme_content += f"│   │   ├── {file_data['file_path']}\n"
                if len(pages) > 3:
                    readme_content += f"│   │   └── ... and {len(pages) - 3} more\n"
            
            if components:
                readme_content += f"│   ├── Components ({len(components)} files)\n"
                for file_data in components[:3]:  # Show first 3
                    readme_content += f"│   │   ├── {file_data['file_path']}\n"
                if len(components) > 3:
                    readme_content += f"│   │   └── ... and {len(components) - 3} more\n"
        
        readme_content += f"""└── Configuration Files
    ├── Environment configs
    ├── Package managers
    └── Deployment scripts
```

</details>

## 🛠 Technology Stack

<div align="center">

### Backend Technologies
| Technology | Purpose | Files | Usage |
|------------|---------|-------|-------|
"""
        
        # Enhanced technology analysis
        tech_usage = {}
        for file_data in backend_files:
            deps = file_data.get('dependencies', [])
            for dep in deps:
                if dep not in tech_usage:
                    tech_usage[dep] = {'files': 0, 'purpose': 'Development'}
                tech_usage[dep]['files'] += 1
        
        # Add major technologies to the table
        major_techs = {
            'flask': ('Web Framework', 'REST API development'),
            'fastapi': ('API Framework', 'High-performance APIs'),
            'firebase': ('Backend Service', 'Authentication & Database'),
            'tensorflow': ('ML Framework', 'Machine Learning'),
            'opencv': ('Computer Vision', 'Image Processing'),
            'react': ('UI Library', 'Frontend Components'),
            'next': ('React Framework', 'Full-stack Development')
        }
        
        for tech, (category, purpose) in major_techs.items():
            if tech in tech_usage:
                readme_content += f"| **{tech.title()}** | {category} | {tech_usage[tech]['files']} | {purpose} |\n"
        
        readme_content += f"""

### Frontend Technologies  
| Technology | Purpose | Description |
|------------|---------|-------------|
"""
        
        if 'javascript' in languages or 'typescript' in languages:
            readme_content += """| **React** | UI Framework | Component-based user interface |
| **Next.js** | Full-stack | Server-side rendering & routing |
| **TypeScript** | Type Safety | Enhanced JavaScript with types |
| **Tailwind CSS** | Styling | Utility-first CSS framework |
"""
        
        readme_content += f"""
</div>

## Quick Start

<div align="center">

### Prerequisites

</div>

"""
        
        if 'python' in languages:
            readme_content += "- **Python 3.8+**\n"
        if 'javascript' in languages:
            readme_content += "- **Node.js 18+**\n"
        
        # Add service-specific prerequisites
        if 'firebase' in dependencies:
            readme_content += "- **Firebase Account**\n"
        if 'google' in str(dependencies).lower():
            readme_content += "- **Google API Keys**\n"
        if 'groq' in dependencies or 'Groq' in dependencies:
            readme_content += "- **Groq API Key**\n"
        
        readme_content += """
### Installation

<div align="center">

#### Get Started in 3 Steps

</div>

<details>
<summary><strong>Step 1: Clone the Repository</strong></summary>

```bash
# Clone the repository
git clone https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}.git

# Navigate to project directory
cd {repo_info.get('name', 'repo')}
```

</details>

<details>
<summary><strong>Step 2: Backend Setup</strong></summary>

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

</details>

"""
        
        if 'javascript' in languages:
            readme_content += """<details>
<summary><strong>Step 3: Frontend Setup</strong></summary>

```bash
# Install Node.js dependencies
npm install
# or
yarn install

# Start development server
npm run dev
# or
yarn dev
```

</details>

"""
            readme_content += """
3. **Frontend Setup**
```bash
# Install Node.js dependencies
npm install

# Configure environment
# Update configuration files with your settings
```
"""
        
        readme_content += """
4. **Environment Configuration**
Create a `.env` file with the following variables:
```env
"""
        
        # Add environment variables based on detected services
        if 'groq' in dependencies or 'Groq' in dependencies:
            readme_content += "# AI/ML APIs\nGROQ_API_KEY=your_groq_api_key\n"
        if 'google' in str(dependencies).lower():
            readme_content += "# Google Services\nGOOGLE_MAPS_API_KEY=your_google_maps_api_key\n"
        if 'firebase' in dependencies:
            readme_content += "# Firebase Configuration\nFIREBASE_API_KEY=your_firebase_api_key\n"
        
        readme_content += """```

### Running the Application

1. **Start Backend Services**
```bash
"""
        
        # Add start commands for each backend service
        for i, file_data in enumerate(backend_files):
            if file_data.get('language') == 'python' and file_data.get('api_count', 0) > 0:
                service_name = file_data['file_path'].replace('.py', '')
                port = 5000 + i
                readme_content += f"# Start the {service_name} service\npython {file_data['file_path']}\n\n"
        
        if 'javascript' in languages:
            readme_content += """```

2. **Start Frontend Application**
```bash
# Development mode
npm run dev

# Production build
npm run build
npm start
```
"""
        else:
            readme_content += "```\n"
        
        readme_content += f"""
3. **Access the Application**
- Backend APIs: http://localhost:5000 (and other ports)
"""
        
        if 'javascript' in languages:
            readme_content += "- Frontend: http://localhost:3000\n"
        
        readme_content += f"""

## API Documentation

### API Overview
This project provides {total_apis} API endpoints across {len(backend_files)} services:

"""
        
        # Add API summary
        for file_data in backend_files:
            if file_data.get('api_count', 0) > 0:
                readme_content += f"#### {file_data['file_path']}\n"
                readme_content += f"**Base URL**: `http://localhost:500X`\n\n"
                readme_content += "**Endpoints**:\n"
                
                for api in file_data.get('apis', []):
                    readme_content += f"- `{api['method']} {api['path']}` - {api.get('description', 'API endpoint')}\n"
                
                readme_content += "\n"
        
        readme_content += """
For complete API documentation with examples, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## Configuration

### Service Configuration
Each service can be configured through environment variables and configuration files.

### Security Setup
- Enable authentication for production use
- Configure API rate limiting
- Set up proper CORS policies
- Use HTTPS in production

## Testing

### API Testing
```bash
# Test individual services
curl -X GET http://localhost:5000/health

# Run automated tests
pytest tests/
```

## Deployment

### Production Deployment
```bash
# Using Docker
docker build -t project-backend .
docker run -p 5000:5000 project-backend
```

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) for details on our code of conduct.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Email: support@project.com
- Issues: [GitHub Issues]({repo_info.get('url', '')}/issues)
- Documentation: [Project Wiki]({repo_info.get('url', '')}/wiki)

## Acknowledgments

"""
        
        # Add acknowledgments based on detected technologies
        acknowledgments = []
        if 'groq' in dependencies or 'Groq' in dependencies:
            acknowledgments.append("- **Groq** for AI model infrastructure")
        if 'google' in str(dependencies).lower():
            acknowledgments.append("- **Google** for Maps and API services")
        if 'firebase' in dependencies:
            acknowledgments.append("- **Firebase** for authentication and database services")
        if 'mediapipe' in dependencies:
            acknowledgments.append("- **MediaPipe** for computer vision capabilities")
        if 'flask' in dependencies:
            acknowledgments.append("- **Flask** team for the excellent web framework")
        if 'next' in str(dependencies).lower():
            acknowledgments.append("- **Next.js** team for the React framework")
        
        for ack in acknowledgments:
            readme_content += f"{ack}\n"
        
        readme_content += f"""

---

<div align="center">

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

[![Contributors](https://img.shields.io/github/contributors/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/graphs/contributors)
[![Pull Requests](https://img.shields.io/github/issues-pr/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/pulls)
[![Code Quality](https://img.shields.io/codacy/grade/a/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})](https://app.codacy.com/gh/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[![License](https://img.shields.io/github/license/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}?style=for-the-badge)](LICENSE)

## Support & Community

<div align="center">

| Platform | Link | Purpose |
|----------|------|---------|
| **Issues** | [GitHub Issues](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/issues) | Bug reports & feature requests |
| **Discussions** | [GitHub Discussions](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/discussions) | Community chat & Q&A |
| **Wiki** | [Project Wiki](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/wiki) | Documentation & guides |
| **Email** | support@{repo_info.get('name', 'project').lower()}.com | Direct support |

</div>

## Show Your Support

If this project helped you, please consider giving it a ⭐on GitHub!

[![GitHub stars](https://img.shields.io/github/stars/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}?style=social)](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}?style=social)](https://github.com/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')}/network/members)

## Project Stats

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})
![GitHub last commit](https://img.shields.io/github/last-commit/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})
![GitHub release](https://img.shields.io/github/v/release/{repo_info.get('owner', 'user')}/{repo_info.get('name', 'repo')})

---

<div align="center">

**Project Status**: Active Development  
**Last Updated**: {time.strftime('%Y-%m-%d')}  
**Version**: 1.0.0  
**Analysis Time**: {analysis_results.get('analysis_time', 0):.1f}s  
**Total Files**: {analysis_results.get('summary', {}).get('total_files', 0)}  
**API Endpoints**: {analysis_results.get('summary', {}).get('total_apis', 0)}

**Made with love by the development team**

*This documentation was automatically generated by the Enhanced GitHub Documentation Analyzer*

</div>

</div>
"""
        
        with open(f"{self.output_dir}/README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _generate_comprehensive_api_docs(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate comprehensive API documentation with detailed examples."""
        
        backend_files = analysis_results.get('backend_files', [])
        total_apis = analysis_results.get('summary', {}).get('total_apis', 0)
        
        api_content = f"""# {repo_info.get('name', 'Project')} - API Documentation 📚

Complete API reference with examples and usage instructions.

## Overview

The {repo_info.get('name', 'project')} provides {total_apis} API endpoints across {len(backend_files)} services.

## API Endpoints

"""
        
        # Add API documentation for each backend file
        for file_data in backend_files:
            if file_data.get('api_count', 0) > 0:
                api_content += f"### {file_data['file_path']}\n\n"
                
                for api in file_data.get('apis', []):
                    api_content += f"#### `{api['method']} {api['path']}`\n\n"
                    api_content += f"**Description**: {api.get('description', 'API endpoint')}\n\n"
                    
                    # Add example
                    api_content += f"""**Example**:
```bash
curl -X {api['method']} http://localhost:5000{api['path']}
```

"""
        
        api_content += """
## Error Handling

All APIs return standard HTTP status codes and JSON error responses.

## Rate Limiting

Rate limits are applied per service to ensure fair usage.
"""
        
        with open(f"{self.output_dir}/API_DOCUMENTATION.md", 'w', encoding='utf-8') as f:
            f.write(api_content)
    
    def _get_api_group_name(self, file_path: str) -> str:
        """Get API group name based on file path."""
        return "🔧 Core APIs"
    
    def _generate_code_of_conduct(self, repo_info: Dict[str, Any]):
        """Generate comprehensive Code of Conduct."""
        
        project_name = repo_info.get('name', 'Project')
        
        conduct_content = f"""# Code of Conduct

## Our Pledge

We pledge to make participation in our {project_name} community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment include:

- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team.

---

**Last Updated**: {time.strftime('%Y-%m-%d')}
"""
        
        with open(f"{self.output_dir}/CODE_OF_CONDUCT.md", 'w', encoding='utf-8') as f:
            f.write(conduct_content)
    
    def _generate_project_summary(self, analysis_results: Dict[str, Any], repo_info: Dict[str, Any]):
        """Generate comprehensive project summary with technical details."""
        
        summary_data = analysis_results.get('summary', {})
        project_name = repo_info.get('name', 'Project')
        total_files = summary_data.get('total_files', 0)
        total_apis = summary_data.get('total_apis', 0)
        total_functions = summary_data.get('total_functions', 0)
        
        summary_content = f"""# {project_name} - Project Summary

## Project Overview

The {project_name} is a comprehensive software platform with {total_files} files, {total_apis} APIs, and {total_functions} functions.

## Project Statistics

- **Total Files**: {total_files}
- **Total APIs**: {total_apis}
- **Total Functions**: {total_functions}
- **Analysis Time**: {analysis_results.get('analysis_time', 0):.1f}s

## Architecture

The project follows modern software architecture principles with clear separation of concerns.

---

**Project Status**: Complete and Production-Ready  
**Last Updated**: {time.strftime('%Y-%m-%d')}
"""
        
        with open(f"{self.output_dir}/PROJECT_SUMMARY.md", 'w', encoding='utf-8') as f:
            f.write(summary_content)

class EnhancedGitHubAnalyzer:
    """Enhanced GitHub repository analyzer with comprehensive documentation generation."""
    """Enhanced GitHub repository analyzer with comprehensive documentation generation."""
    
    def __init__(self):
        self.temp_dir = None
        self.progress = ProgressTracker()
    
    async def analyze_repository_comprehensive(self, repo_url: str, api_keys: List[str] = None) -> Dict[str, Any]:
        """Comprehensive analysis with detailed documentation generation."""
        
        start_time = time.time()
        
        try:
            # Step 1: Clone repository
            self.progress.update_stage("Cloning repository...")
            repo_path = self._clone_repo(repo_url)
            
            # Step 2: Fast file scanning
            self.progress.update_stage("Scanning files...")
            all_files = self._scan_files_fast(repo_path)
            
            if not all_files:
                return {"error": "No code files found"}
            
            self.progress.set_total_files(len(all_files))
            print(f"Found {len(all_files)} code files")
            
            # Step 3: Enhanced extraction
            self.progress.update_stage("Performing enhanced code analysis...")
            extractor = EnhancedCodeExtractor()
            
            analyzed_files = []
            backend_files = []
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for file_path, content, language in all_files:
                    future = executor.submit(
                        extractor.extract_enhanced_analysis,
                        file_path, content, language
                    )
                    futures.append(future)
                
                for future in futures:
                    try:
                        file_analysis = future.result()
                        analyzed_files.append(file_analysis)
                        
                        if file_analysis.is_backend:
                            backend_files.append(file_analysis)
                        
                        self.progress.increment_processed()
                        
                    except Exception as e:
                        print(f"Error analyzing file: {e}")
            
            print(f"Found {len(backend_files)} backend files with APIs")
            
            # Step 4: Comprehensive LLM processing
            llm_results = {}
            if api_keys and analyzed_files:
                self.progress.update_stage("Generating comprehensive documentation with LLM...")
                llm_processor = EnhancedLLMProcessor(api_keys)
                
                # Process all files (not just backend) for comprehensive docs
                files_to_process = [f for f in analyzed_files if f.functions or f.api_endpoints]
                llm_results = await llm_processor.process_files_comprehensive(files_to_process)
            
            # Step 5: Compile comprehensive results
            self.progress.update_stage("Compiling comprehensive results...")
            
            total_apis = sum(len(f.api_endpoints) for f in analyzed_files)
            total_functions = sum(len(f.functions) for f in analyzed_files)
            
            # Get repository info
            repo_info = self._get_repo_info(repo_url)
            
            results = {
                "repository_url": repo_url,
                "repository_info": repo_info,
                "analysis_time": time.time() - start_time,
                "summary": {
                    "total_files": len(analyzed_files),
                    "backend_files": len(backend_files),
                    "total_apis": total_apis,
                    "total_functions": total_functions,
                    "languages": list(set(f.language for f in analyzed_files))
                },
                "backend_files": [
                    {
                        "file_path": f.file_path,
                        "language": f.language,
                        "file_purpose": f.file_purpose,
                        "api_count": len(f.api_endpoints),
                        "function_count": len(f.functions),
                        "lines_of_code": f.lines_of_code,
                        "dependencies": f.dependencies,
                        "apis": [
                            {
                                "method": api.method,
                                "path": api.path,
                                "function": api.function_name,
                                "line": api.line,
                                "description": api.description,
                                "parameters": api.parameters
                            } for api in f.api_endpoints
                        ],
                        "functions": [
                            {
                                "name": func.name,
                                "params": func.params,
                                "line": func.line,
                                "return_type": func.return_type,
                                "complexity": func.complexity,
                                "docstring": func.docstring,
                                "is_api_handler": func.is_api_handler
                            } for func in f.functions
                        ]
                    } for f in backend_files
                ],
                "api_documentation": llm_results,
                "all_files": [
                    {
                        "file_path": f.file_path,
                        "language": f.language,
                        "file_purpose": f.file_purpose,
                        "lines_of_code": f.lines_of_code,
                        "function_count": len(f.functions),
                        "is_backend": f.is_backend,
                        "dependencies": f.dependencies
                    } for f in analyzed_files
                ]
            }
            
            # Step 6: Generate comprehensive documentation files
            if api_keys:
                self.progress.update_stage("Generating comprehensive documentation files...")
                
                # Create unique output directory for this repository
                repo_name = repo_info.get('name', 'repository')
                timestamp = int(time.time())
                unique_output_dir = f"docs_{repo_name}_{timestamp}"
                
                doc_generator = DocumentationFileGenerator(unique_output_dir)
                doc_generator.generate_all_documentation_files(results, repo_info)
                
                # Store output directory in results for later reference
                results["output_directory"] = unique_output_dir
            
            elapsed = time.time() - start_time
            print(f"Comprehensive analysis complete in {elapsed:.1f}s!")
            print(f"Summary: {len(analyzed_files)} files, {len(backend_files)} backend, {total_apis} APIs, {total_functions} functions")
            
            if api_keys:
                output_dir = results.get("output_directory", "docs_output")
                print(f"Comprehensive documentation generated in {output_dir}/")
            
            return results
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {"error": str(e)}
        
        finally:
            self._cleanup()
    
    def _clone_repo(self, repo_url: str) -> str:
        """Clone repository to temp directory."""
        
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        
        owner, repo_name = path_parts[0], path_parts[1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix=f'{repo_name}_')
        
        # Clone repository
        clone_url = f'https://github.com/{owner}/{repo_name}.git'
        Repo.clone_from(clone_url, self.temp_dir)
        
        return self.temp_dir
    
    def _scan_files_fast(self, repo_path: str) -> List[tuple]:
        """Fast file scanning - only get code files."""
        
        SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'dist', 'build', '.next', 'coverage', 'venv', 'env'}
        EXTENSIONS = {'.js': 'javascript', '.mjs': 'javascript', '.jsx': 'javascript', 
                     '.ts': 'typescript', '.tsx': 'typescript', '.py': 'python'}
        
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            
            for filename in filenames:
                # Check if it's a code file
                ext = Path(filename).suffix.lower()
                if ext in EXTENSIONS:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Skip very large files (>100KB for comprehensive analysis)
                        if len(content) > 100000:
                            continue
                        
                        files.append((rel_path, content, EXTENSIONS[ext]))
                        
                    except Exception:
                        continue
        
        return files
    
    def _get_repo_info(self, repo_url: str) -> Dict[str, str]:
        """Get repository information."""
        
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner, repo_name = path_parts[0], path_parts[1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            return {
                "name": repo_name,
                "owner": owner,
                "url": repo_url,
                "description": f"Comprehensive documentation for {repo_name}"
            }
        
        return {
            "name": "Repository",
            "owner": "Unknown",
            "url": repo_url,
            "description": "Comprehensive repository documentation"
        }
    
    def _cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"⚠️ Could not clean up temp directory: {e}")

async def main():
    """Main entry point for enhanced analyzer."""
    
    # Wait for package installation to complete
    install_thread.join()
    print('✅ Package installation complete!')
    
    print("🚀 Enhanced GitHub Documentation Generator")
    print("=" * 60)
    
    # Get input
    repo_url = input("Enter GitHub repository URL: ").strip()
    if not repo_url:
        print("❌ Repository URL is required")
        return
    
    api_keys_input = input("Enter Groq API keys (comma-separated, optional): ").strip()
    api_keys = []
    if api_keys_input:
        api_keys = [key.strip() for key in api_keys_input.split(',') if key.strip()]
        print(f"🔑 Using {len(api_keys)} API keys for comprehensive documentation generation")
    else:
        print("ℹ️ No API keys - will extract code structure but skip LLM documentation")
    
    # Run comprehensive analysis
    analyzer = EnhancedGitHubAnalyzer()
    results = await analyzer.analyze_repository_comprehensive(repo_url, api_keys)
    
    # Save results
    if "error" not in results:
        output_file = f"comprehensive_analysis_{int(time.time())}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Complete analysis results saved to {output_file}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
        
        # Print comprehensive summary
        summary = results["summary"]
        print(f"\n📊 Comprehensive Analysis Summary:")
        print(f"   Analysis time: {results['analysis_time']:.1f}s")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Backend files: {summary['backend_files']}")
        print(f"   API endpoints: {summary['total_apis']}")
        print(f"   Functions: {summary['total_functions']}")
        print(f"   Languages: {', '.join(summary['languages'])}")
        
        if api_keys:
            doc_count = len(results.get("api_documentation", {}))
            output_dir = results.get("output_directory", "docs_output")
            print(f"   Comprehensive docs generated: {doc_count}")
            print(f"   📚 Documentation files created in: {output_dir}/")
            print(f"   📖 Main README: {output_dir}/README.md")
            print(f"   📋 API Documentation: {output_dir}/API_DOCUMENTATION.md")
            print(f"   📜 Code of Conduct: {output_dir}/CODE_OF_CONDUCT.md")
            print(f"   📊 Project Summary: {output_dir}/PROJECT_SUMMARY.md")
            print(f"   🔧 Setup Guide: {output_dir}/SETUP.md")
            print(f"   🏗️ Architecture: {output_dir}/ARCHITECTURE.md")

if __name__ == "__main__":
    asyncio.run(main())
