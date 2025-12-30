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

# Enhanced API endpoint model
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

# Enhanced data models for hierarchical analysis
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
    api_endpoints: List[Dict[str, Any]] = []  # Changed to Dict for flexibility
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
    api_endpoints: List[Dict[str, Any]] = []  # Changed to Dict for flexibility
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

def parse_api_keys(keys_input: str) -> List[str]:
    """Parse API keys from user input, supporting multiple formats"""
    if not keys_input:
        return []
    
    # Split by comma, semicolon, or newline
    import re
    keys = re.split(r'[,;\n]+', keys_input)
    
    # Clean and validate keys
    cleaned_keys = []
    for key in keys:
        key = key.strip()
        if key and len(key) > 20:  # Basic validation
            cleaned_keys.append(key)
    
    return cleaned_keys

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

def estimate_processing_time(num_files: int, num_keys: int) -> str:
    """Estimate processing time based on files and API keys"""
    if num_keys == 0:
        return "No LLM processing"
    
    # Rough estimation: ~30 seconds per file with 1 key, scales with more keys
    base_time = num_files * 30
    parallel_factor = min(num_keys * 2, 8)  # Max 8x speedup
    estimated_seconds = base_time / parallel_factor
    
    if estimated_seconds < 60:
        return f"~{int(estimated_seconds)}s"
    elif estimated_seconds < 3600:
        return f"~{int(estimated_seconds/60)}m {int(estimated_seconds%60)}s"
    else:
        hours = int(estimated_seconds / 3600)
        minutes = int((estimated_seconds % 3600) / 60)
        return f"~{hours}h {minutes}m"

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

class RobustMultiKeyRateLimiter:
    """Ultra-robust rate limiter that ensures LLM analysis completion"""
    def __init__(self, api_keys: List[str], max_tokens_per_minute: int = 3000, max_calls_per_second: float = 1.0):
        self.api_keys = api_keys
        self.max_tokens_per_minute = max_tokens_per_minute
        self.max_calls_per_second = max_calls_per_second
        self.min_call_interval = 1.0 / max_calls_per_second
        
        # Enhanced per-key tracking
        self.key_usage = {}  # {key: [(timestamp, tokens_used), ...]}
        self.key_last_call = {}  # {key: timestamp}
        self.key_failures = {}  # {key: failure_count}
        self.key_cooldown = {}  # {key: cooldown_until_timestamp}
        self.key_health = {}  # {key: health_score (0-100)}
        self.key_success_count = {}  # {key: success_count}
        self.lock = threading.Lock()
        
        # Initialize tracking for each key
        for key in api_keys:
            self.key_usage[key] = []
            self.key_last_call[key] = 0
            self.key_failures[key] = 0
            self.key_cooldown[key] = 0
            self.key_health[key] = 100  # Start with perfect health
            self.key_success_count[key] = 0
    
    def estimate_tokens(self, content: str) -> int:
        """Ultra-conservative token estimation to avoid limits"""
        return len(content) // 2 + 200  # Very conservative estimation
    
    def update_key_health(self, api_key: str, success: bool):
        """Update key health based on success/failure"""
        with self.lock:
            if success:
                self.key_success_count[api_key] += 1
                self.key_health[api_key] = min(100, self.key_health[api_key] + 5)
                # Reduce failure count on success
                self.key_failures[api_key] = max(0, self.key_failures[api_key] - 1)
            else:
                self.key_failures[api_key] += 1
                self.key_health[api_key] = max(0, self.key_health[api_key] - 10)
    
    def mark_key_failed(self, api_key: str, error_type: str = "rate_limit"):
        """Mark a key as failed with adaptive cooldown based on error type"""
        with self.lock:
            self.key_failures[api_key] += 1
            
            # Adaptive cooldown based on failure count and error type
            base_cooldown = 30 if error_type == "rate_limit" else 10
            failure_multiplier = min(self.key_failures[api_key], 5)  # Cap at 5x
            cooldown_seconds = base_cooldown * failure_multiplier
            
            self.key_cooldown[api_key] = time.time() + cooldown_seconds
            self.key_health[api_key] = max(0, self.key_health[api_key] - 15)
            
            print(f"🔴 Key {api_key[-8:]}... cooldown: {cooldown_seconds}s (failure #{self.key_failures[api_key]}, health: {self.key_health[api_key]}%)")
    
    def get_best_available_key(self, estimated_tokens: int) -> tuple[str, float]:
        """Get the healthiest available API key"""
        with self.lock:
            current_time = time.time()
            available_keys = []
            
            # Check each key's availability and health
            for key in self.api_keys:
                # Skip keys in cooldown
                if current_time < self.key_cooldown.get(key, 0):
                    continue
                
                # Clean old usage for this key
                minute_ago = current_time - 60
                self.key_usage[key] = [(ts, tokens) for ts, tokens in self.key_usage[key] if ts > minute_ago]
                
                # Check token limit for this key (more conservative)
                current_tokens = sum(tokens for _, tokens in self.key_usage[key])
                if current_tokens + estimated_tokens > self.max_tokens_per_minute:
                    continue
                
                # Check call rate limit for this key (more conservative)
                time_since_last_call = current_time - self.key_last_call[key]
                if time_since_last_call < self.min_call_interval:
                    continue
                
                # Calculate comprehensive key score (health + usage + failures)
                usage_ratio = current_tokens / self.max_tokens_per_minute
                failure_penalty = self.key_failures[key] * 10
                health_bonus = self.key_health[key]
                
                score = health_bonus - (usage_ratio * 50) - failure_penalty
                available_keys.append((key, score))
            
            if available_keys:
                # Sort by score (higher is better) and return best key
                available_keys.sort(key=lambda x: x[1], reverse=True)
                best_key = available_keys[0][0]
                return best_key, 0
            
            # No key available immediately, calculate minimum wait time
            min_wait = float('inf')
            for key in self.api_keys:
                # Check cooldown wait
                cooldown_wait = max(0, self.key_cooldown.get(key, 0) - current_time)
                
                # Check token limit wait
                if self.key_usage[key]:
                    oldest_time = min(ts for ts, _ in self.key_usage[key])
                    token_wait = max(0, 61 - (current_time - oldest_time))
                else:
                    token_wait = 0
                
                # Check call rate wait
                call_wait = max(0, self.min_call_interval - (current_time - self.key_last_call[key]))
                
                key_wait = max(cooldown_wait, token_wait, call_wait)
                min_wait = min(min_wait, key_wait)
            
            return self.api_keys[0], max(min_wait, 2.0)  # Minimum 2s wait
    
    def record_request(self, api_key: str, tokens_used: int, success: bool = True):
        """Record a request and update key health"""
        with self.lock:
            current_time = time.time()
            self.key_usage[api_key].append((current_time, tokens_used))
            self.key_last_call[api_key] = current_time
            self.update_key_health(api_key, success)
    
    async def wait_for_available_key_async(self, estimated_tokens: int, max_wait_time: int = 300) -> str:
        """Wait for available key with maximum wait time limit"""
        start_time = time.time()
        attempt = 0
        
        while (time.time() - start_time) < max_wait_time:
            key, wait_time = self.get_best_available_key(estimated_tokens)
            if wait_time == 0:
                return key
            
            # Progressive wait time increase
            adaptive_wait = min(wait_time * (1 + attempt * 0.2), 60)  # Max 60s wait
            elapsed = time.time() - start_time
            remaining = max_wait_time - elapsed
            
            if adaptive_wait > remaining:
                print(f"⏰ Timeout approaching, using best available key...")
                # Return the healthiest key even if not optimal
                healthiest_key = max(self.api_keys, key=lambda k: self.key_health.get(k, 0))
                return healthiest_key
            
            print(f"⏳ All keys busy, waiting {adaptive_wait:.1f}s (attempt {attempt + 1}, {remaining:.0f}s remaining)...")
            await asyncio.sleep(adaptive_wait)
            attempt += 1
        
        # Timeout reached, return healthiest key
        healthiest_key = max(self.api_keys, key=lambda k: self.key_health.get(k, 0))
        print(f"⚠️ Max wait time reached, using healthiest key: {healthiest_key[-8:]}...")
        return healthiest_key
    
    def get_key_stats(self) -> Dict[str, Dict]:
        """Get comprehensive statistics for all keys"""
        with self.lock:
            stats = {}
            for key in self.api_keys:
                stats[key[-8:]] = {
                    "health": self.key_health[key],
                    "failures": self.key_failures[key],
                    "successes": self.key_success_count[key],
                    "in_cooldown": time.time() < self.key_cooldown.get(key, 0),
                    "cooldown_remaining": max(0, self.key_cooldown.get(key, 0) - time.time())
                }
            return stats
            self.key_cooldown[api_key] = time.time() + cooldown_seconds
            print(f"🔴 Key {api_key[-8:]}... in cooldown for {cooldown_seconds}s (failure #{self.key_failures[api_key]})")
    
    def get_best_available_key(self, estimated_tokens: int) -> tuple[str, float]:
        """Get the best available API key with enhanced selection logic"""
        with self.lock:
            current_time = time.time()
            available_keys = []
            
            # Check each key's availability
            for key in self.api_keys:
                # Skip keys in cooldown
                if current_time < self.key_cooldown.get(key, 0):
                    continue
                
                # Clean old usage for this key
                minute_ago = current_time - 60
                self.key_usage[key] = [(ts, tokens) for ts, tokens in self.key_usage[key] if ts > minute_ago]
                
                # Check token limit for this key
                current_tokens = sum(tokens for _, tokens in self.key_usage[key])
                if current_tokens + estimated_tokens > self.max_tokens_per_minute:
                    continue
                
                # Check call rate limit for this key
                time_since_last_call = current_time - self.key_last_call[key]
                if time_since_last_call < self.min_call_interval:
                    continue
                
                # Calculate key score (lower failures = better score)
                score = self.key_failures.get(key, 0) + (current_tokens / self.max_tokens_per_minute)
                available_keys.append((key, score))
            
            if available_keys:
                # Sort by score and return best key
                available_keys.sort(key=lambda x: x[1])
                best_key = available_keys[0][0]
                return best_key, 0
            
            # No key available immediately, calculate minimum wait time
            min_wait = float('inf')
            for key in self.api_keys:
                # Check cooldown wait
                cooldown_wait = max(0, self.key_cooldown.get(key, 0) - current_time)
                
                # Check token limit wait
                if self.key_usage[key]:
                    oldest_time = min(ts for ts, _ in self.key_usage[key])
                    token_wait = max(0, 61 - (current_time - oldest_time))
                else:
                    token_wait = 0
                
                # Check call rate wait
                call_wait = max(0, self.min_call_interval - (current_time - self.key_last_call[key]))
                
                key_wait = max(cooldown_wait, token_wait, call_wait)
                min_wait = min(min_wait, key_wait)
            
            return self.api_keys[0], max(min_wait, 1.0)
            if api_key in self.key_failures:
                self.key_failures[api_key] = max(0, self.key_failures[api_key] - 1)

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

