import os
import json
import ast
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

# Install packages
packages = [
    'gitpython', 'tree_sitter', 'tree_sitter_javascript', 'tree_sitter_typescript', 
    'tree_sitter_python', 'requests', 'groq', 'aiohttp', 'asyncio', 'pydantic',
    'tiktoken', 'tenacity', 'networkx'
]
print('📦 Installing packages...')
for pkg in packages:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], capture_output=True)

from git import Repo
from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_python
import requests
import asyncio
import aiohttp
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential
import networkx as nx

print('✅ Setup complete!')

# Configuration
SKIP_DIRECTORIES = {'node_modules', '.git', '__pycache__', 'dist', 'build', '.next', 'coverage', '.pytest_cache', 'venv', 'env', '.venv', 'out'}
LANGUAGE_EXTENSIONS = {'.js': 'javascript', '.mjs': 'javascript', '.jsx': 'jsx', '.ts': 'typescript', '.tsx': 'tsx', '.py': 'python'}

# LLM Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MAX_TOKENS_PER_REQUEST = 4000
MAX_CONCURRENT_REQUESTS = 5
RATE_LIMIT_DELAY = 0.2  # seconds between requests

# Structured Data Models
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

# Enhanced data models for detailed analysis
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

class DetailedFileAnalysis(BaseModel):
    file: str
    language: str
    service_info: Optional[ServiceInfo] = None
    functions: List[FunctionInfo] = []
    classes: List[ClassInfo] = []
    imports: List[ImportInfo] = []
    api_endpoints: List[APIEndpointDetail] = []
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
    api_endpoints: List[APIEndpointDetail] = []
    shared_dependencies: List[str] = []
    folder_purpose: Optional[str] = None
    key_components: List[str] = []
    integration_patterns: List[str] = []
    llm_summary: Optional[str] = None
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

def should_skip_directory(dirname):
    return dirname in SKIP_DIRECTORIES or dirname.startswith('.')

def get_file_language(filename):
    for ext, lang in LANGUAGE_EXTENSIONS.items():
        if filename.endswith(ext):
            return lang
    return None

