"""Fast GitHub documentation analyzer - optimized for speed and API documentation."""

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
REQUIRED_PACKAGES = ['requests', 'aiohttp', 'pydantic', 'gitpython']

def install_packages():
    """Install packages in background."""
    print(' Installing packages in background...')
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
class FastAPIEndpoint:
    method: str
    path: str
    function_name: str = ""
    line: int = 0
    file_path: str = ""
    code_snippet: str = ""

@dataclass
class FastFunction:
    name: str
    params: List[str]
    file_path: str
    line: int
    language: str
    code_snippet: str = ""
    is_api_handler: bool = False

@dataclass
class FastFileAnalysis:
    file_path: str
    language: str
    functions: List[FastFunction]
    api_endpoints: List[FastAPIEndpoint]
    lines_of_code: int
    is_backend: bool = False

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
                    print(f"📊 Progress: {self.processed_files}/{self.total_files} ({progress:.1f}%) - ETA: {eta:.0f}s")

class FastCodeExtractor:
    """Fast code extraction focusing only on functions and APIs."""
    
    def __init__(self):
        self.progress = ProgressTracker()
    
    def extract_functions_and_apis(self, file_path: str, content: str, language: str) -> FastFileAnalysis:
        """Extract only functions and API endpoints - optimized for speed."""
        
        functions = []
        api_endpoints = []
        lines = content.split('\n')
        
        if language in ['javascript', 'typescript']:
            functions, api_endpoints = self._extract_js_functions_apis(lines, file_path, language)
        elif language == 'python':
            functions, api_endpoints = self._extract_python_functions_apis(lines, file_path, language)
        
        # Determine if this is a backend file
        is_backend = (
            len(api_endpoints) > 0 or
            any(keyword in content.lower() for keyword in ['express', 'fastapi', 'flask', 'router', 'app.']) or
            any(keyword in file_path.lower() for keyword in ['api', 'server', 'route', 'controller'])
        )
        
        return FastFileAnalysis(
            file_path=file_path,
            language=language,
            functions=functions,
            api_endpoints=api_endpoints,
            lines_of_code=len([line for line in lines if line.strip()]),
            is_backend=is_backend
        )
    
    def _extract_js_functions_apis(self, lines: List[str], file_path: str, language: str):
        """Extract JavaScript/TypeScript functions and API routes."""
        functions = []
        api_endpoints = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # API endpoints (Express.js style)
            api_match = re.search(r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line_stripped, re.IGNORECASE)
            if api_match:
                method = api_match.group(2).upper()
                path = api_match.group(3)
                
                # Get code snippet (current line + next 5 lines)
                snippet_lines = lines[i:i+6]
                code_snippet = '\n'.join(snippet_lines)
                
                api_endpoints.append(FastAPIEndpoint(
                    method=method,
                    path=path,
                    line=i+1,
                    file_path=file_path,
                    code_snippet=code_snippet
                ))
            
            # Next.js API routes (export default function or export function)
            nextjs_api_match = re.search(r'export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)?\s*\([^)]*(?:req|request)[^)]*(?:res|response)[^)]*\)', line_stripped, re.IGNORECASE)
            if nextjs_api_match and ('api' in file_path.lower() or 'pages' in file_path.lower()):
                # Determine method from function name or default to multiple methods
                func_name = nextjs_api_match.group(1) or "handler"
                
                # Get code snippet
                snippet_lines = lines[i:i+8]
                code_snippet = '\n'.join(snippet_lines)
                
                # Next.js API routes typically handle multiple methods
                for method in ['GET', 'POST', 'PUT', 'DELETE']:
                    api_endpoints.append(FastAPIEndpoint(
                        method=method,
                        path=f"/api/{Path(file_path).stem}",  # Infer path from file
                        function_name=func_name,
                        line=i+1,
                        file_path=file_path,
                        code_snippet=code_snippet
                    ))
                break  # Only add once per file
            
            # Function definitions
            func_match = re.search(r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))', line_stripped)
            if func_match:
                func_name = func_match.group(1) or func_match.group(2)
                
                # Extract parameters
                param_match = re.search(r'\(([^)]*)\)', line_stripped)
                params = []
                if param_match:
                    param_str = param_match.group(1).strip()
                    if param_str:
                        params = [p.strip().split('=')[0].strip() for p in param_str.split(',')]
                
                # Get code snippet (current line + next 6 lines)
                snippet_lines = lines[i:i+7]
                code_snippet = '\n'.join(snippet_lines)
                
                functions.append(FastFunction(
                    name=func_name,
                    params=params,
                    file_path=file_path,
                    line=i+1,
                    language=language,
                    code_snippet=code_snippet,
                    is_api_handler='req' in line_stripped and 'res' in line_stripped
                ))
        
        return functions, api_endpoints
    
    def _extract_python_functions_apis(self, lines: List[str], file_path: str, language: str):
        """Extract Python functions and API routes."""
        functions = []
        api_endpoints = []
        
        i = 0
        while i < len(lines):
            line_stripped = lines[i].strip()
            
            # Flask route detection - @app.route()
            flask_route_match = re.search(r'@app\.route\s*\(\s*["\']([^"\']+)["\'](?:[^)]*methods\s*=\s*\[([^\]]+)\])?', line_stripped, re.IGNORECASE)
            if flask_route_match:
                path = flask_route_match.group(1)
                methods_str = flask_route_match.group(2)
                
                # Parse methods
                methods = ['GET']  # Default
                if methods_str:
                    methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
                
                # Find the function definition on next lines
                func_name = ""
                for j in range(i+1, min(i+5, len(lines))):
                    func_match = re.search(r'def\s+(\w+)\s*\(', lines[j].strip())
                    if func_match:
                        func_name = func_match.group(1)
                        break
                
                # Get code snippet
                snippet_lines = lines[i:i+8]
                code_snippet = '\n'.join(snippet_lines)
                
                # Create endpoint for each method
                for method in methods:
                    api_endpoints.append(FastAPIEndpoint(
                        method=method.upper(),
                        path=path,
                        function_name=func_name,
                        line=i+1,
                        file_path=file_path,
                        code_snippet=code_snippet
                    ))
            
            # FastAPI/Flask API endpoints - @app.get, @app.post, etc.
            api_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line_stripped, re.IGNORECASE)
            if api_match:
                method = api_match.group(1).upper()
                path = api_match.group(2)
                
                # Find the function definition on next lines
                func_name = ""
                for j in range(i+1, min(i+5, len(lines))):
                    func_match = re.search(r'def\s+(\w+)\s*\(', lines[j].strip())
                    if func_match:
                        func_name = func_match.group(1)
                        break
                
                # Get code snippet
                snippet_lines = lines[i:i+8]
                code_snippet = '\n'.join(snippet_lines)
                
                api_endpoints.append(FastAPIEndpoint(
                    method=method,
                    path=path,
                    function_name=func_name,
                    line=i+1,
                    file_path=file_path,
                    code_snippet=code_snippet
                ))
            
            # Function definitions
            func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', line_stripped)
            if func_match:
                func_name = func_match.group(1)
                param_str = func_match.group(2).strip()
                
                # Extract parameters
                params = []
                if param_str:
                    params = [p.strip().split(':')[0].strip() for p in param_str.split(',') if p.strip()]
                
                # Get code snippet
                snippet_lines = lines[i:i+8]
                code_snippet = '\n'.join(snippet_lines)
                
                functions.append(FastFunction(
                    name=func_name,
                    params=params,
                    file_path=file_path,
                    line=i+1,
                    language=language,
                    code_snippet=code_snippet,
                    is_api_handler=any(keyword in line_stripped.lower() for keyword in ['request', 'response', 'req', 'res'])
                ))
            
            i += 1
        
        return functions, api_endpoints

