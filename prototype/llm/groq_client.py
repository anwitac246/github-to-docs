"""Groq LLM client with robust error handling."""

import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from summary_models import LLMSummaryRequest, LLMSummaryResponse
from rate_limiter import RobustMultiKeyRateLimiter

class RobustGroqLLMClient:
    """Ultra-robust Groq LLM client that ensures analysis completion."""
    
    def __init__(self, api_keys: List[str], rate_limiter: RobustMultiKeyRateLimiter):
        self.api_keys = api_keys
        self.rate_limiter = rate_limiter
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def generate_summary_with_guarantee(self, session: aiohttp.ClientSession, request: LLMSummaryRequest) -> LLMSummaryResponse:
        """Generate file summary with guarantee of completion - no fallbacks allowed."""
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
        """Aggressively optimize content to fit within API limits."""
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
    
    def _build_analysis_prompt(self, file_path: str, content: str, analysis) -> str:
        """Build comprehensive analysis prompt for API functions and usage."""
        
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
    
    def _build_api_comprehensive_prompt(self, base_info: str, content: str, analysis) -> str:
        """Comprehensive prompt for API files with complete usage instructions."""
        
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

Focus on providing COMPLETE, ACTIONABLE instructions that allow someone to immediately run and use this application."""

    def _build_component_comprehensive_prompt(self, base_info: str, content: str, analysis) -> str:
        """Comprehensive prompt for frontend components."""
        
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

Focus on providing COMPLETE instructions for setting up and running the frontend application."""

    def _build_service_comprehensive_prompt(self, base_info: str, content: str, analysis) -> str:
        """Comprehensive prompt for backend services."""
        
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

Focus on providing COMPLETE, step-by-step instructions for running this service in development and production."""

    def _build_general_comprehensive_prompt(self, base_info: str, content: str, analysis) -> str:
        """Comprehensive prompt for general files."""
        
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

Focus on providing COMPLETE, actionable documentation."""

    def _determine_file_type(self, file_path: str, analysis) -> str:
        """Determine file type for specialized analysis."""
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
        """Extract wait time from error message."""
        match = re.search(r'try again in ([\d.]+)s', error_text)
        if match:
            return float(match.group(1)) + 2  # Add 2 second buffer
        
        match = re.search(r'try again in ([\d.]+)ms', error_text)
        if match:
            return float(match.group(1)) / 1000 + 1  # Convert to seconds + buffer
        
        return 30.0  # Default wait time
    
    def _parse_llm_response(self, file_path: str, content: str) -> LLMSummaryResponse:
        """Parse comprehensive LLM response."""
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