def dict_to_object(d):
    """Convert dictionary to object with attribute access"""
    if isinstance(d, dict):
        obj = type('DictObject', (), {})()
        for key, value in d.items():
            if isinstance(value, dict):
                setattr(obj, key, dict_to_object(value))
            elif isinstance(value, list):
                setattr(obj, key, [dict_to_object(item) if isinstance(item, dict) else item for item in value])
            else:
                setattr(obj, key, value)
        return obj
    return d
    """Convert FileAnalysis and related objects to dictionaries for JSON serialization"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if isinstance(value, list):
                result[key] = [convert_to_dict(item) for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = convert_to_dict(value)
            else:
                result[key] = value
        return result
    else:
        return obj
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimation
        return len(text.split()) * 1.3

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimation
        return len(text.split()) * 1.3

def convert_to_dict(obj):
    """Convert FileAnalysis and related objects to dictionaries for JSON serialization"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            if isinstance(value, list):
                result[key] = [convert_to_dict(item) for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = convert_to_dict(value)
            else:
                result[key] = value
        return result
    else:
        return obj

def truncate_content(content: str, max_tokens: int = 3000) -> str:
    """Truncate content to fit within token limits"""
    tokens = count_tokens(content)
    if tokens <= max_tokens:
        return content
    
    # Rough truncation - keep first 70% and last 30%
    lines = content.split('\n')
    total_lines = len(lines)
    keep_start = int(total_lines * 0.7)
    keep_end = int(total_lines * 0.3)
    
    truncated = '\n'.join(lines[:keep_start] + ['... [TRUNCATED] ...'] + lines[-keep_end:])
    return truncated

class TokenAwareRateLimiter:
    """Advanced rate limiter that tracks tokens per minute for Groq API"""
    def __init__(self, max_tokens_per_minute: int = 5000, max_calls_per_second: float = 2.0):
        self.max_tokens_per_minute = max_tokens_per_minute
        self.max_calls_per_second = max_calls_per_second
        self.min_call_interval = 1.0 / max_calls_per_second
        
        # Token tracking
        self.token_usage = []  # List of (timestamp, tokens_used)
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def estimate_tokens(self, content: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters)"""
        return len(content) // 4 + 100  # Add buffer for prompt overhead
    
    def can_make_request(self, estimated_tokens: int) -> tuple[bool, float]:
        """Check if request can be made, return (can_make, wait_time)"""
        with self.lock:
            current_time = time.time()
            
            # Clean old token usage (older than 1 minute)
            minute_ago = current_time - 60
            self.token_usage = [(ts, tokens) for ts, tokens in self.token_usage if ts > minute_ago]
            
            # Calculate current token usage in the last minute
            current_tokens = sum(tokens for _, tokens in self.token_usage)
            
            # Check if adding this request would exceed token limit
            if current_tokens + estimated_tokens > self.max_tokens_per_minute:
                # Calculate wait time until oldest token usage expires
                if self.token_usage:
                    oldest_time = min(ts for ts, _ in self.token_usage)
                    wait_time = 61 - (current_time - oldest_time)  # Wait until it's been 61 seconds
                    return False, max(wait_time, 1)
                else:
                    return False, 60  # Wait a full minute if no usage history
            
            # Check call rate limit
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.min_call_interval:
                call_wait_time = self.min_call_interval - time_since_last_call
                return False, call_wait_time
            
            return True, 0
    
    def record_request(self, tokens_used: int):
        """Record a successful request"""
        with self.lock:
            current_time = time.time()
            self.token_usage.append((current_time, tokens_used))
            self.last_call_time = current_time
    
    async def wait_if_needed_async(self, estimated_tokens: int):
        """Async version of rate limiting"""
        can_make, wait_time = self.can_make_request(estimated_tokens)
        if not can_make:
            print(f"⏳ Rate limit: waiting {wait_time:.1f}s (estimated {estimated_tokens} tokens)")
            await asyncio.sleep(wait_time)
            # Check again after waiting
            can_make, additional_wait = self.can_make_request(estimated_tokens)
            if not can_make and additional_wait > 0:
                await asyncio.sleep(additional_wait)

class GroqLLMClient:
    """Groq LLM client with advanced rate limiting and error handling"""
    
    def __init__(self, api_key: str, rate_limiter: TokenAwareRateLimiter):
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def generate_summary(self, session: aiohttp.ClientSession, request: LLMSummaryRequest) -> LLMSummaryResponse:
        """Generate file summary using Groq API with advanced rate limiting"""
        max_retries = 3
        
        # Prepare content for LLM (inline truncation to avoid import issues)
        content = request.content
        if len(content) > 8000:  # Simple truncation
            lines = content.split('\n')
            total_lines = len(lines)
            keep_start = int(total_lines * 0.7)
            keep_end = int(total_lines * 0.3)
            content = '\n'.join(lines[:keep_start] + ['... [TRUNCATED] ...'] + lines[-keep_end:])
        
        prompt = self._build_analysis_prompt(request.file_path, content, request.analysis)
        
        # Estimate tokens for this request
        estimated_tokens = self.rate_limiter.estimate_tokens(prompt)
        
        for attempt in range(max_retries):
            try:
                # Advanced rate limiting with token awareness
                await self.rate_limiter.wait_if_needed_async(estimated_tokens)
                
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert code analyst. Provide concise, structured analysis of code files."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": 800,  # Reduced to stay within limits
                    "temperature": 0.1
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        content_response = result['choices'][0]['message']['content']
                        
                        # Record successful request
                        actual_tokens = result.get('usage', {}).get('total_tokens', estimated_tokens)
                        self.rate_limiter.record_request(actual_tokens)
                        
                        return self._parse_llm_response(request.file_path, content_response)
                        
                    elif response.status == 429:
                        # Rate limit hit - extract wait time from error message
                        error_text = await response.text()
                        wait_time = self._extract_wait_time_from_error(error_text)
                        
                        if attempt < max_retries - 1:
                            print(f"⏳ Rate limit hit for {request.file_path}, waiting {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Rate limit exceeded for {request.file_path} after {max_retries} attempts")
                            return self._create_fallback_response(request.file_path)
                    else:
                        error_text = await response.text()
                        print(f"❌ LLM API Error for {request.file_path}: {response.status} - {error_text}")
                        if attempt == max_retries - 1:
                            return self._create_fallback_response(request.file_path)
                        
            except Exception as e:
                print(f"❌ LLM Request failed for {request.file_path} (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return self._create_fallback_response(request.file_path)
                
                # Exponential backoff for errors
                await asyncio.sleep(2 ** attempt)
        
        # Fallback if all retries failed
        return self._create_fallback_response(request.file_path)
    
    def _extract_wait_time_from_error(self, error_text: str) -> float:
        """Extract wait time from Groq rate limit error message"""
        import re
        # Look for patterns like "Please try again in 2.52s"
        match = re.search(r'try again in ([\d.]+)s', error_text)
        if match:
            return float(match.group(1)) + 1  # Add 1 second buffer
        
        # Look for patterns like "Please try again in 420ms"
        match = re.search(r'try again in ([\d.]+)ms', error_text)
        if match:
            return float(match.group(1)) / 1000 + 0.5  # Convert to seconds + buffer
        
        # Default wait time if no pattern found
        return 5.0
    
    def _build_analysis_prompt(self, file_path: str, content: str, analysis: FileAnalysis) -> str:
        """Build enhanced structured prompt for detailed file analysis"""
        
        # Determine file type for specialized prompts
        file_type = self._determine_file_type(file_path, analysis)
        
        base_info = f"""FILE: {file_path}
LANGUAGE: {analysis.language}
FUNCTIONS: {len(analysis.functions)}
CLASSES: {len(analysis.classes)}
IMPORTS: {len(analysis.imports)}
COMPLEXITY: {analysis.complexity_score}
LINES: {analysis.lines_of_code}"""

        if file_type == "api_routes":
            return self._build_api_routes_prompt(base_info, content, analysis)
        elif file_type == "frontend_component":
            return self._build_frontend_component_prompt(base_info, content, analysis)
        elif file_type == "backend_service":
            return self._build_backend_service_prompt(base_info, content, analysis)
        elif file_type == "configuration":
            return self._build_configuration_prompt(base_info, content, analysis)
        else:
            return self._build_general_prompt(base_info, content, analysis)
    
    def _determine_file_type(self, file_path: str, analysis: FileAnalysis) -> str:
        """Determine the type of file for specialized analysis"""
        path_lower = file_path.lower()
        
        if analysis.api_endpoints or any(route in path_lower for route in ['route', 'api', 'controller']):
            return "api_routes"
        elif analysis.jsx_components or any(comp in path_lower for comp in ['component', 'jsx', 'tsx']):
            return "frontend_component"
        elif any(service in path_lower for service in ['service', 'server', 'app.js', 'main.py']):
            return "backend_service"
        elif any(config in path_lower for config in ['config', 'env', 'docker', 'package.json']):
            return "configuration"
        else:
            return "general"
    
    def _build_api_routes_prompt(self, base_info: str, content: str, analysis: FileAnalysis) -> str:
        """Specialized prompt for API route files"""
        api_info = ""
        if analysis.api_endpoints:
            api_info = f"\nAPI ENDPOINTS DETECTED: {len(analysis.api_endpoints)}"
            for api in analysis.api_endpoints[:3]:
                api_info += f"\n- {api.method} {api.path}"
        
        return f"""Analyze this API routes file and provide detailed documentation:

{base_info}{api_info}

CODE:
```{analysis.language}
{content}
```

Provide analysis in this JSON-like format:
SUMMARY: [Detailed description of what this API file does and its role in the system]
API_ENDPOINTS: [For each endpoint, describe: purpose, parameters, expected response, authentication requirements]
AUTHENTICATION: [What authentication/authorization is used]
MIDDLEWARE: [What middleware is applied]
ERROR_HANDLING: [How errors are handled and what error codes are returned]
DEPENDENCIES: [What external services or databases this connects to]
USAGE_EXAMPLES: [How to call these APIs with example requests]
INTEGRATION_POINTS: [How this integrates with frontend/other services]
SECURITY_CONSIDERATIONS: [Security measures and potential vulnerabilities]
IMPROVEMENTS: [Specific suggestions for better API design, error handling, or performance]

Focus on:
- Exact API endpoint documentation with parameters and responses
- Authentication and authorization mechanisms
- Error handling patterns and status codes
- Integration with databases or external services
- Security best practices and potential issues"""

    def _build_frontend_component_prompt(self, base_info: str, content: str, analysis: FileAnalysis) -> str:
        """Specialized prompt for frontend component files"""
        component_info = ""
        if analysis.jsx_components:
            component_info = f"\nCOMPONENTS: {', '.join(analysis.jsx_components[:5])}"
        
        return f"""Analyze this frontend component file and provide detailed documentation:

{base_info}{component_info}

CODE:
```{analysis.language}
{content}
```

Provide analysis in this JSON-like format:
SUMMARY: [What this component does and its role in the UI]
COMPONENTS: [List each component with its purpose and props]
STATE_MANAGEMENT: [How state is managed - useState, Redux, Context, etc.]
PROPS_INTERFACE: [What props each component expects and their types]
EVENT_HANDLERS: [What user interactions are handled]
API_CALLS: [What backend APIs this component calls]
STYLING: [How styling is implemented - CSS modules, styled-components, etc.]
ROUTING: [If this handles routing, describe the routes]
PERFORMANCE: [Any performance optimizations like memoization, lazy loading]
ACCESSIBILITY: [Accessibility features and ARIA attributes]
TESTING: [How this component should be tested]
IMPROVEMENTS: [Suggestions for better UX, performance, or maintainability]

Focus on:
- Component hierarchy and data flow
- Props and state management patterns
- API integration and data fetching
- User interaction handling
- Performance and accessibility considerations"""

    def _build_backend_service_prompt(self, base_info: str, content: str, analysis: FileAnalysis) -> str:
        """Specialized prompt for backend service files"""
        db_info = ""
        if analysis.database_queries:
            db_info = f"\nDATABASE QUERIES: {len(analysis.database_queries)}"
        
        return f"""Analyze this backend service file and provide detailed documentation:

{base_info}{db_info}

CODE:
```{analysis.language}
{content}
```

Provide analysis in this JSON-like format:
SUMMARY: [What this service does and its role in the backend architecture]
BUSINESS_LOGIC: [Core business logic and algorithms implemented]
DATABASE_OPERATIONS: [What database operations are performed]
EXTERNAL_INTEGRATIONS: [Third-party APIs or services integrated]
ERROR_HANDLING: [How errors are caught and handled]
VALIDATION: [Input validation and data sanitization]
CACHING: [Any caching mechanisms used]
LOGGING: [Logging and monitoring implementation]
PERFORMANCE: [Performance considerations and optimizations]
SCALABILITY: [How this service scales and potential bottlenecks]
SECURITY: [Security measures and data protection]
IMPROVEMENTS: [Suggestions for better architecture, performance, or reliability]

Focus on:
- Core business logic and data processing
- Database interaction patterns
- External service integrations
- Error handling and resilience
- Performance and scalability considerations"""

    def _build_configuration_prompt(self, base_info: str, content: str, analysis: FileAnalysis) -> str:
        """Specialized prompt for configuration files"""
        return f"""Analyze this configuration file and provide detailed documentation:

{base_info}

CODE:
```{analysis.language}
{content}
```

Provide analysis in this JSON-like format:
SUMMARY: [What this configuration file controls and its purpose]
ENVIRONMENT_VARIABLES: [List all environment variables and their purposes]
SERVICE_CONFIGURATION: [How services are configured]
DATABASE_CONFIG: [Database connection and settings]
API_CONFIGURATION: [API endpoints, ports, and external service configs]
SECURITY_SETTINGS: [Security-related configurations]
DEPLOYMENT_INFO: [Deployment and infrastructure settings]
DEPENDENCIES: [Required dependencies and versions]
SETUP_INSTRUCTIONS: [How to set up and use this configuration]
ENVIRONMENT_SETUP: [Different environments (dev, staging, prod) and their differences]
TROUBLESHOOTING: [Common configuration issues and solutions]
IMPROVEMENTS: [Suggestions for better configuration management]

Focus on:
- Required environment variables and their purposes
- Service dependencies and connection details
- Security configurations and best practices
- Setup and deployment instructions
- Environment-specific configurations"""

    def _build_general_prompt(self, base_info: str, content: str, analysis: FileAnalysis) -> str:
        """General prompt for other file types"""
        return f"""Analyze this code file and provide detailed documentation:

{base_info}

CODE:
```{analysis.language}
{content}
```

Provide analysis in this JSON-like format:
SUMMARY: [Detailed description of file purpose and functionality]
KEY_FUNCTIONS: [List main functions with their purposes and parameters]
CLASSES_AND_METHODS: [Classes and their key methods]
ALGORITHMS: [Any important algorithms or business logic]
DATA_STRUCTURES: [Key data structures and their purposes]
DEPENDENCIES: [External libraries and their usage]
PATTERNS: [Design patterns and architectural decisions]
INTEGRATION: [How this integrates with other parts of the system]
TESTING: [Testing approach and test coverage]
PERFORMANCE: [Performance characteristics and optimizations]
MAINTAINABILITY: [Code quality and maintainability aspects]
IMPROVEMENTS: [Specific suggestions for enhancement]

Focus on:
- Core functionality and business logic
- Code organization and design patterns
- Integration points with other components
- Performance and maintainability considerations"""

    def _parse_llm_response(self, file_path: str, content: str) -> LLMSummaryResponse:
        """Parse structured LLM response"""
        lines = content.split('\n')
        
        summary = ""
        key_insights = []
        architectural_role = ""
        complexity_assessment = ""
        improvement_suggestions = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('KEY_INSIGHTS:'):
                current_section = 'insights'
            elif line.startswith('ARCHITECTURAL_ROLE:'):
                current_section = 'role'
                architectural_role = line.replace('ARCHITECTURAL_ROLE:', '').strip()
            elif line.startswith('COMPLEXITY:'):
                current_section = 'complexity'
                complexity_assessment = line.replace('COMPLEXITY:', '').strip()
            elif line.startswith('IMPROVEMENTS:'):
                current_section = 'improvements'
            elif line.startswith('- ') or line.startswith('• '):
                bullet_point = line[2:].strip()
                if current_section == 'insights':
                    key_insights.append(bullet_point)
                elif current_section == 'improvements':
                    improvement_suggestions.append(bullet_point)
            elif current_section == 'summary' and line:
                summary += " " + line
        
        return LLMSummaryResponse(
            file_path=file_path,
            summary=summary or "Code file analysis",
            key_insights=key_insights,
            architectural_role=architectural_role,
            complexity_assessment=complexity_assessment,
            improvement_suggestions=improvement_suggestions
        )
    
    def _create_fallback_response(self, file_path: str) -> LLMSummaryResponse:
        """Create fallback response when LLM fails"""
        from pathlib import Path  # Ensure Path is available
        return LLMSummaryResponse(
            file_path=file_path,
            summary=f"Code file: {Path(file_path).name}",
            key_insights=["Analysis unavailable"],
            architectural_role="Unknown",
            complexity_assessment="Unable to assess",
            improvement_suggestions=[]
        )

class GitHubRepoCloner:
    def __init__(self):
        self.temp_dir = None
        self.repo_info = {}

    def clone_repo(self, github_url):
        print(f'🔄 Cloning {github_url}...')
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')
        owner, repo_name = path_parts[0], path_parts[1]

        self.repo_info = {'owner': owner, 'name': repo_name, 'url': github_url}
        self.temp_dir = tempfile.mkdtemp(prefix=f'{repo_name}_')

        clone_url = f'https://github.com/{owner}/{repo_name}.git'
        Repo.clone_from(clone_url, self.temp_dir)
        print(f'✅ Repository cloned')

        # Get repo metadata
        try:
            api_url = f'https://api.github.com/repos/{owner}/{repo_name}'
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.repo_info.update({
                    'description': data.get('description', ''),
                    'language': data.get('language', ''),
                    'stars': data.get('stargazers_count', 0),
                    'license': data.get('license', {}).get('name', '') if data.get('license') else ''
                })
        except:
            pass

        return self.temp_dir

    def cleanup(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                # On Windows, make files writable before deletion
                if os.name == 'nt':
                    for root, dirs, files in os.walk(self.temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, 0o777)
                            except:
                                pass
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up temp directory: {e}")

class DetailedCodeAnalyzer:
    """Enhanced analyzer for detailed code analysis"""
    
    def __init__(self):
        # We'll implement the parsing logic directly in this class
        pass
    
    def analyze_file_detailed(self, file_path: str, rel_path: str, content: str) -> DetailedFileAnalysis:
        """Perform detailed analysis of a single file"""
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
        """Parse JavaScript content and extract basic information"""
        import re
        
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
        """Parse Python content and extract basic information"""
        try:
            import ast
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
            # Fallback to regex parsing if AST fails
            pass
    
    def _detect_service_type(self, content: str, file_path: str) -> Optional[ServiceInfo]:
        """Detect what type of service this file represents"""
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
        
        # Database detection
        elif any(db in content.lower() for db in ['mongoose', 'sequelize', 'prisma', 'sqlalchemy']):
            service_info.type = "database"
            if 'mongoose' in content.lower():
                service_info.framework = "MongoDB/Mongoose"
            elif 'sequelize' in content.lower():
                service_info.framework = "Sequelize ORM"
            elif 'prisma' in content.lower():
                service_info.framework = "Prisma ORM"
        
        # Configuration detection
        elif any(config in file_path.lower() for config in ['config', 'env', 'docker', 'package.json']):
            service_info.type = "configuration"
        
        # Extract port information
        import re
        port_match = re.search(r'port[:\s=]+(\d+)', content.lower())
        if port_match:
            service_info.port = int(port_match.group(1))
        
        return service_info if service_info.type != "unknown" else None
    
    def _extract_detailed_api_endpoints(self, content: str, language: str) -> List[APIEndpointDetail]:
        """Extract detailed API endpoint information"""
        endpoints = []
        
        if language in ['javascript', 'typescript']:
            endpoints.extend(self._extract_js_api_endpoints(content))
        elif language == 'python':
            endpoints.extend(self._extract_python_api_endpoints(content))
        
        return endpoints
    
    def _extract_js_api_endpoints(self, content: str) -> List[APIEndpointDetail]:
        """Extract JavaScript/Node.js API endpoints"""
        endpoints = []
        import re
        
        # Express.js route patterns
        express_patterns = [
            r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in express_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                # Try to find the handler function
                handler_match = re.search(
                    rf'{re.escape(match.group(0))}[^{{]*{{([^}}]*function\s+(\w+)|(\w+)\s*\()',
                    content[match.start():match.start()+200]
                )
                
                function_name = None
                if handler_match:
                    function_name = handler_match.group(2) or handler_match.group(3)
                
                # Extract parameters from path
                path_params = re.findall(r':(\w+)', path)
                parameters = [{"name": param, "type": "path", "required": True} for param in path_params]
                
                endpoints.append(APIEndpointDetail(
                    method=method,
                    path=path,
                    line=line_num,
                    function_name=function_name,
                    parameters=parameters,
                    description=f"{method} endpoint for {path}"
                ))
        
        return endpoints
    
    def _extract_python_api_endpoints(self, content: str) -> List[APIEndpointDetail]:
        """Extract Python API endpoints (FastAPI, Flask, Django)"""
        endpoints = []
        import re
        
        # FastAPI patterns
        fastapi_patterns = [
            r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        ]
        
        # Flask patterns
        flask_patterns = [
            r'@app\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[["\']([^"\']+)["\']',
            r'@bp\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[["\']([^"\']+)["\']'
        ]
        
        # Process FastAPI patterns
        for pattern in fastapi_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                line_num = content[:match.start()].count('\n') + 1
                
                # Find function definition after decorator
                func_match = re.search(
                    r'def\s+(\w+)\s*\([^)]*\):',
                    content[match.end():match.end()+200]
                )
                
                function_name = func_match.group(1) if func_match else None
                
                endpoints.append(APIEndpointDetail(
                    method=method,
                    path=path,
                    line=line_num,
                    function_name=function_name,
                    description=f"FastAPI {method} endpoint for {path}"
                ))
        
        # Process Flask patterns
        for pattern in flask_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                path = match.group(1)
                method = match.group(2).upper()
                line_num = content[:match.start()].count('\n') + 1
                
                endpoints.append(APIEndpointDetail(
                    method=method,
                    path=path,
                    line=line_num,
                    description=f"Flask {method} endpoint for {path}"
                ))
        
        return endpoints
    
    def _extract_environment_variables(self, content: str) -> List[EnvironmentVariable]:
        """Extract environment variable usage"""
        env_vars = []
        import re
        
        # Common environment variable patterns
        patterns = [
            r'process\.env\.(\w+)',  # Node.js
            r'os\.environ\.get\s*\(\s*["\'](\w+)["\']',  # Python os.environ.get
            r'os\.getenv\s*\(\s*["\'](\w+)["\']',  # Python os.getenv
            r'env\s*\(\s*["\'](\w+)["\']',  # Generic env function
            r'ENV\[[\'""](\w+)[\'""]\]',  # Environment array access
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check if there's a default value
                default_match = re.search(
                    rf'{re.escape(match.group(0))}[^,)]*[,|]\s*["\']([^"\']+)["\']',
                    content[match.start():match.start()+100]
                )
                
                default_value = default_match.group(1) if default_match else None
                
                env_vars.append(EnvironmentVariable(
                    name=var_name,
                    line=line_num,
                    default_value=default_value,
                    description=f"Environment variable used at line {line_num}"
                ))
        
        return env_vars
    
    def _detect_integration_points(self, content: str, language: str) -> List[str]:
        """Detect integration points with other services"""
        integrations = []
        
        # Database integrations
        if any(db in content.lower() for db in ['mongodb', 'mysql', 'postgres', 'redis']):
            integrations.append("Database")
        
        # External API integrations
        if any(api in content.lower() for api in ['fetch(', 'axios', 'requests.', 'http.']):
            integrations.append("External APIs")
        
        # Authentication
        if any(auth in content.lower() for auth in ['jwt', 'oauth', 'passport', 'auth']):
            integrations.append("Authentication")
        
        # File storage
        if any(storage in content.lower() for storage in ['aws', 's3', 'cloudinary', 'multer']):
            integrations.append("File Storage")
        
        # Message queues
        if any(queue in content.lower() for queue in ['rabbitmq', 'kafka', 'redis', 'bull']):
            integrations.append("Message Queue")
        
        return integrations
    
    def _determine_file_purpose(self, file_path: str, content: str, analysis: DetailedFileAnalysis) -> str:
        """Determine the main purpose of the file"""
        path_lower = file_path.lower()
        
        # Configuration files
        if any(config in path_lower for config in ['config', 'env', '.env', 'docker']):
            return "Configuration"
        
        # Route/Controller files
        if any(route in path_lower for route in ['route', 'controller', 'api']):
            return "API Routes/Controllers"
        
        # Model files
        if any(model in path_lower for model in ['model', 'schema', 'entity']):
            return "Data Models"
        
        # Component files
        if any(comp in path_lower for comp in ['component', 'jsx', 'tsx']) or analysis.jsx_components:
            return "UI Components"
        
        # Utility files
        if any(util in path_lower for util in ['util', 'helper', 'lib']):
            return "Utilities/Helpers"
        
        # Test files
        if any(test in path_lower for test in ['test', 'spec']):
            return "Tests"
        
        # Main entry points
        if any(entry in path_lower for entry in ['main', 'index', 'app', 'server']):
            return "Application Entry Point"
        
        # Based on content analysis
        if analysis.api_endpoints:
            return "API Endpoints"
        elif analysis.functions and len(analysis.functions) > 3:
            return "Business Logic"
        elif analysis.classes:
            return "Class Definitions"
        
        return "General Purpose"
    def __init__(self):
        try:
            self.language = Language(tree_sitter_javascript.language())
            self.parser = Parser(self.language)
        except:
            self.parser = None

    def parse(self, file_path, rel_path, is_jsx=False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return None

        result = FileAnalysis(
            file=rel_path,
            language='jsx' if is_jsx else 'javascript',
            lines_of_code=len([line for line in content.split('\n') if line.strip()])
        )

        if self.parser:
            try:
                tree = self.parser.parse(bytes(content, 'utf8'))
                self._traverse_enhanced(tree.root_node, result, content)
            except:
                self._regex_parse_enhanced(content, result)
        else:
            self._regex_parse_enhanced(content, result)

        # Calculate complexity score
        result.complexity_score = self._calculate_complexity(result)
        result.doc = f"{result.language.title()} file with {len(result.functions)} functions, {len(result.classes)} classes"
        
        return result

    def _traverse_enhanced(self, node, result: FileAnalysis, content: str):
        """Enhanced AST traversal with better data extraction"""
        
        if node.type == 'import_statement':
            self._extract_import(node, result, content)
        elif node.type == 'export_statement':
            self._extract_export(node, result, content)
        elif node.type in ['function_declaration', 'arrow_function', 'function_expression']:
            self._extract_function(node, result, content)
        elif node.type == 'class_declaration':
            self._extract_class(node, result, content)
        elif node.type in ['jsx_element', 'jsx_self_closing_element']:
            self._extract_jsx_component(node, result, content)
        elif node.type == 'call_expression':
            self._extract_api_calls(node, result, content)
        elif node.type in ['try_statement', 'catch_clause']:
            self._extract_error_handling(node, result, content)

        for child in node.children:
            self._traverse_enhanced(child, result, content)

    def _extract_import(self, node, result: FileAnalysis, content: str):
        """Extract detailed import information"""
        source = ""
        imported_names = []
        is_default = False
        
        for child in node.children:
            if child.type == 'string':
                source = content[child.start_byte:child.end_byte].strip('"\'')
            elif child.type == 'import_clause':
                for import_child in child.children:
                    if import_child.type == 'identifier':
                        imported_names.append(content[import_child.start_byte:import_child.end_byte])
                        is_default = True
                    elif import_child.type == 'named_imports':
                        for named_child in import_child.children:
                            if named_child.type == 'import_specifier':
                                for spec_child in named_child.children:
                                    if spec_child.type == 'identifier':
                                        imported_names.append(content[spec_child.start_byte:spec_child.end_byte])
        
        if source:
            result.imports.append(ImportInfo(
                source=source,
                line=node.start_point[0] + 1,
                imported_names=imported_names,
                is_default=is_default
            ))
            
            # Track dependencies
            if not source.startswith('.') and not source.startswith('/'):
                dep_name = source.split('/')[0]
                if dep_name not in result.dependencies:
                    result.dependencies.append(dep_name)

    def _extract_function(self, node, result: FileAnalysis, content: str):
        """Extract detailed function information"""
        func_name = ""
        params = []
        is_async = False
        is_exported = False
        docstring = None
        
        # Check if async
        parent = node.parent
        if parent and parent.type == 'export_statement':
            is_exported = True
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = content[child.start_byte:child.end_byte]
            elif child.type == 'formal_parameters':
                for param_child in child.children:
                    if param_child.type == 'identifier':
                        params.append(content[param_child.start_byte:param_child.end_byte])
            elif child.type == 'async':
                is_async = True
        
        if func_name:
            result.functions.append(FunctionInfo(
                name=func_name,
                params=params,
                line=node.start_point[0] + 1,
                is_async=is_async,
                is_exported=is_exported,
                docstring=docstring
            ))

    def _extract_class(self, node, result: FileAnalysis, content: str):
        """Extract detailed class information"""
        class_name = ""
        methods = []
        extends = None
        is_exported = False
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = content[child.start_byte:child.end_byte]
            elif child.type == 'class_heritage':
                for heritage_child in child.children:
                    if heritage_child.type == 'identifier':
                        extends = content[heritage_child.start_byte:heritage_child.end_byte]
            elif child.type == 'class_body':
                for body_child in child.children:
                    if body_child.type == 'method_definition':
                        for method_child in body_child.children:
                            if method_child.type == 'property_identifier':
                                methods.append(content[method_child.start_byte:method_child.end_byte])
        
        if class_name:
            result.classes.append(ClassInfo(
                name=class_name,
                methods=methods,
                line=node.start_point[0] + 1,
                extends=extends,
                is_exported=is_exported
            ))

    def _extract_jsx_component(self, node, result: FileAnalysis, content: str):
        """Extract JSX component usage"""
        for child in node.children:
            if child.type in ['jsx_opening_element', 'jsx_self_closing_element']:
                for elem_child in child.children:
                    if elem_child.type == 'identifier':
                        component_name = content[elem_child.start_byte:elem_child.end_byte]
                        if component_name not in result.jsx_components:
                            result.jsx_components.append(component_name)

    def _extract_api_calls(self, node, result: FileAnalysis, content: str):
        """Extract API endpoint calls (fetch, axios, etc.)"""
        call_text = content[node.start_byte:node.end_byte]
        
        # Look for common API patterns
        if any(pattern in call_text.lower() for pattern in ['fetch(', 'axios.', '.get(', '.post(', '.put(', '.delete(']):
            # Try to extract HTTP method and URL
            method = "GET"  # default
            if '.post(' in call_text.lower():
                method = "POST"
            elif '.put(' in call_text.lower():
                method = "PUT"
            elif '.delete(' in call_text.lower():
                method = "DELETE"
            
            # Simple URL extraction (this could be enhanced)
            import re
            url_match = re.search(r'["\']([^"\']*api[^"\']*)["\']', call_text)
            if url_match:
                result.api_endpoints.append(APIEndpoint(
                    method=method,
                    path=url_match.group(1),
                    line=node.start_point[0] + 1
                ))

    def _extract_error_handling(self, node, result: FileAnalysis, content: str):
        """Extract error handling patterns"""
        error_text = content[node.start_byte:node.end_byte]
        if node.type == 'try_statement':
            result.error_handling.append(f"try-catch block at line {node.start_point[0] + 1}")
        elif 'throw' in error_text.lower():
            result.error_handling.append(f"error throwing at line {node.start_point[0] + 1}")

    def _calculate_complexity(self, result: FileAnalysis) -> int:
        """Calculate basic complexity score"""
        complexity = 0
        complexity += len(result.functions) * 2
        complexity += len(result.classes) * 3
        complexity += len(result.imports)
        complexity += len(result.api_endpoints) * 2
        return complexity

    def _regex_parse_enhanced(self, content: str, result: FileAnalysis):
        """Enhanced fallback regex parsing"""
        import re
        
        # Import extraction
        import_matches = re.findall(r'import\s+(?:[\s\S]+?)\s+from\s+["\']([^"\']+)["\']', content)
        for imp in import_matches:
            result.imports.append(ImportInfo(source=imp, line=0))
            if not imp.startswith('.') and not imp.startswith('/'):
                dep_name = imp.split('/')[0]
                if dep_name not in result.dependencies:
                    result.dependencies.append(dep_name)

        # Function extraction
        func_matches = re.findall(r'(?:function|const|let)\s+(\w+)\s*[=\(]', content)
        for func in func_matches:
            result.functions.append(FunctionInfo(name=func, line=0))

        # Class extraction
        class_matches = re.findall(r'class\s+(\w+)', content)
        for cls in class_matches:
            result.classes.append(ClassInfo(name=cls, line=0))

        # API calls
        api_matches = re.findall(r'(fetch|axios\.\w+)\s*\(\s*["\']([^"\']+)["\']', content)
        for method, url in api_matches:
            http_method = "GET"
            if "post" in method.lower():
                http_method = "POST"
            result.api_endpoints.append(APIEndpoint(method=http_method, path=url, line=0))

        result.complexity_score = self._calculate_complexity(result)
class EnhancedPythonParser:
    def parse(self, file_path, rel_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return None

        result = FileAnalysis(
            file=rel_path,
            language='python',
            lines_of_code=len([line for line in content.split('\n') if line.strip()])
        )

        try:
            tree = ast.parse(content)
            self._analyze_ast(tree, result, content)
        except Exception as e:
            print(f"⚠️ Python AST parsing failed for {rel_path}: {e}")
            self._regex_parse_python(content, result)

        result.complexity_score = self._calculate_complexity(result)
        result.doc = f"Python file with {len(result.functions)} functions, {len(result.classes)} classes"
        
        return result

    def _analyze_ast(self, tree, result: FileAnalysis, content: str):
        """Enhanced AST analysis for Python"""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append(ImportInfo(
                        source=alias.name,
                        line=node.lineno,
                        imported_names=[alias.asname or alias.name]
                    ))
                    dep_name = alias.name.split('.')[0]
                    if dep_name not in result.dependencies:
                        result.dependencies.append(dep_name)
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names = [alias.asname or alias.name for alias in node.names]
                    result.imports.append(ImportInfo(
                        source=node.module,
                        line=node.lineno,
                        imported_names=imported_names
                    ))
                    if not node.module.startswith('.'):
                        dep_name = node.module.split('.')[0]
                        if dep_name not in result.dependencies:
                            result.dependencies.append(dep_name)
                            
            elif isinstance(node, ast.FunctionDef):
                # Extract docstring
                docstring = None
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    docstring = node.body[0].value.value
                
                # Check if function is async
                is_async = isinstance(node, ast.AsyncFunctionDef)
                
                # Extract return type annotation
                return_type = None
                if node.returns:
                    return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
                
                result.functions.append(FunctionInfo(
                    name=node.name,
                    params=[arg.arg for arg in node.args.args],
                    return_type=return_type,
                    line=node.lineno,
                    docstring=docstring,
                    is_async=is_async
                ))
                
            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                
                # Extract base classes
                extends = None
                if node.bases:
                    extends = ast.unparse(node.bases[0]) if hasattr(ast, 'unparse') else str(node.bases[0])
                
                result.classes.append(ClassInfo(
                    name=node.name,
                    methods=methods,
                    line=node.lineno,
                    extends=extends
                ))
                
            elif isinstance(node, ast.Call):
                # Extract API calls and database queries
                self._extract_python_calls(node, result, content)
                
            elif isinstance(node, (ast.Try, ast.ExceptHandler, ast.Raise)):
                # Extract error handling
                if isinstance(node, ast.Try):
                    result.error_handling.append(f"try-except block at line {node.lineno}")
                elif isinstance(node, ast.Raise):
                    result.error_handling.append(f"exception raised at line {node.lineno}")

    def _extract_python_calls(self, node, result: FileAnalysis, content: str):
        """Extract API calls and database queries from Python AST"""
        if isinstance(node.func, ast.Attribute):
            # Method calls like requests.get(), cursor.execute()
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                method_name = node.func.attr
                
                # HTTP requests
                if obj_name in ['requests', 'httpx', 'aiohttp'] and method_name in ['get', 'post', 'put', 'delete', 'patch']:
                    if node.args and isinstance(node.args[0], ast.Str):
                        url = node.args[0].s
                        result.api_endpoints.append(APIEndpoint(
                            method=method_name.upper(),
                            path=url,
                            line=node.lineno
                        ))
                
                # Database queries
                elif method_name in ['execute', 'query', 'select', 'insert', 'update', 'delete']:
                    if node.args and isinstance(node.args[0], ast.Str):
                        query = node.args[0].s
                        query_type = self._detect_sql_type(query)
                        result.database_queries.append(DatabaseQuery(
                            type=query_type,
                            line=node.lineno,
                            raw_query=query[:100] + "..." if len(query) > 100 else query
                        ))

    def _detect_sql_type(self, query: str) -> str:
        """Detect SQL query type"""
        query_lower = query.lower().strip()
        if query_lower.startswith('select'):
            return 'SELECT'
        elif query_lower.startswith('insert'):
            return 'INSERT'
        elif query_lower.startswith('update'):
            return 'UPDATE'
        elif query_lower.startswith('delete'):
            return 'DELETE'
        else:
            return 'OTHER'

    def _calculate_complexity(self, result: FileAnalysis) -> int:
        """Calculate complexity score for Python"""
        complexity = 0
        complexity += len(result.functions) * 2
        complexity += len(result.classes) * 3
        complexity += len(result.imports)
        complexity += len(result.api_endpoints) * 2
        complexity += len(result.database_queries) * 2
        return complexity

    def _regex_parse_python(self, content: str, result: FileAnalysis):
        """Fallback regex parsing for Python"""
        import re
        
        # Import extraction
        import_matches = re.findall(r'(?:from\s+(\S+)\s+)?import\s+([^\n]+)', content)
        for from_module, imports in import_matches:
            if from_module:
                result.imports.append(ImportInfo(source=from_module, line=0))
                if not from_module.startswith('.'):
                    dep_name = from_module.split('.')[0]
                    if dep_name not in result.dependencies:
                        result.dependencies.append(dep_name)
        
        # Function extraction
        func_matches = re.findall(r'def\s+(\w+)\s*\(([^)]*)\)', content)
        for func_name, params in func_matches:
            param_list = [p.strip().split('=')[0].strip() for p in params.split(',') if p.strip()]
            result.functions.append(FunctionInfo(name=func_name, params=param_list, line=0))
        
        # Class extraction
        class_matches = re.findall(r'class\s+(\w+)(?:\([^)]*\))?:', content)
        for cls in class_matches:
            result.classes.append(ClassInfo(name=cls, line=0))

        result.complexity_score = self._calculate_complexity(result)

class AsyncLLMProcessor:
    """Async batch processor for LLM analysis with advanced rate limiting"""
    
    def __init__(self, api_key: str, max_concurrent: int = 2):  # Reduced concurrency
        # Conservative rate limiting for Groq free tier
        self.rate_limiter = TokenAwareRateLimiter(
            max_tokens_per_minute=4500,  # Conservative limit (Groq free tier is 6000)
            max_calls_per_second=1.5     # Slower rate to avoid bursts
        )
        self.llm_client = GroqLLMClient(api_key, self.rate_limiter)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_files_batch(self, file_analyses: List[DetailedFileAnalysis], file_contents: Dict[str, str]) -> List[DetailedFileAnalysis]:
        """Process multiple files with LLM analysis in parallel with smart rate limiting"""
        print(f"🤖 Starting LLM analysis for {len(file_analyses)} files...")
        print(f"⚙️ Rate limits: {self.rate_limiter.max_tokens_per_minute} tokens/min, {self.max_concurrent} concurrent")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for file_analysis in file_analyses:
                if file_analysis.file in file_contents:
                    task = self._process_single_file(
                        session, 
                        file_analysis, 
                        file_contents[file_analysis.file]
                    )
                    tasks.append(task)
            
            # Process with smaller batches and longer delays for rate limiting
            results = []
            batch_size = 2  # Smaller batches
            
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                print(f"  Processing batch {i//batch_size + 1}/{(len(tasks) + batch_size - 1)//batch_size} ({len(batch)} files)...")
                
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"❌ Batch processing error: {result}")
                    else:
                        results.append(result)
                
                # Longer delay between batches to respect rate limits
                if i + batch_size < len(tasks):
                    print(f"  ⏳ Waiting 10s between batches for rate limiting...")
                    await asyncio.sleep(10)
        
        successful_summaries = len([r for r in results if r.llm_summary and r.llm_summary != "Code file analysis"])
        print(f"✅ LLM analysis completed: {successful_summaries}/{len(results)} files with AI summaries")
        return results
    
    async def _process_single_file(self, session: aiohttp.ClientSession, file_analysis: DetailedFileAnalysis, content: str) -> DetailedFileAnalysis:
        """Process a single file with rate limiting"""
        async with self.semaphore:
            try:
                # Ensure all necessary imports are available in async context
                import asyncio
                from pathlib import Path
                
                request = LLMSummaryRequest(
                    file_path=file_analysis.file,
                    content=content,
                    analysis=file_analysis
                )
                
                response = await self.llm_client.generate_summary(session, request)
                
                # Update file analysis with LLM results
                file_analysis.llm_summary = response.summary
                file_analysis.key_patterns = response.key_insights
                
                return file_analysis
                
            except Exception as e:
                print(f"❌ Error processing {file_analysis.file}: {e}")
                import traceback
                traceback.print_exc()
                return file_analysis

class FolderAnalyzer:
    """Analyzes folders and creates structured summaries"""
    
    def __init__(self, llm_processor: AsyncLLMProcessor = None):
        self.llm_processor = llm_processor
    
    def analyze_folders(self, files_data: List[DetailedFileAnalysis]) -> Dict[str, FolderSummary]:
        """Analyze files grouped by folders"""
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
        """Create a comprehensive folder summary"""
        
        # Aggregate data
        all_api_endpoints = []
        all_dependencies = set()
        languages = {}
        service_types = set()
        
        for file_data in files:
            # Collect API endpoints
            if hasattr(file_data, 'api_endpoints'):
                all_api_endpoints.extend(file_data.api_endpoints)
            
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
        """Determine the main purpose of a folder"""
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
        """Extract key components from files in the folder"""
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
        """Detect integration patterns in the folder"""
        patterns = set()
        
        for file_data in files:
            if hasattr(file_data, 'integration_points'):
                patterns.update(file_data.integration_points)
        
        return list(patterns)
    
    async def generate_folder_summaries_with_llm(self, folder_summaries: Dict[str, FolderSummary]) -> Dict[str, FolderSummary]:
        """Generate LLM summaries for folders"""
        if not self.llm_processor:
            return folder_summaries
        
        print("🤖 Generating folder-level summaries...")
        
        for folder_path, folder_summary in folder_summaries.items():
            try:
                # Create prompt for folder analysis
                prompt = self._build_folder_analysis_prompt(folder_summary)
                
                # This would need to be implemented to work with the LLM processor
                # For now, we'll create a basic summary
                folder_summary.llm_summary = f"Folder containing {folder_summary.total_files} files focused on {folder_summary.folder_purpose}"
                
            except Exception as e:
                print(f"❌ Failed to generate summary for folder {folder_path}: {e}")
                folder_summary.llm_summary = f"Folder with {folder_summary.total_files} {folder_summary.primary_language} files"
        
        return folder_summaries
    
    def _build_folder_analysis_prompt(self, folder_summary: FolderSummary) -> str:
        """Build prompt for folder-level analysis"""
        return f"""Analyze this folder and provide a comprehensive summary:

FOLDER: {folder_summary.folder_path}
FILES: {folder_summary.total_files}
PRIMARY_LANGUAGE: {folder_summary.primary_language}
SERVICE_TYPE: {folder_summary.service_type}
PURPOSE: {folder_summary.folder_purpose}
API_ENDPOINTS: {len(folder_summary.api_endpoints)}
KEY_COMPONENTS: {', '.join(folder_summary.key_components[:5])}
DEPENDENCIES: {', '.join(folder_summary.shared_dependencies[:10])}

Provide analysis in this format:
FOLDER_SUMMARY: [Comprehensive description of what this folder contains and its role]
ARCHITECTURE_ROLE: [How this folder fits into the overall system architecture]
KEY_FUNCTIONALITY: [Main functionality provided by files in this folder]
API_DOCUMENTATION: [If APIs exist, document them with usage examples]
INTEGRATION_POINTS: [How this folder integrates with other parts of the system]
SETUP_REQUIREMENTS: [What's needed to run/use code in this folder]
USAGE_INSTRUCTIONS: [How developers should work with this folder]
IMPROVEMENTS: [Suggestions for better organization or functionality]

Focus on:
- Overall purpose and responsibility of this folder
- Key APIs and how to use them
- Integration with other system components
- Setup and usage instructions for developers"""

class EnhancedRepositoryAnalyzer:
    def __init__(self, repo_path: str, enable_llm: bool = True, groq_api_key: str = None):
        self.repo_path = Path(repo_path)
        self.code_analyzer = DetailedCodeAnalyzer()
        self.files_data = []
        self.file_contents = {}  # Store file contents for LLM processing
        self.enable_llm = enable_llm and groq_api_key
        
        if self.enable_llm:
            self.llm_processor = AsyncLLMProcessor(groq_api_key)
        else:
            print("⚠️ LLM analysis disabled (no API key provided)")

    def analyze(self):
        print(f'📂 Analyzing repository: {self.repo_path}')
        
        # Step 1: Parse all files
        self._walk_repository()
        print(f'✅ Parsed {len(self.files_data)} files')

        # Step 2: Run LLM analysis if enabled
        if self.enable_llm and self.files_data:
            try:
                # Run async LLM processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                enhanced_files = loop.run_until_complete(
                    self.llm_processor.process_files_batch(self.files_data, self.file_contents)
                )
                self.files_data = enhanced_files
                loop.close()
            except Exception as e:
                print(f"❌ LLM processing failed: {e}")

        # Step 3: Generate additional analysis
        dependency_data = self._generate_dependencies()
        call_data = self._generate_call_graph()
        
        return {
            'total_files': len(self.files_data),
            'files': [convert_to_dict(f) for f in self.files_data],  # Convert to dict safely
            'dependencies': dependency_data,
            'call_graph': call_data,
            'llm_enabled': self.enable_llm
        }

    def _walk_repository(self):
        """Walk repository and parse files"""
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]

            for file in files:
                file_path = Path(root) / file
                language = get_file_language(file)

                if language:
                    try:
                        file_data = self._parse_file(file_path, language)
                        if file_data:
                            self.files_data.append(file_data)
                            
                            # Store file content for LLM processing
                            if self.enable_llm:
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        self.file_contents[file_data.file] = f.read()
                                except:
                                    pass
                            
                            if len(self.files_data) % 10 == 0:
                                print(f'  Parsed {len(self.files_data)} files...', end='\r')
                    except Exception as e:
                        continue

    def _parse_file(self, file_path: Path, language: str) -> Optional[DetailedFileAnalysis]:
        """Parse individual file with detailed analysis"""
        rel_path = str(file_path.relative_to(self.repo_path)).replace('\\', '/')
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use DetailedCodeAnalyzer for comprehensive analysis
            detailed_analysis = self.code_analyzer.analyze_file_detailed(str(file_path), rel_path, content)
            
            return detailed_analysis
            
        except Exception as e:
            print(f"⚠️ Failed to parse {rel_path}: {e}")
            return None

    def _generate_dependencies(self):
        """Generate dependency analysis"""
        external_deps = {}
        internal_deps = {}
        
        for file_data in self.files_data:
            for imp in file_data.imports:
                source = imp.source
                
                if source.startswith('.') or source.startswith('/'):
                    # Internal dependency
                    if source not in internal_deps:
                        internal_deps[source] = []
                    internal_deps[source].append(file_data.file)
                else:
                    # External dependency
                    dep_name = source.split('/')[0]
                    if dep_name not in external_deps:
                        external_deps[dep_name] = []
                    external_deps[dep_name].append(file_data.file)

        return {
            'external_deps': external_deps,
            'internal_deps': internal_deps,
            'total_external': len(external_deps),
            'total_internal': len(internal_deps)
        }

    def _generate_call_graph(self):
        """Generate function call graph"""
        nodes = []
        
        for file_data in self.files_data:
            for func in file_data.functions:
                nodes.append({
                    'id': f"{file_data.file}:{func.name}",
                    'name': func.name,
                    'file': file_data.file,
                    'params': func.params,
                    'line': func.line,
                    'complexity': func.complexity,
                    'is_async': func.is_async,
                    'is_exported': func.is_exported
                })

        return {
            'nodes': nodes,
            'total_functions': len(nodes),
            'async_functions': len([n for n in nodes if n['is_async']]),
            'exported_functions': len([n for n in nodes if n['is_exported']])
        }

class EnhancedDocumentationGenerator:
    """Enhanced documentation generator with detailed summaries and API docs"""
    
    def __init__(self, files_data, dependencies, call_graph, repo_info, output_dir):
        print(f"🔧 Initializing EnhancedDocumentationGenerator...")
        print(f"  - files_data: {type(files_data)} ({len(files_data) if files_data else 0} items)")
        print(f"  - dependencies: {type(dependencies)}")
        print(f"  - call_graph: {type(call_graph)}")
        print(f"  - repo_info: {type(repo_info)}")
        print(f"  - output_dir: {output_dir}")
        
        self.files_data = files_data
        self.dependencies = dependencies
        self.dependency_data = dependencies  # Also set this for compatibility
        self.call_graph = call_graph
        self.call_data = call_graph  # Also set this for compatibility
        self.repo_info = repo_info
        self.output_dir = Path(output_dir)
        self.docs_dir = self.output_dir / 'docs'
        self.summaries_dir = self.output_dir / 'summaries'
        
        print(f"✅ Set self.dependencies = {self.dependencies}")
        
        # Create directories
        try:
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            self.summaries_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directories: {self.docs_dir}, {self.summaries_dir}")
        except Exception as e:
            print(f"⚠️ Failed to create directories: {e}")
            # Ensure attributes exist even if directory creation fails
            if not hasattr(self, 'summaries_dir'):
                self.summaries_dir = self.output_dir / 'summaries'
    
    def generate_all_enhanced(self):
        """Generate all enhanced documentation"""
        print('📝 Generating enhanced documentation...')
        print(f"🔧 Debug: self.dependencies = {getattr(self, 'dependencies', 'NOT_SET')}")
        print(f"🔧 Debug: self.__dict__.keys() = {list(self.__dict__.keys())}")
        
        # Convert dict files back to objects if needed
        processed_files = []
        for file_data in self.files_data:
            if isinstance(file_data, dict):
                # Convert dict back to object with proper attribute access
                processed_file = dict_to_object(file_data)
                processed_files.append(processed_file)
            else:
                processed_files.append(file_data)
        
        # Analyze folders - use simpler approach without strict Pydantic validation
        folder_analyzer = FolderAnalyzer(None)
        try:
            folder_summaries = folder_analyzer.analyze_folders(processed_files)
        except Exception as e:
            print(f"⚠️ Folder analysis failed: {e}")
            # Create simple folder summaries
            folder_summaries = {
                'root': type('FolderSummary', (), {
                    'folder_path': 'root',
                    'total_files': len(processed_files),
                    'primary_language': 'mixed',
                    'service_type': 'mixed',
                    'folder_purpose': 'Repository root',
                    'files': [getattr(f, 'file', 'unknown') for f in processed_files],
                    'api_endpoints': [],
                    'key_components': [],
                    'shared_dependencies': [],
                    'integration_patterns': [],
                    'llm_summary': f'Root folder with {len(processed_files)} files'
                })()
            }
        
        # Generate detailed summaries
        self._generate_detailed_file_summaries()
        self._generate_folder_summaries(folder_summaries)
        self._generate_global_api_documentation()
        self._generate_environment_setup_guide()
        self._generate_service_architecture_docs()
        
        # Generate enhanced README
        self._generate_enhanced_readme(folder_summaries)
        
        # Generate original docs for compatibility
        self._generate_summary()
        self._generate_architecture()
        self._generate_files()
        
        print('✅ Enhanced documentation generation complete!')
    
    def _generate_detailed_file_summaries(self):
        """Generate detailed JSON summaries for each file"""
        print('  📄 Generating detailed file summaries...')
        
        # Ensure summaries_dir exists
        if not hasattr(self, 'summaries_dir'):
            self.summaries_dir = self.output_dir / 'summaries'
            self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        for file_data in self.files_data:
            file_summary = {
                "file_info": {
                    "path": file_data.get('file', ''),
                    "language": file_data.get('language', ''),
                    "lines_of_code": file_data.get('lines_of_code', 0),
                    "complexity_score": file_data.get('complexity_score', 0),
                    "file_purpose": file_data.get('file_purpose', 'Unknown')
                },
                "functions": [],
                "classes": [],
                "api_endpoints": [],
                "environment_variables": [],
                "dependencies": file_data.get('dependencies', []),
                "integration_points": file_data.get('integration_points', []),
                "llm_analysis": {
                    "summary": file_data.get('llm_summary', 'No AI analysis available'),
                    "key_insights": file_data.get('key_patterns', []),
                    "improvements": []
                }
            }
            
            # Process functions
            for func in file_data.get('functions', []):
                func_info = {
                    "name": func.get('name') if isinstance(func, dict) else func.name,
                    "parameters": func.get('params', []) if isinstance(func, dict) else func.params,
                    "line": func.get('line', 0) if isinstance(func, dict) else func.line,
                    "is_async": func.get('is_async', False) if isinstance(func, dict) else getattr(func, 'is_async', False),
                    "return_type": func.get('return_type') if isinstance(func, dict) else getattr(func, 'return_type', None),
                    "description": f"Function {func.get('name') if isinstance(func, dict) else func.name} with {len(func.get('params', []) if isinstance(func, dict) else func.params)} parameters"
                }
                file_summary["functions"].append(func_info)
            
            # Process API endpoints
            for api in file_data.get('api_endpoints', []):
                api_info = {
                    "method": api.get('method') if isinstance(api, dict) else api.method,
                    "path": api.get('path') if isinstance(api, dict) else api.path,
                    "line": api.get('line', 0) if isinstance(api, dict) else api.line,
                    "function_name": api.get('function_name') if isinstance(api, dict) else getattr(api, 'function_name', None),
                    "parameters": api.get('parameters', []) if isinstance(api, dict) else getattr(api, 'parameters', []),
                    "description": f"{api.get('method') if isinstance(api, dict) else api.method} endpoint for {api.get('path') if isinstance(api, dict) else api.path}",
                    "usage_example": self._generate_api_usage_example(api)
                }
                file_summary["api_endpoints"].append(api_info)
            
            # Save file summary
            safe_filename = file_data.get('file', 'unknown').replace('/', '_').replace('\\', '_')
            summary_file = self.summaries_dir / f"{safe_filename}.json"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(file_summary, f, indent=2, ensure_ascii=False)
    
    def _generate_api_usage_example(self, api) -> str:
        """Generate usage example for API endpoint"""
        method = api.get('method') if isinstance(api, dict) else api.method
        path = api.get('path') if isinstance(api, dict) else api.path
        
        if method == 'GET':
            return f"""// JavaScript fetch example
fetch('{path}')
  .then(response => response.json())
  .then(data => console.log(data));

# Python requests example
import requests
response = requests.get('{path}')
data = response.json()"""
        
        elif method == 'POST':
            return f"""// JavaScript fetch example
fetch('{path}', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{ /* your data */ }})
}})
.then(response => response.json());