class FastLLMProcessor:
    """Fast LLM processing for API documentation."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
    
    async def process_backend_files(self, backend_files: List[FastFileAnalysis]) -> Dict[str, Any]:
        """Process only backend files with LLM for API documentation."""
        
        if not self.api_keys:
            return {"error": "No API keys provided"}
        
        print(f"🤖 Processing {len(backend_files)} backend files with LLM...")
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for file_analysis in backend_files:
                try:
                    # Create optimized prompt focusing on APIs and functions
                    prompt = self._create_api_documentation_prompt(file_analysis)
                    
                    # Call LLM
                    response = await self._call_llm(session, prompt)
                    
                    results[file_analysis.file_path] = {
                        "api_documentation": response,
                        "api_count": len(file_analysis.api_endpoints),
                        "function_count": len(file_analysis.functions),
                        "language": file_analysis.language
                    }
                    
                    print(f"Processed {file_analysis.file_path}")
                    
                except Exception as e:
                    print(f"Error processing {file_analysis.file_path}: {e}")
                    results[file_analysis.file_path] = {"error": str(e)}
        
        return results
    
    def _create_api_documentation_prompt(self, file_analysis: FastFileAnalysis) -> str:
        """Create focused prompt for API documentation."""
        
        prompt = f"""Create comprehensive API documentation for this {file_analysis.language} file:

FILE: {file_analysis.file_path}
LANGUAGE: {file_analysis.language}
API ENDPOINTS: {len(file_analysis.api_endpoints)}
FUNCTIONS: {len(file_analysis.functions)}

"""
        
        # Add API endpoints
        if file_analysis.api_endpoints:
            prompt += "API ENDPOINTS:\n"
            for api in file_analysis.api_endpoints:
                prompt += f"\n{api.method} {api.path} (line {api.line})\n"
                prompt += f"```{file_analysis.language}\n{api.code_snippet}\n```\n"
        
        # Add key functions
        if file_analysis.functions:
            prompt += "\nKEY FUNCTIONS:\n"
            for func in file_analysis.functions[:5]:  # Limit to 5 functions
                prompt += f"\n{func.name}({', '.join(func.params)}) (line {func.line})\n"
                prompt += f"```{file_analysis.language}\n{func.code_snippet}\n```\n"
        
        prompt += """