class RobustGroqLLMClient:
    """Ultra-robust Groq LLM client that ensures analysis completion"""
    
    def __init__(self, api_keys: List[str], rate_limiter: RobustMultiKeyRateLimiter):
        self.api_keys = api_keys
        self.rate_limiter = rate_limiter
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def generate_summary_with_guarantee(self, session: aiohttp.ClientSession, request: LLMSummaryRequest) -> LLMSummaryResponse:
        """Generate file summary with guarantee of completion - no fallbacks allowed"""
        max_retries = 15  # Increased retries for guarantee
        retry_delays = [1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300, 360]  # Progressive delays
        
        # Prepare highly optimized content for API limits
        content = self._optimize_content_for_api(request.content)
        prompt = self._build_analysis_prompt(request.file_path, content, request.analysis)
        estimated_tokens = self.rate_limiter.estimate_tokens(prompt)
        
        print(f"🎯 Guaranteed processing: {request.file_path} ({estimated_tokens} tokens)")
        
        for attempt in range(max_retries):
            try:
                # Get best available API key with extended wait time
                api_key = await self.rate_limiter.wait_for_available_key_async(estimated_tokens, max_wait_time=600)
                
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert code analyst. Provide detailed, structured analysis of code files with specific focus on API endpoints, functions, and usage instructions."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": 500,  # Conservative for reliability
                    "temperature": 0.1
                }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Extended timeout for reliability
                timeout = aiohttp.ClientTimeout(total=60)
                
                async with session.post(self.base_url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.json()
                        content_response = result['choices'][0]['message']['content']
                        
                        # Record successful request
                        actual_tokens = result.get('usage', {}).get('total_tokens', estimated_tokens)
                        self.rate_limiter.record_request(api_key, actual_tokens, success=True)
                        
                        print(f"✅ Success: {request.file_path} (attempt {attempt + 1})")
                        return self._parse_llm_response(request.file_path, content_response)
                        
                    elif response.status == 429:
                        # Rate limit hit - mark key and try again
                        error_text = await response.text()
                        wait_time = self._extract_wait_time_from_error(error_text)
                        
                        self.rate_limiter.mark_key_failed(api_key, "rate_limit")
                        self.rate_limiter.record_request(api_key, estimated_tokens, success=False)
                        
                        retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                        print(f"⏳ Rate limit hit for {request.file_path}, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        continue
                    
                    elif response.status in [500, 502, 503, 504]:
                        # Server errors - retry with exponential backoff
                        self.rate_limiter.mark_key_failed(api_key, "server_error")
                        retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                        print(f"🔄 Server error {response.status} for {request.file_path}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                        continue
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error for {request.file_path}: {response.status} - {error_text[:200]}")
                        self.rate_limiter.record_request(api_key, estimated_tokens, success=False)
                        
                        if attempt < max_retries - 1:
                            retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                            await asyncio.sleep(retry_delay)
                            continue
                        
            except asyncio.TimeoutError:
                print(f"⏰ Timeout for {request.file_path} (attempt {attempt + 1})")
                retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                await asyncio.sleep(retry_delay)
                
            except Exception as e:
                print(f"❌ Request failed for {request.file_path} (attempt {attempt + 1}): {str(e)[:200]}")
                retry_delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                await asyncio.sleep(retry_delay)
        
        # If we reach here, all retries failed - this should not happen with robust system
        raise Exception(f"CRITICAL: Failed to process {request.file_path} after {max_retries} attempts with robust retry system")
    
    def _optimize_content_for_api(self, content: str) -> str:
        """Aggressively optimize content to fit within API limits"""
        if len(content) <= 4000:
            return content
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Keep more of the beginning (functions/APIs) and less of the end
        keep_start = int(total_lines * 0.8)  # 80% from start
        keep_end = int(total_lines * 0.1)    # 10% from end
        
        optimized = '\n'.join(lines[:keep_start] + ['... [CONTENT OPTIMIZED FOR API ANALYSIS] ...'] + lines[-keep_end:])
        
        # If still too long, take only function definitions and API routes
        if len(optimized) > 4000:
            function_lines = []
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in ['function ', 'def ', 'app.', 'router.', 'export', 'class ', '@']):
                    # Take this line and next 2 lines for context
                    function_lines.extend(lines[i:i+3])
            
            if function_lines:
                optimized = '\n'.join(function_lines[:100])  # Limit to 100 lines
            else:
                optimized = '\n'.join(lines[:50])  # Fallback to first 50 lines
        
        return optimized
    
    def _build_analysis_prompt(self, file_path: str, content: str, analysis: Any) -> str:
        """Build comprehensive analysis prompt for API functions and usage"""
        
        # Determine file type for specialized analysis
        file_type = self._determine_file_type(file_path, analysis)
        
        base_info = f"""FILE: {file_path}
LANGUAGE: {getattr(analysis, 'language', 'unknown')}
FUNCTIONS: {len(getattr(analysis, 'functions', []))}
CLASSES: {len(getattr(analysis, 'classes', []))}
API_ENDPOINTS: {len(getattr(analysis, 'api_endpoints', []))}"""

        if file_type == "api_routes" or getattr(analysis, 'api_endpoints', []):
            return self._build_api_comprehensive_prompt(base_info, content, analysis)
        elif file_type == "frontend_component":
            return self._build_component_comprehensive_prompt(base_info, content, analysis)
        elif file_type == "backend_service":
            return self._build_service_comprehensive_prompt(base_info, content, analysis)
        else:
            return self._build_general_comprehensive_prompt(base_info, content, analysis)
    
    def _build_api_comprehensive_prompt(self, base_info: str, content: str, analysis: Any) -> str:
        """Comprehensive prompt for API files with complete usage instructions"""
        
        api_info = ""
        if hasattr(analysis, 'api_endpoints') and analysis.api_endpoints:
            api_info = f"\nAPI ENDPOINTS DETECTED: {len(analysis.api_endpoints)}"
            for api in analysis.api_endpoints[:5]:
                method = api.get('method', 'GET') if isinstance(api, dict) else getattr(api, 'method', 'GET')
                path = api.get('path', '/') if isinstance(api, dict) else getattr(api, 'path', '/')
                api_info += f"\n- {method} {path}"
        
        return f"""Analyze this API file and provide COMPLETE documentation for running and using the application:

{base_info}{api_info}

CODE:
```
{content}
```

Provide COMPREHENSIVE analysis in this format:

SUMMARY: [Detailed description of what this API file does and its role in the application]

API_ENDPOINTS: [For EACH endpoint, provide:
- Purpose and functionality
- Required parameters with types and descriptions
- Request body format with examples
- Response format with examples
- Authentication requirements
- Error codes and handling]

SETUP_INSTRUCTIONS: [Complete step-by-step instructions to run this API:
- Prerequisites and dependencies
- Environment variables needed
- Database setup if required
- How to start the server
- Port and URL information]

USAGE_EXAMPLES: [Provide complete working examples:
- cURL commands for each endpoint
- JavaScript fetch examples
- Python requests examples
- Postman collection format]

AUTHENTICATION: [Complete authentication setup:
- How to obtain API keys/tokens
- Where to include authentication
- Authentication flow examples]

ERROR_HANDLING: [Complete error documentation:
- All possible error codes
- Error response formats
- How to handle each error type]

INTEGRATION_GUIDE: [How to integrate with frontend:
- Frontend connection examples
- State management integration
- Real-time features if any]

DEPLOYMENT: [Production deployment instructions:
- Environment setup
- Configuration requirements
- Scaling considerations]

Focus on providing COMPLETE, ACTIONABLE instructions that allow someone to immediately run and use this application."""

    def _build_component_comprehensive_prompt(self, base_info: str, content: str, analysis: Any) -> str:
        """Comprehensive prompt for frontend components"""
        
        return f"""Analyze this frontend component and provide COMPLETE usage and setup documentation:

{base_info}

CODE:
```
{content}
```

Provide COMPREHENSIVE analysis:

SUMMARY: [What this component does and its role in the application]

COMPONENT_USAGE: [Complete usage instructions:
- How to import and use this component
- Required props with types and descriptions
- Optional props and their defaults
- Event handlers and callbacks]

SETUP_INSTRUCTIONS: [Complete frontend setup:
- Prerequisites (Node.js version, etc.)
- Installation commands (npm/yarn install)
- Development server startup
- Build process for production]

INTEGRATION_EXAMPLES: [Working code examples:
- How to use this component in other components
- Props passing examples
- State management integration
- API integration examples]

STYLING_SETUP: [Complete styling information:
- CSS framework used
- Custom styles location
- Theme configuration
- Responsive design features]

DEPENDENCIES: [All required dependencies:
- External libraries used
- Installation commands
- Configuration requirements]

DEVELOPMENT_WORKFLOW: [Complete development setup:
- How to run in development mode
- Hot reload setup
- Testing instructions
- Debugging tips]

Focus on providing COMPLETE instructions for setting up and running the frontend application."""

    def _build_service_comprehensive_prompt(self, base_info: str, content: str, analysis: Any) -> str:
        """Comprehensive prompt for backend services"""
        
        return f"""Analyze this backend service and provide COMPLETE setup and usage documentation:

{base_info}

CODE:
```
{content}
```

Provide COMPREHENSIVE analysis:

SUMMARY: [What this service does and its role in the application architecture]

SERVICE_SETUP: [Complete service setup instructions:
- Prerequisites and system requirements
- Installation steps
- Configuration files needed
- Environment variables with descriptions]

DATABASE_SETUP: [Complete database configuration:
- Database type and version
- Schema setup instructions
- Migration commands
- Seed data instructions]

API_DOCUMENTATION: [Complete API documentation:
- All endpoints with full descriptions
- Request/response formats
- Authentication requirements
- Rate limiting information]

DEPLOYMENT_GUIDE: [Production deployment:
- Server requirements
- Deployment steps
- Environment configuration
- Monitoring setup]

INTEGRATION_POINTS: [How this service integrates:
- Frontend integration
- Other service dependencies
- External API integrations
- Message queue setup if any]

TROUBLESHOOTING: [Common issues and solutions:
- Error messages and fixes
- Performance optimization
- Debugging techniques]

Focus on providing COMPLETE, step-by-step instructions for running this service in development and production."""

    def _build_general_comprehensive_prompt(self, base_info: str, content: str, analysis: Any) -> str:
        """Comprehensive prompt for general files"""
        
        return f"""Analyze this code file and provide COMPLETE documentation:

{base_info}

CODE:
```
{content}
```

Provide COMPREHENSIVE analysis:

SUMMARY: [Detailed description of file purpose and functionality]

KEY_FUNCTIONS: [List all important functions with:
- Purpose and functionality
- Parameters and return values
- Usage examples
- Integration points]

SETUP_REQUIREMENTS: [What's needed to use this code:
- Dependencies and installations
- Configuration requirements
- Environment setup]

USAGE_INSTRUCTIONS: [How to use this code:
- Import/require statements
- Initialization steps
- Common usage patterns
- Integration examples]

CONFIGURATION: [All configuration options:
- Environment variables
- Config file settings
- Runtime parameters]

Focus on providing COMPLETE, actionable documentation."""

    def _determine_file_type(self, file_path: str, analysis: Any) -> str:
        """Determine file type for specialized analysis"""
        path_lower = file_path.lower()
        
        if hasattr(analysis, 'api_endpoints') and analysis.api_endpoints:
            return "api_routes"
        elif any(pattern in path_lower for pattern in ['component', 'jsx', 'tsx']):
            return "frontend_component"
        elif any(pattern in path_lower for pattern in ['server', 'service', 'api', 'app.py', 'main.py']):
            return "backend_service"
        else:
            return "general"
    
    def _extract_wait_time_from_error(self, error_text: str) -> float:
        """Extract wait time from error message"""
        import re
        match = re.search(r'try again in ([\d.]+)s', error_text)
        if match:
            return float(match.group(1)) + 2  # Add 2 second buffer
        
        match = re.search(r'try again in ([\d.]+)ms', error_text)
        if match:
            return float(match.group(1)) / 1000 + 1  # Convert to seconds + buffer
        
        return 30.0  # Default wait time
    
    def _parse_llm_response(self, file_path: str, content: str) -> LLMSummaryResponse:
        """Parse comprehensive LLM response"""
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
            elif line.startswith('API_ENDPOINTS:'):
                current_section = 'api_endpoints'
            elif line.startswith('SETUP_INSTRUCTIONS:'):
                current_section = 'setup'
            elif line.startswith('USAGE_EXAMPLES:'):
                current_section = 'usage'
            elif line.startswith('KEY_FUNCTIONS:'):
                current_section = 'functions'
            elif current_section and line:
                if current_section == 'summary':
                    summary += " " + line
                else:
                    key_insights.append(f"[{current_section.upper()}] {line}")
        
        return LLMSummaryResponse(
            file_path=file_path,
            summary=summary or f"Comprehensive analysis of {Path(file_path).name}",
            key_insights=key_insights[:10],  # Limit to prevent overflow
            architectural_role=architectural_role or "Application component",
            complexity_assessment=complexity_assessment or "Standard complexity",
            improvement_suggestions=improvement_suggestions
        )
    """Enhanced Groq LLM client with improved rate limiting and error handling"""
    
    def __init__(self, api_keys: List[str], rate_limiter: RobustMultiKeyRateLimiter):
        self.api_keys = api_keys
        self.rate_limiter = rate_limiter
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def generate_summary(self, session: aiohttp.ClientSession, request: LLMSummaryRequest) -> LLMSummaryResponse:
        """Generate file summary with enhanced error handling and rate limiting"""
        max_retries = 5  # Increased retries
        
        # Prepare optimized content
        content = request.content
        if len(content) > 6000:  # More aggressive truncation
            lines = content.split('\n')
            total_lines = len(lines)
            keep_start = int(total_lines * 0.6)
            keep_end = int(total_lines * 0.2)
            content = '\n'.join(lines[:keep_start] + ['... [TRUNCATED] ...'] + lines[-keep_end:])
        
        prompt = self._build_analysis_prompt(request.file_path, content, request.analysis)
        estimated_tokens = self.rate_limiter.estimate_tokens(prompt)
        
        for attempt in range(max_retries):
            try:
                # Get best available API key
                api_key = await self.rate_limiter.wait_for_available_key_async(estimated_tokens)
                
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert code analyst. Provide concise, structured analysis."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": 600,  # Reduced for faster processing
                    "temperature": 0.1
                }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Add timeout for faster failure detection
                timeout = aiohttp.ClientTimeout(total=30)
                
                async with session.post(self.base_url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        result = await response.json()
                        content_response = result['choices'][0]['message']['content']
                        
                        # Record successful request
                        actual_tokens = result.get('usage', {}).get('total_tokens', estimated_tokens)
                        self.rate_limiter.record_request(api_key, actual_tokens)
                        
                        return self._parse_llm_response(request.file_path, content_response)
                        
                    elif response.status == 429:
                        # Rate limit hit - mark key as failed and try another
                        error_text = await response.text()
                        wait_time = self._extract_wait_time_from_error(error_text)
                        
                        # Mark this key as failed with adaptive cooldown
                        cooldown = min(wait_time + 10, 60)  # 10s buffer, max 60s
                        self.rate_limiter.mark_key_failed(api_key, cooldown)
                        
                        if attempt < max_retries - 1:
                            print(f"⏳ Rate limit hit for {request.file_path}, trying different key...")
                            await asyncio.sleep(1)  # Short delay before retry
                            continue
                        else:
                            print(f"❌ Rate limit exceeded for {request.file_path} after {max_retries} attempts")
                            return self._create_fallback_response(request.file_path)
                    
                    elif response.status in [500, 502, 503, 504]:
                        # Server errors - retry with different key
                        print(f"🔄 Server error {response.status} for {request.file_path}, retrying...")
                        await asyncio.sleep(2 ** min(attempt, 3))  # Exponential backoff, max 8s
                        continue
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error for {request.file_path}: {response.status} - {error_text[:100]}")
                        if attempt == max_retries - 1:
                            return self._create_fallback_response(request.file_path)
                        
            except asyncio.TimeoutError:
                print(f"⏰ Timeout for {request.file_path} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return self._create_fallback_response(request.file_path)
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Request failed for {request.file_path} (attempt {attempt + 1}): {str(e)[:100]}")
                if attempt == max_retries - 1:
                    return self._create_fallback_response(request.file_path)
                await asyncio.sleep(2 ** min(attempt, 3))
        
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
                method = api.get('method') if isinstance(api, dict) else getattr(api, 'method', 'GET')
                path = api.get('path') if isinstance(api, dict) else getattr(api, 'path', '/')
                api_info += f"\n- {method} {path}"
        
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

class KnowledgeGraphBuilder:
    """Builds a comprehensive knowledge graph from code analysis"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = []
        self.edges = []
    
    def build_graph(self, files_data: List[DetailedFileAnalysis]) -> KnowledgeGraph:
        """Build knowledge graph from analyzed files"""
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
        """Add file nodes to the graph"""
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
        """Add function and class nodes"""
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
                
                # Add method nodes
                for method in cls.methods:
                    method_id = f"method:{file_data.file}:{cls.name}:{method}"
                    
                    method_node = GraphNode(
                        id=method_id,
                        type="method",
                        name=method,
                        path=file_data.file,
                        metadata={
                            "class": cls.name,
                            "line": cls.line  # Approximate
                        }
                    )
                    
                    self.nodes.append(method_node)
                    self.graph.add_node(method_id, **method_node.metadata)
                    
                    # Add containment edge (class contains method)
                    self._add_edge(cls_id, method_id, "contains", 1.0)
    
    def _add_dependency_edges(self, files_data: List[DetailedFileAnalysis]):
        """Add import and dependency edges"""
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
        """Add function call relationships (simplified)"""
        # This is a simplified implementation
        # In a full implementation, you'd parse the AST to find actual function calls
        
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
        """Add folder/module containment relationships"""
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
        """Add an edge to the graph"""
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
        """Calculate graph metrics and add to metadata"""
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
        """Categorize file based on its content and purpose"""
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
        """Resolve relative import path to actual file path"""
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
        """Get count of nodes by type"""
        counts = {}
        for node in self.nodes:
            counts[node.type] = counts.get(node.type, 0) + 1
        return counts
    
    def _get_edge_type_counts(self) -> Dict[str, int]:
        """Get count of edges by type"""
        counts = {}
        for edge in self.edges:
            counts[edge.type] = counts.get(edge.type, 0) + 1
        return counts

# Enhanced data models for detailed analysis
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
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "line": line_num,
                    "function_name": function_name,
                    "parameters": parameters,
                    "description": f"{method} endpoint for {path}"
                })
        
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
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "line": line_num,
                    "function_name": function_name,
                    "description": f"FastAPI {method} endpoint for {path}"
                })
        
        # Process Flask patterns
        for pattern in flask_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                path = match.group(1)
                method = match.group(2).upper()
                line_num = content[:match.start()].count('\n') + 1
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "line": line_num,
                    "description": f"Flask {method} endpoint for {path}"
                })
        
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

class GuaranteedLLMProcessor:
    """Guaranteed LLM processor that ensures 100% completion of analysis"""
    
    def __init__(self, api_keys: List[str]):
        # Ultra-conservative settings for guaranteed completion
        self.rate_limiter = RobustMultiKeyRateLimiter(
            api_keys=api_keys,
            max_tokens_per_minute=2500,  # Very conservative per key
            max_calls_per_second=0.8     # Very slow rate per key
        )
        self.llm_client = RobustGroqLLMClient(api_keys, self.rate_limiter)
        self.max_concurrent = 1  # Sequential processing for reliability
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        print(f"🛡️ Guaranteed processor initialized: {len(api_keys)} API keys, sequential processing for 100% success")
    
    async def process_files_with_guarantee(self, file_analyses: List[DetailedFileAnalysis], file_contents: Dict[str, str]) -> List[DetailedFileAnalysis]:
        """Process files with 100% guarantee - no failures allowed"""
        
        # Filter files for LLM processing - focus on API and important files
        files_to_process = []
        skipped_files = []
        
        for file_analysis in file_analyses:
            should_process = self._should_process_with_llm_guaranteed(file_analysis)
            if should_process and file_analysis.file in file_contents:
                files_to_process.append(file_analysis)
            else:
                skipped_files.append(file_analysis)
                # Set basic summary for skipped files
                file_analysis.llm_summary = f"Code file: {Path(file_analysis.file).name}"
        
        print(f"🎯 GUARANTEED LLM PROCESSING")
        print(f"  📁 Processing: {len(files_to_process)} critical files (APIs, services, components)")
        print(f"  ⏭️ Skipping: {len(skipped_files)} non-critical files")
        print(f"🛡️ Guarantee: 100% success rate with robust retry system")
        
        if not files_to_process:
            print("✅ No files require guaranteed LLM processing")
            return file_analyses
        
        # Show key health before starting
        print(f"🔑 API Key Health Status:")
        key_stats = self.rate_limiter.get_key_stats()
        for key_id, stats in key_stats.items():
            print(f"  Key {key_id}: Health {stats['health']}%, Successes: {stats['successes']}, Failures: {stats['failures']}")
        
        async with aiohttp.ClientSession() as session:
            results = []
            successful = 0
            
            print(f"  🔄 Processing {len(files_to_process)} files sequentially for guaranteed success...")
            start_time = time.time()
            
            # Sequential processing for maximum reliability
            for i, file_analysis in enumerate(files_to_process):
                try:
                    print(f"\n📋 Processing {i+1}/{len(files_to_process)}: {file_analysis.file}")
                    
                    result = await self._process_single_file_guaranteed(
                        session, 
                        file_analysis, 
                        file_contents[file_analysis.file]
                    )
                    
                    results.append(result)
                    
                    # Check if LLM analysis was successful
                    if result.llm_summary and result.llm_summary not in ["Code file analysis", f"Backend file: {Path(result.file).name}"]:
                        successful += 1
                        print(f"✅ SUCCESS: {file_analysis.file}")
                    else:
                        print(f"❌ FAILED: {file_analysis.file} - This should not happen with guaranteed processing!")
                    
                    # Progress update
                    elapsed = time.time() - start_time
                    remaining_files = len(files_to_process) - (i + 1)
                    avg_time_per_file = elapsed / (i + 1)
                    estimated_remaining = remaining_files * avg_time_per_file
                    
                    print(f"📊 Progress: {i+1}/{len(files_to_process)} ({successful} successful) - ETA: {estimated_remaining/60:.1f}m")
                    
                    # Show updated key health
                    if (i + 1) % 3 == 0:  # Every 3 files
                        key_stats = self.rate_limiter.get_key_stats()
                        healthy_keys = sum(1 for stats in key_stats.values() if stats['health'] > 50)
                        print(f"🔑 Key Health: {healthy_keys}/{len(key_stats)} keys healthy")
                    
                except Exception as e:
                    print(f"🚨 CRITICAL ERROR: {file_analysis.file} - {str(e)}")
                    # This should not happen with guaranteed processing
                    raise Exception(f"Guaranteed processing failed for {file_analysis.file}: {str(e)}")
        
        # Combine processed and skipped files
        all_results = skipped_files + results
        
        # Final statistics
        total_time = time.time() - start_time
        print(f"\n🎯 GUARANTEED PROCESSING COMPLETE!")
        print(f"✅ Success Rate: {successful}/{len(files_to_process)} ({successful/len(files_to_process)*100:.1f}%)")
        print(f"⏱️ Total Time: {total_time/60:.1f} minutes")
        print(f"📊 Average: {total_time/len(files_to_process):.1f}s per file")
        
        # Final key health report
        print(f"\n🔑 Final API Key Health:")
        key_stats = self.rate_limiter.get_key_stats()
        for key_id, stats in key_stats.items():
            print(f"  Key {key_id}: Health {stats['health']}%, Total Successes: {stats['successes']}")
        
        return all_results
    
    def _should_process_with_llm_guaranteed(self, file_analysis: DetailedFileAnalysis) -> bool:
        """Determine if a file should be processed with guaranteed LLM analysis"""
        
        # Prioritize API files and important backend/frontend files
        is_api_file = len(getattr(file_analysis, 'api_endpoints', [])) > 0
        is_backend = (
            'backend' in file_analysis.file.lower() or
            'server' in file_analysis.file.lower() or
            'api' in file_analysis.file.lower() or
            'route' in file_analysis.file.lower() or
            file_analysis.file.endswith('.py')
        )
        is_main_component = (
            'app.' in file_analysis.file.lower() or
            'main.' in file_analysis.file.lower() or
            'index.' in file_analysis.file.lower()
        )
        has_functions = len(getattr(file_analysis, 'functions', [])) > 0
        
        # Skip config files and simple files
        is_config = (
            file_analysis.file.endswith('.json') or
            'config' in file_analysis.file.lower() or
            'package.json' in file_analysis.file or
            '.config.' in file_analysis.file
        )
        
        # Process if it's important and has content
        should_process = (is_api_file or is_backend or is_main_component) and has_functions and not is_config
        
        return should_process
    
    async def _process_single_file_guaranteed(self, session: aiohttp.ClientSession, file_analysis: DetailedFileAnalysis, content: str) -> DetailedFileAnalysis:
        """Process a single file with guarantee of success"""
        async with self.semaphore:
            try:
                from pathlib import Path
                
                request = LLMSummaryRequest(
                    file_path=file_analysis.file,
                    content=content,
                    analysis=file_analysis
                )
                
                # Use guaranteed generation method
                response = await self.llm_client.generate_summary_with_guarantee(session, request)
                
                # Update file analysis with comprehensive LLM results
                file_analysis.llm_summary = response.summary
                file_analysis.key_patterns = response.key_insights
                
                return file_analysis
                
            except Exception as e:
                print(f"🚨 GUARANTEED PROCESSING FAILED: {file_analysis.file} - {str(e)}")
                # This should not happen - re-raise to indicate system failure
                raise e
    """Enhanced async batch processor with improved rate limiting and error handling"""
    
    def __init__(self, api_keys: List[str], max_concurrent: int = None):
        # Conservative auto-scaling based on number of API keys
        if max_concurrent is None:
            max_concurrent = min(len(api_keys) * 1, 4)  # 1 concurrent per key, max 4
        
        # Enhanced rate limiting with conservative settings
        self.rate_limiter = RobustMultiKeyRateLimiter(
            api_keys=api_keys,
            max_tokens_per_minute=3500,  # More conservative per key limit
            max_calls_per_second=1.2     # Slower rate per key
        )
        self.llm_client = RobustGroqLLMClient(api_keys, self.rate_limiter)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        print(f"🚀 Enhanced processor: {len(api_keys)} API keys, {max_concurrent} max concurrent requests")
    
    async def process_files_batch(self, file_analyses: List[DetailedFileAnalysis], file_contents: Dict[str, str]) -> List[DetailedFileAnalysis]:
        """Process multiple files with LLM analysis - optimized for backend files and functions/APIs only"""
        
        # Filter files for LLM processing - only backend files with functions or APIs
        files_to_process = []
        skipped_files = []
        
        for file_analysis in file_analyses:
            should_process = self._should_process_with_llm(file_analysis)
            if should_process and file_analysis.file in file_contents:
                files_to_process.append(file_analysis)
            else:
                skipped_files.append(file_analysis)
                # Set basic summary for skipped files
                file_analysis.llm_summary = f"Code file: {Path(file_analysis.file).name}"
        
        print(f"🤖 Starting optimized parallel LLM analysis...")
        print(f"  📁 Processing: {len(files_to_process)} backend/API files")
        print(f"  ⏭️ Skipping: {len(skipped_files)} frontend/config files")
        print(f"⚙️ Parallel processing: {self.max_concurrent} concurrent, {len(self.rate_limiter.api_keys)} API keys")
        
        if not files_to_process:
            print("✅ No files require LLM processing")
            return file_analyses
        
        async with aiohttp.ClientSession() as session:
            # Create all tasks at once for maximum parallelism
            tasks = []
            for file_analysis in files_to_process:
                task = self._process_single_file_optimized(
                    session, 
                    file_analysis, 
                    file_contents[file_analysis.file]
                )
                tasks.append(task)
            
            # Process all tasks in parallel with enhanced progress tracking
            results = []
            completed = 0
            successful = 0
            failed = 0
            
            print(f"  🔄 Processing {len(tasks)} files in parallel...")
            start_time = time.time()
            
            # Use asyncio.as_completed for real-time progress updates
            for coro in asyncio.as_completed(tasks):
                try:
                    result = await coro
                    results.append(result)
                    completed += 1
                    
                    # Check if LLM analysis was successful
                    if result.llm_summary and result.llm_summary not in ["Code file analysis", f"Backend file: {Path(result.file).name}"]:
                        successful += 1
                    else:
                        failed += 1
                    
                    # Progress update every 2 files or at completion
                    if completed % 2 == 0 or completed == len(tasks):
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        print(f"  ✅ Progress: {completed}/{len(tasks)} files ({successful} successful, {failed} failed) - {rate:.1f} files/sec")
                        
                except Exception as e:
                    print(f"❌ Task failed: {e}")
                    completed += 1
                    failed += 1
        
        # Combine processed and skipped files
        all_results = skipped_files + results
        successful_summaries = len([r for r in results if r.llm_summary and r.llm_summary != "Code file analysis"])
        print(f"✅ Parallel LLM analysis completed: {successful_summaries}/{len(files_to_process)} backend files with AI summaries")
        return all_results
    
    def _should_process_with_llm(self, file_analysis: DetailedFileAnalysis) -> bool:
        """Determine if a file should be processed with LLM based on optimization criteria"""
        
        # Check if it's a backend file
        is_backend = (
            'backend' in file_analysis.file.lower() or
            'server' in file_analysis.file.lower() or
            'api' in file_analysis.file.lower() or
            'route' in file_analysis.file.lower() or
            'controller' in file_analysis.file.lower() or
            file_analysis.file.endswith('.py')  # Python files are often backend
        )
        
        # Check if it has functions or APIs (meaningful content)
        has_functions = len(file_analysis.functions) > 0
        has_apis = len(file_analysis.api_endpoints) > 0
        has_classes = len(file_analysis.classes) > 0
        
        # Check if it's a service file
        is_service = (
            hasattr(file_analysis, 'service_info') and 
            file_analysis.service_info and 
            file_analysis.service_info.type == 'backend'
        )
        
        # Skip config files, package.json, etc.
        is_config = (
            file_analysis.file.endswith('.json') or
            file_analysis.file.endswith('.config.js') or
            file_analysis.file.endswith('.md') or
            'config' in file_analysis.file.lower() or
            'package.json' in file_analysis.file or
            'vite.config' in file_analysis.file or
            'tailwind.config' in file_analysis.file
        )
        
        # Process if it's backend AND has meaningful content AND not a config file
        should_process = (is_backend or is_service) and (has_functions or has_apis or has_classes) and not is_config
        
        return should_process
    
    async def _process_single_file_optimized(self, session: aiohttp.ClientSession, file_analysis: DetailedFileAnalysis, content: str) -> DetailedFileAnalysis:
        """Process a single file with rate limiting - optimized for functions and APIs"""
        async with self.semaphore:
            try:
                from pathlib import Path
                
                # Create optimized content focusing on functions and APIs
                optimized_content = self._extract_function_and_api_content(content, file_analysis)
                
                request = LLMSummaryRequest(
                    file_path=file_analysis.file,
                    content=optimized_content,
                    analysis=file_analysis
                )
                
                response = await self.llm_client.generate_summary(session, request)
                
                # Update file analysis with LLM results
                file_analysis.llm_summary = response.summary
                file_analysis.key_patterns = response.key_insights
                
                return file_analysis
                
            except Exception as e:
                print(f"❌ Error processing {file_analysis.file}: {e}")
                file_analysis.llm_summary = f"Backend file: {Path(file_analysis.file).name}"
                return file_analysis
    
    def _extract_function_and_api_content(self, content: str, file_analysis: DetailedFileAnalysis) -> str:
        """Extract only function definitions and API-related content to reduce token usage"""
        lines = content.split('\n')
        extracted_lines = []
        
        # Add file header (first 5 lines for context)
        extracted_lines.extend(lines[:5])
        extracted_lines.append("\n// ... [File content optimized for function and API analysis] ...\n")
        
        # Extract function definitions based on language
        if file_analysis.language in ['javascript', 'typescript']:
            extracted_lines.extend(self._extract_js_functions_and_apis(lines, file_analysis))
        elif file_analysis.language == 'python':
            extracted_lines.extend(self._extract_python_functions_and_apis(lines, file_analysis))
        
        # Add API endpoints context
        if file_analysis.api_endpoints:
            extracted_lines.append("\n// API Endpoints detected:")
            for api in file_analysis.api_endpoints[:5]:  # Limit to 5 APIs
                method = api.get('method', 'GET') if isinstance(api, dict) else getattr(api, 'method', 'GET')
                path = api.get('path', '/') if isinstance(api, dict) else getattr(api, 'path', '/')
                extracted_lines.append(f"// {method} {path}")
        
        return '\n'.join(extracted_lines)
    
    def _extract_js_functions_and_apis(self, lines: List[str], file_analysis: DetailedFileAnalysis) -> List[str]:
        """Extract JavaScript/TypeScript function definitions and API routes"""
        extracted = []
        
        for i, line in enumerate(lines):
            # Function definitions
            if any(pattern in line for pattern in ['function ', 'const ', 'let ', '=>', 'app.', 'router.', 'export']):
                # Add function and next few lines for context
                start = max(0, i-1)
                end = min(len(lines), i+5)
                extracted.extend(lines[start:end])
                extracted.append("// ... function body truncated ...")
        
        return extracted
    
    def _extract_python_functions_and_apis(self, lines: List[str], file_analysis: DetailedFileAnalysis) -> List[str]:
        """Extract Python function definitions and API routes"""
        extracted = []
        
        for i, line in enumerate(lines):
            # Function definitions and decorators
            if any(pattern in line for pattern in ['def ', '@app.', '@router.', 'class ', '@']):
                # Add function and next few lines for context
                start = max(0, i-1)
                end = min(len(lines), i+5)
                extracted.extend(lines[start:end])
                extracted.append("# ... function body truncated ...")
        
        return extracted
    
    async def _process_single_file(self, session: aiohttp.ClientSession, file_analysis: DetailedFileAnalysis, content: str) -> DetailedFileAnalysis:
        """Process a single file with rate limiting (original method for compatibility)"""
        async with self.semaphore:
            try:
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
                return file_analysis

class FolderAnalyzer:
    """Analyzes folders and creates structured summaries"""
    
    def __init__(self, llm_processor: GuaranteedLLMProcessor = None):
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

class HierarchicalAnalyzer:
    """Performs hierarchical analysis from folders to global architecture"""
    
    def __init__(self, llm_processor: GuaranteedLLMProcessor = None):
        self.llm_processor = llm_processor
        self.knowledge_graph = None
        self.folder_summaries = {}
        self.module_summaries = {}
        self.domain_summaries = {}
        self.global_summary = None
    
    async def perform_hierarchical_analysis(self, files_data: List[DetailedFileAnalysis], 
                                          folder_summaries: Dict[str, FolderSummary]) -> Dict[str, Any]:
        """Perform complete hierarchical analysis"""
        print("🏗️ Starting hierarchical analysis...")
        
        # Step 6: Build Knowledge Graph
        graph_builder = KnowledgeGraphBuilder()
        self.knowledge_graph = graph_builder.build_graph(files_data)
        
        # Step 7: Enhanced Folder-Level Summarization (already done, enhance with LLM)
        self.folder_summaries = await self._enhance_folder_summaries(folder_summaries)
        
        # Step 8: Module-Level Summarization
        self.module_summaries = await self._create_module_summaries()
        
        # Step 9: Domain-Level Summarization
        self.domain_summaries = await self._create_domain_summaries()
        
        # Step 10: Global Architecture Summary
        self.global_summary = await self._create_global_summary()
        
        return {
            "knowledge_graph": self.knowledge_graph,
            "folder_summaries": self.folder_summaries,
            "module_summaries": self.module_summaries,
            "domain_summaries": self.domain_summaries,
            "global_summary": self.global_summary
        }
    
    async def _enhance_folder_summaries(self, folder_summaries: Dict[str, FolderSummary]) -> Dict[str, FolderSummary]:
        """Step 7: Enhanced folder-level summarization with LLM"""
        print("📁 Enhancing folder summaries with LLM analysis...")
        
        if not self.llm_processor:
            return folder_summaries
        
        enhanced_summaries = {}
        
        for folder_path, folder_summary in folder_summaries.items():
            try:
                # Create enhanced prompt for folder analysis
                prompt = self._build_folder_analysis_prompt(folder_summary)
                
                # For now, create a basic enhanced summary
                # In a full implementation, you'd call the LLM here
                enhanced_summary = folder_summary
                enhanced_summary.llm_summary = f"Enhanced analysis: {folder_summary.folder_purpose} with {folder_summary.total_files} files"
                
                enhanced_summaries[folder_path] = enhanced_summary
                
            except Exception as e:
                print(f"⚠️ Failed to enhance folder summary for {folder_path}: {e}")
                enhanced_summaries[folder_path] = folder_summary
        
        print(f"✅ Enhanced {len(enhanced_summaries)} folder summaries")
        return enhanced_summaries
    
    async def _create_module_summaries(self) -> Dict[str, ModuleSummary]:
        """Step 8: Module-level summarization"""
        print("🔧 Creating module-level summaries...")
        
        modules = self._identify_modules()
        module_summaries = {}
        
        for module_name, module_data in modules.items():
            try:
                module_summary = ModuleSummary(
                    module_name=module_name,
                    module_path=module_data["path"],
                    folders=module_data["folders"],
                    total_files=module_data["total_files"],
                    primary_languages=module_data["languages"],
                    architecture_role=self._determine_module_role(module_name, module_data),
                    interfaces=self._extract_module_interfaces(module_data),
                    responsibilities=self._extract_module_responsibilities(module_data),
                    key_components=module_data["key_components"]
                )
                
                # Generate LLM summary for module
                if self.llm_processor:
                    module_summary.llm_summary = await self._generate_module_llm_summary(module_summary)
                else:
                    module_summary.llm_summary = f"Module {module_name}: {module_summary.architecture_role}"
                
                module_summaries[module_name] = module_summary
                
            except Exception as e:
                print(f"⚠️ Failed to create module summary for {module_name}: {e}")
        
        print(f"✅ Created {len(module_summaries)} module summaries")
        return module_summaries
    
    async def _create_domain_summaries(self) -> Dict[str, DomainSummary]:
        """Step 9: Domain-level summarization"""
        print("🌐 Creating domain-level summaries...")
        
        domains = self._identify_domains()
        domain_summaries = {}
        
        for domain_name, domain_data in domains.items():
            try:
                domain_summary = DomainSummary(
                    domain_name=domain_name,
                    modules=domain_data["modules"],
                    architecture_overview=self._create_domain_architecture_overview(domain_data),
                    data_flow=self._analyze_domain_data_flow(domain_data),
                    business_logic=self._extract_domain_business_logic(domain_data),
                    integration_points=self._identify_domain_integrations(domain_data),
                    key_patterns=self._identify_domain_patterns(domain_data)
                )
                
                # Generate LLM summary for domain
                if self.llm_processor:
                    domain_summary.llm_summary = await self._generate_domain_llm_summary(domain_summary)
                else:
                    domain_summary.llm_summary = f"Domain {domain_name}: {domain_summary.architecture_overview}"
                
                domain_summaries[domain_name] = domain_summary
                
            except Exception as e:
                print(f"⚠️ Failed to create domain summary for {domain_name}: {e}")
        
        print(f"✅ Created {len(domain_summaries)} domain summaries")
        return domain_summaries
    
    async def _create_global_summary(self) -> GlobalArchitectureSummary:
        """Step 10: Global architecture summary"""
        print("🌍 Creating global architecture summary...")
        
        try:
            global_summary = GlobalArchitectureSummary(
                system_overview=self._create_system_overview(),
                key_patterns=self._identify_global_patterns(),
                architectural_decisions=self._extract_architectural_decisions(),
                data_flow_summary=self._create_global_data_flow_summary(),
                scalability_analysis=self._analyze_scalability(),
                security_considerations=self._identify_security_considerations(),
                performance_insights=self._analyze_performance(),
                recommendations=self._generate_recommendations(),
                technology_stack=self._analyze_technology_stack()
            )
            
            # Generate comprehensive LLM summary
            if self.llm_processor:
                global_summary.llm_summary = await self._generate_global_llm_summary(global_summary)
            else:
                global_summary.llm_summary = f"Global architecture: {global_summary.system_overview}"
            
            print("✅ Created global architecture summary")
            return global_summary
            
        except Exception as e:
            print(f"⚠️ Failed to create global summary: {e}")
            return GlobalArchitectureSummary(
                system_overview="Analysis failed",
                llm_summary="Could not generate global architecture summary"
            )
    
    def _identify_modules(self) -> Dict[str, Dict[str, Any]]:
        """Identify logical modules from folder structure"""
        modules = {}
        
        # Group folders into logical modules
        for folder_path, folder_summary in self.folder_summaries.items():
            # Determine module based on folder structure
            path_parts = folder_path.split('/')
            
            if len(path_parts) >= 2:
                module_name = path_parts[0]  # Top-level directory as module
            else:
                module_name = "core"
            
            if module_name not in modules:
                modules[module_name] = {
                    "path": module_name,
                    "folders": [],
                    "total_files": 0,
                    "languages": set(),
                    "key_components": []
                }
            
            modules[module_name]["folders"].append(folder_path)
            modules[module_name]["total_files"] += folder_summary.total_files
            modules[module_name]["languages"].add(folder_summary.primary_language)
            modules[module_name]["key_components"].extend(folder_summary.key_components)
        
        # Convert language sets to lists
        for module_data in modules.values():
            module_data["languages"] = list(module_data["languages"])
        
        return modules
    
    def _identify_domains(self) -> Dict[str, Dict[str, Any]]:
        """Identify business domains from modules"""
        domains = {}
        
        # Simple domain identification based on common patterns
        domain_patterns = {
            "frontend": ["frontend", "ui", "client", "web", "app"],
            "backend": ["backend", "api", "server", "services"],
            "data": ["data", "models", "database", "db"],
            "infrastructure": ["config", "deploy", "docker", "scripts"],
            "shared": ["shared", "common", "utils", "lib"]
        }
        
        for module_name, module_data in self.module_summaries.items():
            domain_assigned = False
            
            for domain_name, patterns in domain_patterns.items():
                if any(pattern in module_name.lower() for pattern in patterns):
                    if domain_name not in domains:
                        domains[domain_name] = {
                            "modules": [],
                            "total_files": 0,
                            "languages": set()
                        }
                    
                    domains[domain_name]["modules"].append(module_name)
                    domains[domain_name]["total_files"] += module_data.total_files
                    domains[domain_name]["languages"].update(module_data.primary_languages)
                    domain_assigned = True
                    break
            
            # If no domain assigned, put in "core"
            if not domain_assigned:
                if "core" not in domains:
                    domains["core"] = {
                        "modules": [],
                        "total_files": 0,
                        "languages": set()
                    }
                domains["core"]["modules"].append(module_name)
                domains["core"]["total_files"] += module_data.total_files
                domains["core"]["languages"].update(module_data.primary_languages)
        
        # Convert language sets to lists
        for domain_data in domains.values():
            domain_data["languages"] = list(domain_data["languages"])
        
        return domains
    
    def _determine_module_role(self, module_name: str, module_data: Dict[str, Any]) -> str:
        """Determine the architectural role of a module"""
        name_lower = module_name.lower()
        
        if any(pattern in name_lower for pattern in ["frontend", "ui", "client"]):
            return "User Interface Layer"
        elif any(pattern in name_lower for pattern in ["backend", "api", "server"]):
            return "Business Logic Layer"
        elif any(pattern in name_lower for pattern in ["data", "model", "db"]):
            return "Data Access Layer"
        elif any(pattern in name_lower for pattern in ["config", "deploy", "script"]):
            return "Infrastructure Layer"
        else:
            return "Core Application Logic"
    
    def _extract_module_interfaces(self, module_data: Dict[str, Any]) -> List[str]:
        """Extract interfaces exposed by the module"""
        interfaces = []
        
        # Look for API endpoints in the knowledge graph
        if self.knowledge_graph:
            for node in self.knowledge_graph.nodes:
                if node.type == "api_endpoint" and any(folder in node.path for folder in module_data["folders"]):
                    interfaces.append(f"{node.metadata.get('method', 'GET')} {node.metadata.get('path', '')}")
        
        return interfaces[:10]  # Limit to top 10
    
    def _extract_module_responsibilities(self, module_data: Dict[str, Any]) -> List[str]:
        """Extract key responsibilities of the module"""
        responsibilities = []
        
        # Analyze based on folder purposes
        for folder_path in module_data["folders"]:
            if folder_path in self.folder_summaries:
                folder_summary = self.folder_summaries[folder_path]
                if folder_summary.folder_purpose:
                    responsibilities.append(folder_summary.folder_purpose)
        
        return list(set(responsibilities))  # Remove duplicates
    
    def _create_system_overview(self) -> str:
        """Create high-level system overview"""
        total_files = sum(len(folder.files) for folder in self.folder_summaries.values())
        total_modules = len(self.module_summaries)
        total_domains = len(self.domain_summaries)
        
        # Identify primary technologies
        languages = set()
        for folder in self.folder_summaries.values():
            languages.add(folder.primary_language)
        
        overview = f"System with {total_files} files organized into {total_modules} modules across {total_domains} domains. "
        overview += f"Primary technologies: {', '.join(sorted(languages))}. "
        
        # Add architecture pattern detection
        if "frontend" in self.domain_summaries and "backend" in self.domain_summaries:
            overview += "Follows client-server architecture pattern."
        
        return overview
    
    def _identify_global_patterns(self) -> List[str]:
        """Identify architectural patterns across the system"""
        patterns = []
        
        # Detect common patterns
        if "frontend" in self.domain_summaries and "backend" in self.domain_summaries:
            patterns.append("Client-Server Architecture")
        
        if any("api" in module.lower() for module in self.module_summaries.keys()):
            patterns.append("RESTful API Design")
        
        if any("component" in folder.folder_purpose.lower() for folder in self.folder_summaries.values() if folder.folder_purpose):
            patterns.append("Component-Based Architecture")
        
        return patterns
    
    def _analyze_technology_stack(self) -> Dict[str, List[str]]:
        """Analyze the technology stack"""
        stack = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": []
        }
        
        # Collect languages
        for folder in self.folder_summaries.values():
            if folder.primary_language not in stack["languages"]:
                stack["languages"].append(folder.primary_language)
        
        # Detect frameworks from dependencies
        if self.knowledge_graph:
            for node in self.knowledge_graph.nodes:
                if node.type == "external_dependency":
                    dep_name = node.name.lower()
                    if any(fw in dep_name for fw in ["react", "vue", "angular"]):
                        if node.name not in stack["frameworks"]:
                            stack["frameworks"].append(node.name)
                    elif any(db in dep_name for db in ["mongo", "postgres", "mysql"]):
                        if node.name not in stack["databases"]:
                            stack["databases"].append(node.name)
        
        return stack
    
    # Placeholder methods for other analysis functions
    def _extract_architectural_decisions(self) -> List[str]:
        return ["Modular architecture", "Separation of concerns", "API-first design"]
    
    def _create_global_data_flow_summary(self) -> str:
        return "Data flows from frontend through API layer to backend services and data storage."
    
    def _analyze_scalability(self) -> str:
        return "System designed with modular architecture supporting horizontal scaling."
    
    def _identify_security_considerations(self) -> List[str]:
        return ["API authentication", "Input validation", "Secure data handling"]
    
    def _analyze_performance(self) -> List[str]:
        return ["Async processing", "Efficient data structures", "Optimized algorithms"]
    
    def _generate_recommendations(self) -> List[str]:
        return ["Add comprehensive testing", "Implement monitoring", "Document APIs"]
    
    def _create_domain_architecture_overview(self, domain_data: Dict[str, Any]) -> str:
        return f"Domain with {len(domain_data['modules'])} modules handling core functionality"
    
    def _analyze_domain_data_flow(self, domain_data: Dict[str, Any]) -> List[str]:
        return ["Input processing", "Business logic execution", "Output generation"]
    
    def _extract_domain_business_logic(self, domain_data: Dict[str, Any]) -> List[str]:
        return ["Core business rules", "Data validation", "Process orchestration"]
    
    def _identify_domain_integrations(self, domain_data: Dict[str, Any]) -> List[str]:
        return ["External APIs", "Database connections", "Service communications"]
    
    def _identify_domain_patterns(self, domain_data: Dict[str, Any]) -> List[str]:
        return ["MVC pattern", "Repository pattern", "Service layer pattern"]
    
    # LLM summary generation methods (placeholders)
    async def _generate_module_llm_summary(self, module_summary: ModuleSummary) -> str:
        return f"Module {module_summary.module_name}: {module_summary.architecture_role} with {module_summary.total_files} files"
    
    async def _generate_domain_llm_summary(self, domain_summary: DomainSummary) -> str:
        return f"Domain {domain_summary.domain_name}: {domain_summary.architecture_overview}"
    
    async def _generate_global_llm_summary(self, global_summary: GlobalArchitectureSummary) -> str:
        return f"Global architecture: {global_summary.system_overview}"
    
    def _build_folder_analysis_prompt(self, folder_summary: FolderSummary) -> str:
        return f"Analyze folder {folder_summary.folder_path} with {folder_summary.total_files} files"

class EnhancedRepositoryAnalyzer:
    def __init__(self, repo_path: str, enable_llm: bool = True, groq_api_keys: List[str] = None):
        self.repo_path = Path(repo_path)
        self.code_analyzer = DetailedCodeAnalyzer()
        self.hierarchical_analyzer = HierarchicalAnalyzer()
        self.files_data = []
        self.file_contents = {}  # Store file contents for LLM processing
        self.enable_llm = enable_llm and groq_api_keys
        
        if self.enable_llm:
            self.llm_processor = GuaranteedLLMProcessor(groq_api_keys)
            self.hierarchical_analyzer.llm_processor = self.llm_processor
        else:
            print("⚠️ LLM analysis disabled (no API keys provided)")

    def _get_all_files(self):
        """Get all files in the repository for estimation"""
        files = []
        for root, dirs, file_list in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            for file in file_list:
                if get_file_language(file):
                    files.append(file)
        return files
    
    def _is_backend_file(self, filename):
        """Check if a file is likely a backend file"""
        return (
            'backend' in filename.lower() or
            'server' in filename.lower() or
            'api' in filename.lower() or
            filename.endswith('.py')
        )

    def analyze(self):
        print(f'📂 Analyzing repository: {self.repo_path}')
        
        # Step 1: Parse all files
        self._walk_repository()
        print(f'✅ Parsed {len(self.files_data)} files')

        # Step 2: Run GUARANTEED LLM analysis if enabled
        if self.enable_llm and self.files_data:
            try:
                print(f"\n🛡️ STARTING GUARANTEED LLM ANALYSIS")
                print(f"🎯 This process will ensure 100% completion of critical file analysis")
                print(f"⏱️ Estimated time: {len([f for f in self.files_data if self._should_process_file(f)]) * 2} minutes")
                
                # Run guaranteed async LLM processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                enhanced_files = loop.run_until_complete(
                    self.llm_processor.process_files_with_guarantee(self.files_data, self.file_contents)
                )
                self.files_data = enhanced_files
                loop.close()
                
                print(f"🎉 GUARANTEED LLM ANALYSIS COMPLETED SUCCESSFULLY!")
                
            except Exception as e:
                print(f"🚨 CRITICAL: Guaranteed LLM processing failed: {e}")
                print(f"🔧 This indicates a system-level issue that needs investigation")
                raise e

        # Step 3: Generate basic analysis
        dependency_data = self._generate_dependencies()
        call_data = self._generate_call_graph()
        
        # Step 4: Perform hierarchical analysis (Steps 6-10)
        hierarchical_results = None
        if self.files_data:
            try:
                # Create folder summaries first
                folder_analyzer = FolderAnalyzer(self.llm_processor if self.enable_llm else None)
                folder_summaries = folder_analyzer.analyze_folders(self.files_data)
                
                # Run hierarchical analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                hierarchical_results = loop.run_until_complete(
                    self.hierarchical_analyzer.perform_hierarchical_analysis(self.files_data, folder_summaries)
                )
                loop.close()
                
            except Exception as e:
                print(f"❌ Hierarchical analysis failed: {e}")
                import traceback
                traceback.print_exc()
        
        return {
            'total_files': len(self.files_data),
            'files': [convert_to_dict(f) for f in self.files_data],  # Convert to dict safely
            'dependencies': dependency_data,
            'call_graph': call_data,
            'llm_enabled': self.enable_llm,
            'hierarchical_analysis': hierarchical_results
        }
    
    def _should_process_file(self, file_data):
        """Check if a file should be processed with LLM"""
        is_api_file = len(getattr(file_data, 'api_endpoints', [])) > 0
        is_backend = (
            'backend' in file_data.file.lower() or
            'server' in file_data.file.lower() or
            'api' in file_data.file.lower() or
            file_data.file.endswith('.py')
        )
        has_functions = len(getattr(file_data, 'functions', [])) > 0
        return (is_api_file or is_backend) and has_functions

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
    
    def __init__(self, files_data, dependencies, call_graph, repo_info, output_dir, hierarchical_analysis=None):
        print(f"🔧 Initializing EnhancedDocumentationGenerator...")
        print(f"  - files_data: {type(files_data)} ({len(files_data) if files_data else 0} items)")
        print(f"  - dependencies: {type(dependencies)}")
        print(f"  - call_graph: {type(call_graph)}")
        print(f"  - repo_info: {type(repo_info)}")
        print(f"  - output_dir: {output_dir}")
        print(f"  - hierarchical_analysis: {type(hierarchical_analysis)}")
        
        self.files_data = files_data
        self.dependencies = dependencies
        self.dependency_data = dependencies  # Also set this for compatibility
        self.call_graph = call_graph
        self.call_data = call_graph  # Also set this for compatibility
        self.repo_info = repo_info
        self.hierarchical_analysis = hierarchical_analysis
        self.output_dir = Path(output_dir)
        self.docs_dir = self.output_dir / 'docs'
        self.summaries_dir = self.output_dir / 'summaries'
        self.hierarchical_dir = self.output_dir / 'hierarchical'
        
        print(f"✅ Set self.dependencies = {self.dependencies}")
        
        # Create directories
        try:
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            self.summaries_dir.mkdir(parents=True, exist_ok=True)
            self.hierarchical_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directories: {self.docs_dir}, {self.summaries_dir}, {self.hierarchical_dir}")
        except Exception as e:
            print(f"⚠️ Failed to create directories: {e}")
            # Ensure attributes exist even if directory creation fails
            if not hasattr(self, 'summaries_dir'):
                self.summaries_dir = self.output_dir / 'summaries'
            if not hasattr(self, 'hierarchical_dir'):
                self.hierarchical_dir = self.output_dir / 'hierarchical'
    
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
        method = api.get('method', 'GET') if isinstance(api, dict) else getattr(api, 'method', 'GET')
        path = api.get('path', '/') if isinstance(api, dict) else getattr(api, 'path', '/')
        
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
                        "method": api.get('method', 'GET') if isinstance(api, dict) else getattr(api, 'method', 'GET'),
                        "path": api.get('path', '/') if isinstance(api, dict) else getattr(api, 'path', '/'),
                        "function_name": api.get('function_name') if isinstance(api, dict) else getattr(api, 'function_name', None),
                        "description": api.get('description', '') if isinstance(api, dict) else getattr(api, 'description', ''),
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

    # Get Groq API keys (support multiple for guaranteed processing)
    print('\n🛡️ GUARANTEED LLM ANALYSIS SETUP')
    print('  🎯 This system ensures 100% completion of API function analysis')
    print('  📋 For best results, provide 2-4 API keys for redundancy')
    print('  ⏱️ Processing time: ~2-3 minutes per API file (guaranteed completion)')
    groq_keys_input = input('\nAPI key(s) (required for guaranteed analysis): ').strip()
    
    groq_keys = []
    if groq_keys_input:
        # Split by comma and clean up
        groq_keys = [key.strip() for key in groq_keys_input.split(',') if key.strip()]
        if len(groq_keys) > 1:
            print(f'🚀 Excellent! Using {len(groq_keys)} API keys for guaranteed redundancy!')
        else:
            print('✅ Using single API key with robust retry system')
    else:
        print('❌ API keys required for guaranteed LLM analysis')
        print('🔧 Without API keys, you will only get basic code analysis (no AI insights)')
        proceed = input('Continue with basic analysis only? (y/N): ').strip().lower()
        if proceed != 'y':
            print('👋 Please run again with API keys for complete analysis')
            return

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

        analyzer = EnhancedRepositoryAnalyzer(repo_path, enable_llm=bool(groq_keys), groq_api_keys=groq_keys)
        
        # Show estimated processing time
        if groq_keys:
            backend_files = len([f for f in analyzer._get_all_files() if analyzer._is_backend_file(f)])
            estimated_time = estimate_processing_time(backend_files, len(groq_keys))
            print(f"⏱️ Estimated LLM processing time: {estimated_time} ({backend_files} backend files)")
        
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
        
        # Convert Pydantic models to dictionaries for JSON serialization
        json_results = results.copy()
        if 'hierarchical_analysis' in json_results and json_results['hierarchical_analysis']:
            hierarchical = json_results['hierarchical_analysis']
            if 'knowledge_graph' in hierarchical:
                # Convert KnowledgeGraph to dict
                kg = hierarchical['knowledge_graph']
                if hasattr(kg, 'model_dump'):
                    hierarchical['knowledge_graph'] = kg.model_dump()
                elif hasattr(kg, '__dict__'):
                    hierarchical['knowledge_graph'] = convert_to_dict(kg)
            
            # Convert other Pydantic models
            for key in ['folder_summaries', 'module_summaries', 'domain_summaries', 'global_summary']:
                if key in hierarchical and hierarchical[key]:
                    if hasattr(hierarchical[key], 'model_dump'):
                        hierarchical[key] = hierarchical[key].model_dump()
                    elif hasattr(hierarchical[key], '__dict__'):
                        hierarchical[key] = convert_to_dict(hierarchical[key])
                    elif isinstance(hierarchical[key], dict):
                        # Convert nested Pydantic models in dictionaries
                        converted_dict = {}
                        for k, v in hierarchical[key].items():
                            if hasattr(v, 'model_dump'):
                                converted_dict[k] = v.model_dump()
                            elif hasattr(v, '__dict__'):
                                converted_dict[k] = convert_to_dict(v)
                            else:
                                converted_dict[k] = v
                        hierarchical[key] = converted_dict
        
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)

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