# Python requests example
import requests
response = requests.post('{path}', json={{"key": "value"}})"""
        
        return f"// {method} request to {path}"
    
    def _generate_folder_summaries(self, folder_summaries: Dict[str, FolderSummary]):
        """Generate folder-level summary JSON files"""
        print('  📁 Generating folder summaries...')
        
        for folder_path, folder_summary in folder_summaries.items():
            folder_data = {
                "folder_info": {
                    "path": folder_summary.folder_path,
                    "total_files": folder_summary.total_files,
                    "primary_language": folder_summary.primary_language,
                    "service_type": folder_summary.service_type,
                    "purpose": folder_summary.folder_purpose
                },
                "files": folder_summary.files,
                "api_endpoints": [
                    {
                        "method": api.method,
                        "path": api.path,
                        "function_name": api.function_name,
                        "description": api.description,
                        "usage_example": self._generate_api_usage_example(api)
                    }
                    for api in folder_summary.api_endpoints
                ],
                "key_components": folder_summary.key_components,
                "dependencies": folder_summary.shared_dependencies,
                "integration_patterns": folder_summary.integration_patterns,
                "llm_summary": folder_summary.llm_summary or f"Folder containing {folder_summary.total_files} files for {folder_summary.folder_purpose}"
            }
            
            safe_folder_name = folder_path.replace('/', '_').replace('\\', '_')
            folder_file = self.summaries_dir / f"folder_{safe_folder_name}.json"
            
            with open(folder_file, 'w', encoding='utf-8') as f:
                json.dump(folder_data, f, indent=2, ensure_ascii=False)
    
    def _generate_global_api_documentation(self):
        """Generate comprehensive API documentation"""
        print('  🌐 Generating global API documentation...')
        
        all_apis = []
        api_groups = {}
        
        # Collect all API endpoints
        for file_data in self.files_data:
            for api in file_data.get('api_endpoints', []):
                api_info = {
                    "method": api.get('method') if isinstance(api, dict) else api.method,
                    "path": api.get('path') if isinstance(api, dict) else api.path,
                    "file": file_data.get('file', ''),
                    "function_name": api.get('function_name') if isinstance(api, dict) else getattr(api, 'function_name', None),
                    "line": api.get('line', 0) if isinstance(api, dict) else api.line,
                    "description": f"{api.get('method') if isinstance(api, dict) else api.method} endpoint for {api.get('path') if isinstance(api, dict) else api.path}",
                    "usage_example": self._generate_api_usage_example(api)
                }
                all_apis.append(api_info)
                
                # Group by base path
                base_path = api_info["path"].split('/')[1] if '/' in api_info["path"] else 'root'
                if base_path not in api_groups:
                    api_groups[base_path] = []
                api_groups[base_path].append(api_info)
        
        # Create global API documentation
        api_docs = {
            "api_overview": {
                "total_endpoints": len(all_apis),
                "api_groups": list(api_groups.keys()),
                "base_url": "http://localhost:3000",  # Default, should be detected
                "authentication": "To be determined from code analysis"
            },
            "endpoint_groups": api_groups,
            "all_endpoints": all_apis
        }
        
        # Save global API docs
        with open(self.summaries_dir / 'global_api_documentation.json', 'w', encoding='utf-8') as f:
            json.dump(api_docs, f, indent=2, ensure_ascii=False)
        
        # Generate markdown API docs
        self._generate_api_markdown(api_docs)
    
    def _generate_api_markdown(self, api_docs):
        """Generate markdown API documentation"""
        content = f"""# API Documentation