Provide COMPLETE API documentation in this format:

SUMMARY: [What this file does and its role in the API]

API_ENDPOINTS: [For each endpoint:
- Purpose and functionality
- Parameters (path, query, body)
- Request/Response examples
- Error codes]

FUNCTIONS: [For each key function:
- Purpose and usage
- Parameters and return values
- Integration with APIs]

SETUP_INSTRUCTIONS: [How to run this API:
- Prerequisites
- Environment variables
- Start commands
- Port/URL information]

USAGE_EXAMPLES: [Complete examples:
- cURL commands
- JavaScript fetch examples
- Response formats]

Focus on providing ACTIONABLE documentation for developers to use this API immediately.
"""
        
        return prompt
    
    async def _call_llm(self, session: aiohttp.ClientSession, prompt: str) -> str:
        """Call LLM API with the prompt."""
        
        api_key = self.api_keys[self.current_key_index % len(self.api_keys)]
        self.current_key_index += 1
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert API documentation generator. Create comprehensive, actionable documentation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
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
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    return f"API Error {response.status}: {error_text[:200]}"
        
        except Exception as e:
            return f"Request failed: {str(e)}"

class FastGitHubAnalyzer:
    """Fast GitHub repository analyzer."""
    
    def __init__(self):
        self.temp_dir = None
        self.progress = ProgressTracker()
    
    async def analyze_repository_fast(self, repo_url: str, api_keys: List[str] = None) -> Dict[str, Any]:
        """Fast analysis focusing on API documentation."""
        
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
            
            # Step 3: Extract functions and APIs
            self.progress.update_stage("Extracting functions and APIs...")
            extractor = FastCodeExtractor()
            
            analyzed_files = []
            backend_files = []
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for file_path, content, language in all_files:
                    future = executor.submit(
                        extractor.extract_functions_and_apis,
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
            
            # Step 4: LLM processing for backend files
            llm_results = {}
            if api_keys and backend_files:
                self.progress.update_stage("Generating API documentation with LLM...")
                llm_processor = FastLLMProcessor(api_keys)
                llm_results = await llm_processor.process_backend_files(backend_files)
            
            # Step 5: Compile results
            self.progress.update_stage("Compiling results...")
            
            total_apis = sum(len(f.api_endpoints) for f in analyzed_files)
            total_functions = sum(len(f.functions) for f in analyzed_files)
            
            results = {
                "repository_url": repo_url,
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
                        "api_count": len(f.api_endpoints),
                        "function_count": len(f.functions),
                        "apis": [
                            {
                                "method": api.method,
                                "path": api.path,
                                "function": api.function_name,
                                "line": api.line
                            } for api in f.api_endpoints
                        ],
                        "functions": [
                            {
                                "name": func.name,
                                "params": func.params,
                                "line": func.line,
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
                        "lines_of_code": f.lines_of_code,
                        "function_count": len(f.functions),
                        "is_backend": f.is_backend
                    } for f in analyzed_files
                ]
            }
            
            elapsed = time.time() - start_time
            print(f"Analysis complete in {elapsed:.1f}s!")
            print(f"Summary: {len(analyzed_files)} files, {len(backend_files)} backend, {total_apis} APIs, {total_functions} functions")
            
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
                        
                        # Skip very large files (>50KB)
                        if len(content) > 50000:
                            continue
                        
                        files.append((rel_path, content, EXTENSIONS[ext]))
                        
                    except Exception:
                        continue
        
        return files
    
    def _cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Could not clean up temp directory: {e}")

async def main():
    """Main entry point for fast analyzer."""
    
    # Wait for package installation to complete
    install_thread.join()
    print('Package installation complete!')
    
    print("Fast GitHub API Documentation Generator")
    print("=" * 50)
    
    # Get input
    repo_url = input("Enter GitHub repository URL: ").strip()
    if not repo_url:
        print("Repository URL is required")
        return
    
    api_keys_input = input("Enter Groq API keys (comma-separated, optional): ").strip()
    api_keys = []
    if api_keys_input:
        api_keys = [key.strip() for key in api_keys_input.split(',') if key.strip()]
        print(f"Using {len(api_keys)} API keys for documentation generation")
    else:
        print("No API keys - will extract APIs but skip LLM documentation")
    
    # Run analysis
    analyzer = FastGitHubAnalyzer()
    results = await analyzer.analyze_repository_fast(repo_url, api_keys)
    
    # Save results
    if "error" not in results:
        output_file = f"api_docs_{int(time.time())}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Could not save results: {e}")
        
        # Print summary
        summary = results["summary"]
        print(f"\nFinal Summary:")
        print(f"   Analysis time: {results['analysis_time']:.1f}s")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Backend files: {summary['backend_files']}")
        print(f"   API endpoints: {summary['total_apis']}")
        print(f"   Functions: {summary['total_functions']}")
        print(f"   Languages: {', '.join(summary['languages'])}")
        
        if api_keys:
            doc_count = len(results.get("api_documentation", {}))
            print(f"   API docs generated: {doc_count}")

if __name__ == "__main__":
    asyncio.run(main())