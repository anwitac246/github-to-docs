"""LLM processing orchestration."""

import asyncio
import aiohttp
from typing import List, Dict, Any
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from analysis_models import DetailedFileAnalysis
from summary_models import LLMSummaryRequest
from rate_limiter import RobustMultiKeyRateLimiter
from groq_client import RobustGroqLLMClient

class GuaranteedLLMProcessor:
    """Guaranteed LLM processing with robust error handling and optimization."""
    
    def __init__(self, api_keys: List[str], max_concurrent: int = 3):
        self.api_keys = api_keys
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize rate limiter and LLM client
        self.rate_limiter = RobustMultiKeyRateLimiter(
            api_keys=api_keys,
            max_tokens_per_minute=3000,
            max_calls_per_second=1.0
        )
        self.llm_client = RobustGroqLLMClient(api_keys, self.rate_limiter)
    
    async def process_files_with_llm_optimized(self, files_data: List[DetailedFileAnalysis], 
                                             file_contents: Dict[str, str]) -> List[DetailedFileAnalysis]:
        """Process files with LLM analysis - optimized for backend files and APIs."""
        if not self.api_keys:
            print("⚠️ No API keys provided, skipping LLM analysis")
            return files_data
        
        print(f"🤖 Starting optimized LLM processing for {len(files_data)} files...")
        
        # Filter files for processing (focus on backend and API files)
        files_to_process = []
        for file_analysis in files_data:
            if self._should_process_file_optimized(file_analysis):
                files_to_process.append(file_analysis)
        
        print(f"📊 Processing {len(files_to_process)} backend/API files out of {len(files_data)} total files")
        
        if not files_to_process:
            print("ℹ️ No backend/API files found for LLM processing")
            return files_data
        
        # Process files with LLM
        async with aiohttp.ClientSession() as session:
            tasks = []
            for file_analysis in files_to_process:
                content = file_contents.get(file_analysis.file, "")
                if content:
                    task = self._process_single_file_optimized(session, file_analysis, content)
                    tasks.append(task)
            
            if tasks:
                processed_files = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update the original files_data with processed results
                processed_dict = {f.file: f for f in processed_files if isinstance(f, DetailedFileAnalysis)}
                
                for i, file_analysis in enumerate(files_data):
                    if file_analysis.file in processed_dict:
                        files_data[i] = processed_dict[file_analysis.file]
        
        print(f"✅ Completed LLM processing for {len(files_to_process)} files")
        return files_data
    
    def _should_process_file_optimized(self, file_analysis: DetailedFileAnalysis) -> bool:
        """Determine if file should be processed with LLM (optimized for backend/API files)."""
        
        # Check if it's a backend service or has APIs
        is_backend = (
            hasattr(file_analysis, 'service_info') and 
            file_analysis.service_info and 
            file_analysis.service_info.type == 'backend'
        )
        
        is_service = any(pattern in file_analysis.file.lower() for pattern in [
            'server', 'api', 'service', 'controller', 'route', 'handler', 'app.py', 'main.py', 'app.js', 'index.js'
        ])
        
        # Check if it has meaningful content
        has_functions = len(file_analysis.functions) > 0
        has_classes = len(file_analysis.classes) > 0
        has_apis = len(file_analysis.api_endpoints) > 0
        
        # Skip if it's just a simple utility or has minimal content
        is_minimal = (
            len(file_analysis.functions) <= 1 and 
            len(file_analysis.classes) == 0 and 
            len(file_analysis.api_endpoints) == 0 and
            file_analysis.lines_of_code < 20
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
    
    async def _process_single_file_optimized(self, session: aiohttp.ClientSession, 
                                           file_analysis: DetailedFileAnalysis, content: str) -> DetailedFileAnalysis:
        """Process a single file with rate limiting - optimized for functions and APIs."""
        async with self.semaphore:
            try:
                # Create optimized content focusing on functions and APIs
                optimized_content = self._extract_function_and_api_content(content, file_analysis)
                
                request = LLMSummaryRequest(
                    file_path=file_analysis.file,
                    content=optimized_content,
                    analysis=file_analysis
                )
                
                response = await self.llm_client.generate_summary_with_guarantee(session, request)
                
                # Update file analysis with LLM results
                file_analysis.llm_summary = response.summary
                file_analysis.key_patterns = response.key_insights
                
                return file_analysis
                
            except Exception as e:
                print(f"❌ Error processing {file_analysis.file}: {e}")
                file_analysis.llm_summary = f"Backend file: {Path(file_analysis.file).name}"
                return file_analysis
    
    def _extract_function_and_api_content(self, content: str, file_analysis: DetailedFileAnalysis) -> str:
        """Extract only function definitions and API-related content to reduce token usage."""
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
        """Extract JavaScript/TypeScript function definitions and API routes."""
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
        """Extract Python function definitions and API routes."""
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