## Overview
- **Total Endpoints**: {api_docs['api_overview']['total_endpoints']}
- **Base URL**: {api_docs['api_overview']['base_url']}
- **API Groups**: {', '.join(api_docs['api_overview']['api_groups'])}

## Authentication
{api_docs['api_overview']['authentication']}

## Endpoints by Group

"""
        
        for group_name, endpoints in api_docs['endpoint_groups'].items():
            content += f"### {group_name.title()} APIs\n\n"
            
            for api in endpoints:
                content += f"#### {api['method']} {api['path']}\n\n"
                content += f"**File**: `{api['file']}`\n"
                if api['function_name']:
                    content += f"**Function**: `{api['function_name']}`\n"
                content += f"**Description**: {api['description']}\n\n"
                content += "**Usage Example**:\n```javascript\n"
                content += api['usage_example']
                content += "\n```\n\n"
        
        with open(self.docs_dir / 'API_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_environment_setup_guide(self):
        """Generate environment setup guide based on detected variables"""
        print('  🔧 Generating environment setup guide...')
        
        all_env_vars = set()
        services_detected = set()
        ports_detected = set()
        
        # Collect environment variables and service info
        for file_data in self.files_data:
            # Collect env vars (if available in enhanced analysis)
            if hasattr(file_data, 'environment_variables'):
                for env_var in file_data.get('environment_variables', []):
                    all_env_vars.add(env_var.get('name') if isinstance(env_var, dict) else env_var.name)
            
            # Detect services
            if hasattr(file_data, 'service_info') and file_data.get('service_info'):
                service_info = file_data['service_info']
                if service_info.get('type'):
                    services_detected.add(service_info['type'])
                if service_info.get('port'):
                    ports_detected.add(service_info['port'])
        
        # Generate setup guide
        setup_guide = {
            "project_setup": {
                "services_detected": list(services_detected),
                "ports_used": list(ports_detected),
                "environment_variables": list(all_env_vars)
            },
            "installation_steps": [
                "1. Clone the repository",
                "2. Install dependencies",
                "3. Set up environment variables",
                "4. Start the services"
            ],
            "environment_variables": {
                var: {
                    "description": f"Environment variable {var}",
                    "required": True,
                    "example": "your_value_here"
                }
                for var in all_env_vars
            },
            "service_commands": self._generate_service_commands(services_detected)
        }
        
        with open(self.summaries_dir / 'environment_setup.json', 'w', encoding='utf-8') as f:
            json.dump(setup_guide, f, indent=2, ensure_ascii=False)
    
    def _generate_service_commands(self, services_detected):
        """Generate commands to run different services"""
        commands = {}
        
        if 'frontend' in services_detected:
            commands['frontend'] = {
                "install": "npm install",
                "dev": "npm run dev",
                "build": "npm run build",
                "start": "npm start"
            }
        
        if 'backend' in services_detected:
            commands['backend'] = {
                "install": "pip install -r requirements.txt",
                "dev": "python app.py",
                "start": "python server.py"
            }
        
        return commands
    
    def _generate_service_architecture_docs(self):
        """Generate service architecture documentation"""
        print('  🏗️ Generating service architecture documentation...')
        
        services = {}
        for file_data in self.files_data:
            if hasattr(file_data, 'service_info') and file_data.get('service_info'):
                service_type = file_data['service_info'].get('type', 'unknown')
                if service_type not in services:
                    services[service_type] = {
                        "files": [],
                        "framework": file_data['service_info'].get('framework'),
                        "port": file_data['service_info'].get('port'),
                        "dependencies": set()
                    }
                
                services[service_type]["files"].append(file_data.get('file', ''))
                services[service_type]["dependencies"].update(file_data.get('dependencies', []))
        
        # Convert sets to lists for JSON serialization
        for service in services.values():
            service["dependencies"] = list(service["dependencies"])
        
        architecture_docs = {
            "services": services,
            "architecture_overview": f"System with {len(services)} service types",
            "service_interactions": "To be analyzed from API calls and dependencies"
        }
        
        with open(self.summaries_dir / 'service_architecture.json', 'w', encoding='utf-8') as f:
            json.dump(architecture_docs, f, indent=2, ensure_ascii=False)
    
    def _generate_enhanced_readme(self, folder_summaries):
        """Generate enhanced README with detailed setup instructions"""
        print('  📖 Generating enhanced README...')
        
        # Detect project type and main services
        has_frontend = any('frontend' in str(folder).lower() or 'src' in str(folder) for folder in folder_summaries.keys())
        has_backend = any('backend' in str(folder).lower() or 'server' in str(folder) or 'api' in str(folder) for folder in folder_summaries.keys())
        
        content = f"""# {self.repo_info.get('name', 'Repository')}

{self.repo_info.get('description', 'A software project with comprehensive documentation')}

[![Stars](https://img.shields.io/github/stars/{self.repo_info['owner']}/{self.repo_info['name']})](https://github.com/{self.repo_info['owner']}/{self.repo_info['name']}/stargazers)
[![License](https://img.shields.io/github/license/{self.repo_info['owner']}/{self.repo_info['name']})](LICENSE)

## 🏗️ Architecture Overview

This project consists of the following components:

"""
        
        # Add service descriptions
        if has_frontend:
            content += "- **Frontend**: User interface and client-side application\n"
        if has_backend:
            content += "- **Backend**: Server-side API and business logic\n"
        
        content += f"""
## 📊 Project Statistics

- **Total Files**: {len(self.files_data)}
- **Total Functions**: {sum(len(f.get('functions', [])) for f in self.files_data)}
- **Total Classes**: {sum(len(f.get('classes', [])) for f in self.files_data)}
- **API Endpoints**: {sum(len(f.get('api_endpoints', [])) for f in self.files_data)}
- **External Dependencies**: {getattr(self, 'dependencies', getattr(self, 'dependency_data', {})).get('total_external', 0)}

## 🚀 Quick Start

### Prerequisites
- Node.js (for frontend)
- Python (for backend services)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone {self.repo_info.get('url', '')}
   cd {self.repo_info.get('name', '')}
   ```

"""
        
        if has_frontend:
            content += """2. **Setup Frontend**
   ```bash
   cd frontend  # or appropriate frontend directory
   npm install
   npm run dev
   ```

"""
        
        if has_backend:
            content += """3. **Setup Backend**
   ```bash
   cd backend  # or appropriate backend directory
   pip install -r requirements.txt
   python app.py
   ```

"""
        
        content += """### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Add your environment variables here
# Check summaries/environment_setup.json for complete list
```

## 📚 Documentation

### Detailed Documentation
- [📊 Project Summary](docs/SUMMARY.md) - Overview and statistics
- [🌐 API Documentation](docs/API_DOCUMENTATION.md) - Complete API reference
- [🏗️ Architecture](docs/ARCHITECTURE.md) - System architecture and dependencies

### Detailed Analysis
- [📁 Folder Summaries](summaries/) - Detailed analysis of each folder
- [📄 File Analysis](summaries/) - Individual file documentation
- [🔧 Environment Setup](summaries/environment_setup.json) - Setup requirements
- [🏗️ Service Architecture](summaries/service_architecture.json) - Service breakdown

## 🔗 API Endpoints

"""
        
        # Add API summary
        total_apis = sum(len(f.get('api_endpoints', [])) for f in self.files_data)
        if total_apis > 0:
            content += f"This project exposes {total_apis} API endpoints. See [API Documentation](docs/API_DOCUMENTATION.md) for complete details.\n\n"
        else:
            content += "No API endpoints detected in the current analysis.\n\n"
        
        content += """## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

---

*This documentation was automatically generated using AI-powered code analysis.*
"""
        
        with open(self.output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Keep original methods for compatibility
    def _generate_summary(self):
        """Generate basic summary (compatibility)"""
        pass  # Implementation from original class
    
    def _generate_architecture(self):
        """Generate architecture docs (compatibility)"""
        pass  # Implementation from original class
    
    def _generate_files(self):
        """Generate files documentation (compatibility)"""
        pass  # Implementation from original class
    def __init__(self, files_data, dependency_data, call_data, repo_info, output_dir):
        self.files_data = files_data
        self.dependency_data = dependency_data
        self.call_data = call_data
        self.repo_info = repo_info
        self.output_dir = Path(output_dir)
        self.docs_dir = self.output_dir / 'docs'
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self):
        print('📝 Generating documentation...')

        # Generate all documentation files
        self._generate_readme()
        self._generate_summary()
        self._generate_architecture()
        self._generate_files()
        self._generate_components()
        self._generate_dependencies()
        self._generate_routes()
        self._generate_call_graph()
        self._generate_api_docs()
        self._generate_code_of_conduct()
        self._generate_contributing()
        self._generate_index()

    def _generate_readme(self):
        content = f"""# {self.repo_info.get('name', 'Repository')} Documentation

{self.repo_info.get('description', 'A software project')}

[![Stars](https://img.shields.io/github/stars/{self.repo_info['owner']}/{self.repo_info['name']})](https://github.com/{self.repo_info['owner']}/{self.repo_info['name']}/stargazers)
[![License](https://img.shields.io/github/license/{self.repo_info['owner']}/{self.repo_info['name']})](LICENSE)

## 📊 Project Statistics

- **Total Files:** {len(self.files_data)}
- **Total Functions:** {sum(len(f['functions']) for f in self.files_data)}
- **Total Classes:** {sum(len(f['classes']) for f in self.files_data)}
- **External Dependencies:** {len(self.dependency_data['external_deps'])}

## 📚 Documentation

Explore the generated documentation:

- [📊 Summary](docs/SUMMARY.md) - Project overview and statistics
- [🏗️ Architecture](docs/ARCHITECTURE.md) - Dependency graphs and structure
- [📁 Files](docs/FILES.md) - Detailed file documentation
- [⚛️ Components](docs/COMPONENTS.md) - React/JSX components
- [📦 Dependencies](docs/DEPENDENCIES.md) - Dependency analysis
- [🛣️ Routes](docs/ROUTES.md) - Application routes
- [🔗 Call Graph](docs/CALL_GRAPH.md) - Function relationships

## 📄 Additional Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🚀 Quick Start

1. Clone the repository
2. Install dependencies
3. Follow setup instructions in the documentation
"""

        with open(self.output_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_summary(self):
        content = "# Enhanced Repository Summary\n\n"
        content += f"**Total Files Analyzed:** {len(self.files_data)}\n\n"

        by_lang = {}
        total_complexity = 0
        files_with_llm = 0
        
        for file_data in self.files_data:
            lang = file_data.get('language', 'unknown')
            by_lang[lang] = by_lang.get(lang, 0) + 1
            total_complexity += file_data.get('complexity_score', 0)
            if file_data.get('llm_summary'):
                files_with_llm += 1

        content += "## Files by Language\n\n"
        content += "| Language | Count | Avg Complexity |\n|----------|-------|----------------|\n"
        for lang, count in sorted(by_lang.items(), key=lambda x: -x[1]):
            lang_files = [f for f in self.files_data if f.get('language') == lang]
            avg_complexity = sum(f.get('complexity_score', 0) for f in lang_files) / count if count > 0 else 0
            content += f"| {lang} | {count} | {avg_complexity:.1f} |\n"

        total_funcs = sum(len(f.get('functions', [])) for f in self.files_data)
        total_classes = sum(len(f.get('classes', [])) for f in self.files_data)
        total_imports = sum(len(f.get('imports', [])) for f in self.files_data)
        total_apis = sum(len(f.get('api_endpoints', [])) for f in self.files_data)
        total_db_queries = sum(len(f.get('database_queries', [])) for f in self.files_data)

        content += f"\n## Enhanced Code Statistics\n\n"
        content += f"- **Total Functions:** {total_funcs}\n"
        content += f"- **Total Classes:** {total_classes}\n"
        content += f"- **Total Imports:** {total_imports}\n"
        content += f"- **API Endpoints:** {total_apis}\n"
        content += f"- **Database Queries:** {total_db_queries}\n"
        content += f"- **External Dependencies:** {self.dependency_data.get('total_external', 0)}\n"
        content += f"- **Internal Dependencies:** {self.dependency_data.get('total_internal', 0)}\n"
        content += f"- **Total Complexity Score:** {total_complexity}\n"
        content += f"- **Average Complexity per File:** {total_complexity / len(self.files_data):.1f}\n"

        if files_with_llm > 0:
            content += f"\n## AI Analysis Results\n\n"
            content += f"- **Files with LLM Summaries:** {files_with_llm}/{len(self.files_data)} ({files_with_llm/len(self.files_data)*100:.1f}%)\n"

        with open(self.docs_dir / 'SUMMARY.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_architecture(self):
        content = "# Architecture Overview\n\n"
        content += "## External Dependencies Graph\n\n"
        content += "```mermaid\ngraph LR\n"

        for dep, files in list(self.dependency_data['external_deps'].items())[:15]:
            dep_node = dep.replace('-', '_').replace('.', '_').replace('@', '')
            content += f"    {dep_node}[{dep}]\n"
            for file in files[:3]:
                file_node = Path(file).stem.replace('-', '_').replace('.', '_')
                content += f"    {file_node}[{Path(file).name}] --> {dep_node}\n"

        content += "```\n\n"

        with open(self.docs_dir / 'ARCHITECTURE.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_files(self):
        content = "# Enhanced Files Documentation\n\n"
        content += f"Total files documented: {len(self.files_data)}\n\n"

        for file_data in sorted(self.files_data, key=lambda x: x.get('file', '')):
            content += f"## {file_data.get('file', 'Unknown')}\n\n"
            
            # Basic info
            lang = file_data.get('language', 'unknown')
            func_count = len(file_data.get('functions', []))
            class_count = len(file_data.get('classes', []))
            complexity = file_data.get('complexity_score', 0)
            loc = file_data.get('lines_of_code', 0)
            
            content += f"**Language:** {lang} | **Functions:** {func_count} | **Classes:** {class_count} | **Complexity:** {complexity} | **LOC:** {loc}\n\n"

            # LLM Summary if available
            if file_data.get('llm_summary'):
                content += "### 🤖 AI Summary\n\n"
                content += f"{file_data['llm_summary']}\n\n"
                
                if file_data.get('key_patterns'):
                    content += "**Key Insights:**\n"
                    for insight in file_data['key_patterns'][:3]:
                        content += f"- {insight}\n"
                    content += "\n"

            # Functions
            if file_data.get('functions'):
                content += "### Functions\n\n"
                for func in file_data['functions'][:10]:
                    func_name = func.get('name', 'unknown') if isinstance(func, dict) else func.name
                    func_params = func.get('params', []) if isinstance(func, dict) else func.params
                    func_line = func.get('line', 0) if isinstance(func, dict) else func.line
                    is_async = func.get('is_async', False) if isinstance(func, dict) else getattr(func, 'is_async', False)
                    
                    params_str = ', '.join(func_params) if func_params else ''
                    async_marker = "async " if is_async else ""
                    content += f"- `{async_marker}{func_name}({params_str})` - line {func_line}\n"
                content += "\n"

            # Classes
            if file_data.get('classes'):
                content += "### Classes\n\n"
                for cls in file_data['classes'][:5]:
                    cls_name = cls.get('name', 'unknown') if isinstance(cls, dict) else cls.name
                    cls_line = cls.get('line', 0) if isinstance(cls, dict) else cls.line
                    methods = cls.get('methods', []) if isinstance(cls, dict) else cls.methods
                    
                    content += f"- `{cls_name}` - line {cls_line}"
                    if methods:
                        content += f" (methods: {', '.join(methods[:3])})"
                    content += "\n"
                content += "\n"

            # API Endpoints
            if file_data.get('api_endpoints'):
                content += "### API Endpoints\n\n"
                for api in file_data['api_endpoints'][:5]:
                    method = api.get('method', 'GET') if isinstance(api, dict) else api.method
                    path = api.get('path', '') if isinstance(api, dict) else api.path
                    line = api.get('line', 0) if isinstance(api, dict) else api.line
                    content += f"- `{method} {path}` - line {line}\n"
                content += "\n"

            # Database Queries
            if file_data.get('database_queries'):
                content += "### Database Queries\n\n"
                for db in file_data['database_queries'][:3]:
                    query_type = db.get('type', 'UNKNOWN') if isinstance(db, dict) else db.type
                    line = db.get('line', 0) if isinstance(db, dict) else db.line
                    content += f"- `{query_type}` query - line {line}\n"
                content += "\n"

            content += "---\n\n"

        with open(self.docs_dir / 'FILES.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_components(self):
        content = "# Component Documentation\n\n"

        react_files = [f for f in self.files_data if f['language'] in ['jsx', 'tsx']]

        if react_files:
            content += f"Total React/TSX files: {len(react_files)}\n\n"

            for file_data in react_files:
                content += f"### {file_data.get('file', 'Unknown')}\n\n"

                if file_data.get('functions'):
                    # Handle both dict and object formats
                    functions = file_data['functions']
                    if functions and isinstance(functions[0], dict):
                        component_funcs = [f for f in functions if f.get('name', '')[0:1].isupper()]
                    else:
                        component_funcs = [f for f in functions if f.name[0:1].isupper()]
                    
                    if component_funcs:
                        content += "**Components:**\n"
                        for func in component_funcs:
                            func_name = func.get('name') if isinstance(func, dict) else func.name
                            func_line = func.get('line', 0) if isinstance(func, dict) else func.line
                            content += f"- `{func_name}` (line {func_line})\n"
                        content += "\n"

                if file_data.get('jsx_components'):
                    jsx_types = {}
                    for component in file_data['jsx_components']:
                        jsx_types[component] = jsx_types.get(component, 0) + 1
                    content += "**JSX Elements Used:**\n"
                    for jsx_type, count in sorted(jsx_types.items()):
                        content += f"- `<{jsx_type}>` ({count} times)\n"
                    content += "\n"
        else:
            content += "No React/JSX components found.\n"

        with open(self.docs_dir / 'COMPONENTS.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_dependencies(self):
        content = "# Dependencies Analysis\n\n"
        content += "## External Dependencies\n\n"
        content += f"Total external packages: {len(self.dependency_data['external_deps'])}\n\n"

        sorted_deps = sorted(self.dependency_data['external_deps'].items(),
                            key=lambda x: len(x[1]), reverse=True)

        content += "| Package | Files Using | Files |\n|---------|-------------|-------|\n"
        for dep, files in sorted_deps[:30]:
            file_list = ', '.join([Path(f).name for f in files[:3]])
            if len(files) > 3:
                file_list += f" +{len(files)-3} more"
            content += f"| `{dep}` | {len(files)} | {file_list} |\n"

        with open(self.docs_dir / 'DEPENDENCIES.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_routes(self):
        content = "# Routes & Pages\n\n"

        route_patterns = ['app/', 'pages/', 'routes/', 'views/']
        route_files = [f for f in self.files_data if any(pattern in f['file'] for pattern in route_patterns)]

        if route_files:
            content += f"Total route files detected: {len(route_files)}\n\n"

            for file_data in sorted(route_files, key=lambda x: x.get('file', '')):
                content += f"### {file_data.get('file', 'Unknown')}\n\n"

                if file_data.get('functions'):
                    content += "**Handlers/Components:**\n"
                    functions = file_data['functions']
                    for func in functions[:5]:
                        func_name = func.get('name') if isinstance(func, dict) else func.name
                        func_line = func.get('line', 0) if isinstance(func, dict) else func.line
                        content += f"- `{func_name}` (line {func_line})\n"
                    content += "\n"
        else:
            content += "No route files detected.\n"

        with open(self.docs_dir / 'ROUTES.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_call_graph(self):
        content = "# Call Graph & Functions\n\n"
        content += f"Total functions: {len(self.call_data['nodes'])}\n\n"

        func_by_file = defaultdict(list)
        for node in self.call_data['nodes']:
            func_by_file[node['file']].append(node)

        sorted_files = sorted(func_by_file.items(),
                             key=lambda x: len(x[1]), reverse=True)[:20]

        content += "| File | Functions |\n|------|----------|\n"
        for file, funcs in sorted_files:
            func_names = ', '.join([f['name'] for f in funcs[:5]])
            if len(funcs) > 5:
                func_names += f" +{len(funcs)-5} more"
            content += f"| {file} | {func_names} |\n"

        with open(self.docs_dir / 'CALL_GRAPH.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_api_docs(self):
        content = """# API Documentation

This document contains API endpoint information extracted from the codebase.

## Endpoints

No API endpoints detected in the analyzed files.

This could mean:
- The project doesn't expose REST APIs
- APIs are defined in files not yet analyzed
- APIs use patterns not currently detected
"""

        with open(self.output_dir / 'API_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_code_of_conduct(self):
        content = """# Code of Conduct

## Our Pledge

We pledge to make participation in our community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the community leaders responsible for enforcement.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.0.
"""

        with open(self.output_dir / 'CODE_OF_CONDUCT.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_contributing(self):
        content = f"""# Contributing Guidelines

Thank you for your interest in contributing to {self.repo_info.get('name', 'this project')}!

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Development Setup

Follow the setup instructions in the main README.md file.

## Code Style

- Follow the existing code style in the project
- Use meaningful variable and function names
- Add comments for complex logic
- Write tests for new functionality

## Pull Request Process

1. Ensure your code follows the project's coding standards
2. Update documentation if needed
3. Add tests for new functionality
4. Ensure all tests pass
5. Request review from maintainers

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.
"""

        with open(self.output_dir / 'CONTRIBUTING.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_index(self):
        content = """# Repository Documentation Index

Welcome to the auto-generated documentation.

## Documentation Files

- [📊 Summary](SUMMARY.md) - Overview and statistics
- [🏗️ Architecture](ARCHITECTURE.md) - Dependency graphs and structure
- [📁 Files](FILES.md) - Detailed file documentation
- [⚛️ Components](COMPONENTS.md) - React/JSX components
- [📦 Dependencies](DEPENDENCIES.md) - External and internal dependencies
- [🛣️ Routes](ROUTES.md) - Application routes and pages
- [🔗 Call Graph](CALL_GRAPH.md) - Function listings and relationships
"""

        with open(self.docs_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(content)

# Main execution function
def main():
    print('=' * 70)
    print('🚀 ENHANCED GITHUB REPOSITORY DOCUMENTATION GENERATOR')
    print('=' * 70)
    print('\nThis tool analyzes GitHub repositories and generates:')
    print('  📊 Comprehensive statistics with LLM insights')
    print('  🏗️ Dependency graphs (Mermaid diagrams)')
    print('  📝 Complete documentation suite')
    print('  ⚛️ Component analysis with complexity scoring')
    print('  🔗 Enhanced call graphs')
    print('  🤖 AI-powered file summaries (with Groq API)')
    print('=' * 70)

    # Get GitHub URL from user
    github_url = input('\n📎 Enter GitHub repository URL: ').strip()

    if not github_url or 'github.com' not in github_url:
        print('❌ Please provide a valid GitHub URL')
        return

    # Get Groq API key (optional)
    groq_key = input('\n🤖 Enter Groq API key (optional, press Enter to skip LLM analysis): ').strip()
    if not groq_key:
        groq_key = None
        print('⚠️ Proceeding without LLM analysis')

    cloner = None

    try:
        # Step 1: Clone repository
        print('\n' + '=' * 70)
        print('📥 STEP 1: CLONING REPOSITORY')
        print('=' * 70)

        cloner = GitHubRepoCloner()
        repo_path = cloner.clone_repo(github_url)

        # Step 2: Enhanced Analysis with LLM
        print('\n' + '=' * 70)
        print('🔍 STEP 2: ENHANCED REPOSITORY ANALYSIS')
        print('=' * 70)

        analyzer = EnhancedRepositoryAnalyzer(repo_path, enable_llm=bool(groq_key), groq_api_key=groq_key)
        results = analyzer.analyze()

        # Step 3: Generate enhanced documentation
        print('\n' + '=' * 70)
        print('📝 STEP 3: GENERATING ENHANCED DOCUMENTATION')
        print('=' * 70)

        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        # Use enhanced documentation generator
        doc_generator = EnhancedDocumentationGenerator(
            results['files'], 
            results['dependencies'], 
            results['call_graph'], 
            cloner.repo_info, 
            str(output_dir)
        )

        doc_generator.generate_all_enhanced()

        # Save enhanced JSON results
        json_output = output_dir / 'enhanced_analysis.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Step 4: Results
        print('\n' + '=' * 70)
        print('✅ ENHANCED DOCUMENTATION GENERATION COMPLETE!')
        print('=' * 70)

        print(f'\n� *J*Enhanced Analysis Summary:**')
        print(f'   • Repository: {cloner.repo_info["name"]}')
        print(f'   • Files analyzed: {results["total_files"]}')
        print(f'   • External dependencies: {results["dependencies"]["total_external"]}')
        print(f'   • Internal dependencies: {results["dependencies"]["total_internal"]}')
        print(f'   • Total functions: {results["call_graph"]["total_functions"]}')
        print(f'   • Async functions: {results["call_graph"]["async_functions"]}')
        print(f'   • LLM analysis: {"✅ Enabled" if results["llm_enabled"] else "❌ Disabled"}')

        # Calculate additional stats
        total_complexity = sum(f.get('complexity_score', 0) for f in results['files'])
        files_with_apis = len([f for f in results['files'] if f.get('api_endpoints')])
        files_with_db = len([f for f in results['files'] if f.get('database_queries')])

        print(f'\n🔍 **Code Quality Metrics:**')
        print(f'   • Total complexity score: {total_complexity}')
        print(f'   • Files with API calls: {files_with_apis}')
        print(f'   • Files with DB queries: {files_with_db}')
        print(f'   • Average complexity per file: {total_complexity / len(results["files"]):.1f}')

        print(f'\n📁 **Results saved to:** {output_dir.absolute()}/')
        print(f'   📄 Enhanced JSON: enhanced_analysis.json')
        print(f'   📚 Documentation: docs/')
        print(f'   📋 Additional: README.md, API_DOCUMENTATION.md, etc.')

        if results["llm_enabled"]:
            llm_summaries = len([f for f in results['files'] if f.get('llm_summary')])
            print(f'\n🤖 **LLM Analysis Results:**')
            print(f'   • Files with AI summaries: {llm_summaries}')
            print(f'   • Success rate: {llm_summaries / len(results["files"]) * 100:.1f}%')

        print('\n' + '=' * 70)
        print('📊 Top 5 External Dependencies:')
        print('=' * 70)
        sorted_deps = sorted(results['dependencies']['external_deps'].items(),
                            key=lambda x: len(x[1]), reverse=True)[:5]
        for dep, files in sorted_deps:
            print(f'  • {dep}: used in {len(files)} files')

        print('\n✨ Open output/README.md to start exploring the enhanced documentation!')

    except Exception as e:
        print(f'\n❌ **Error:** {e}')
        print('\nPlease check the GitHub URL and API key, then try again.')
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if cloner:
            cloner.cleanup()

# Run the main function only if script is executed directly
if __name__ == "__main__":
    main()