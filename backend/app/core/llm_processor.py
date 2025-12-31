"""LLM processing for enhanced documentation generation."""

import asyncio
import httpx
import time
import random
from typing import Dict, Any, List, Optional


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.key_usage = {key: {'requests': 0, 'last_reset': time.time()} for key in api_keys}
        self.max_requests_per_minute = 15  # Conservative limit
    
    def get_available_key(self) -> Optional[str]:
        """Get an available API key."""
        
        now = time.time()
        
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            usage = self.key_usage[key]
            
            # Reset if minute passed
            if now - usage['last_reset'] >= 60:
                usage['requests'] = 0
                usage['last_reset'] = now
            
            # Check if key has capacity
            if usage['requests'] < self.max_requests_per_minute:
                usage['requests'] += 1
                return key
        
        return None
    
    def record_error(self, key: str):
        """Record an error for a key."""
        if key in self.key_usage:
            # Temporarily reduce capacity for this key
            self.key_usage[key]['requests'] += 5


class LLMProcessor:
    """Process files with LLM for enhanced documentation."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.rate_limiter = RateLimiter(api_keys)
    
    async def process_files(self, analyzed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process files with LLM for enhanced documentation."""
        
        if not self.api_keys:
            return {}
        
        # Select important files for LLM processing (limit to avoid rate limits)
        important_files = self._select_important_files(analyzed_files, max_files=5)
        
        print(f"🤖 Processing {len(important_files)} files with LLM...")
        
        results = {}
        
        for file_info in important_files:
            try:
                # Process file with LLM
                analysis = await self._process_single_file(file_info)
                
                if analysis:
                    results[file_info['file_path']] = analysis
                    print(f"✅ LLM analysis completed: {file_info['file_path']}")
                
                # Wait between requests to avoid rate limits
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ LLM processing failed for {file_info['file_path']}: {e}")
                continue
        
        return results
    
    def _select_important_files(self, analyzed_files: List[Dict], max_files: int = 5) -> List[Dict]:
        """Select the most important files for LLM processing."""
        
        scored_files = []
        
        for file_info in analyzed_files:
            score = 0
            
            # API endpoints are very important
            score += file_info.get('api_count', 0) * 10
            
            # Functions are important
            score += file_info.get('function_count', 0) * 2
            
            # Backend files are more important
            if file_info.get('is_backend', False):
                score += 15
            
            # Main files are important
            file_path = file_info['file_path'].lower()
            if any(name in file_path for name in ['main', 'app', 'server', 'index']):
                score += 20
            
            # Controller/service files are important
            if any(name in file_path for name in ['controller', 'service', 'handler', 'route']):
                score += 15
            
            scored_files.append((score, file_info))
        
        # Sort by score and take top files
        scored_files.sort(key=lambda x: x[0], reverse=True)
        return [file_info for _, file_info in scored_files[:max_files]]
    
    async def _process_single_file(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single file with LLM."""
        
        # Get available API key
        api_key = self.rate_limiter.get_available_key()
        
        if not api_key:
            print(f"⏳ No API keys available for {file_info['file_path']}")
            return None
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(file_info)
            
            # Call LLM API
            result = await self._call_llm_api(api_key, prompt)
            
            if result:
                return {
                    'description': result,
                    'timestamp': time.time(),
                    'file_purpose': file_info.get('file_purpose', 'Unknown'),
                    'api_count': file_info.get('api_count', 0),
                    'function_count': file_info.get('function_count', 0)
                }
            
            return None
            
        except Exception as e:
            self.rate_limiter.record_error(api_key)
            raise e
    
    def _create_analysis_prompt(self, file_info: Dict[str, Any]) -> str:
        """Create analysis prompt for LLM."""
        
        content = file_info.get('content_preview', '')[:800]  # Limit content size
        
        prompt = f"""Analyze this {file_info['language']} code file and provide a comprehensive description:

File: {file_info['file_path']}
Purpose: {file_info.get('file_purpose', 'Unknown')}
Functions: {file_info.get('function_count', 0)}
API Endpoints: {file_info.get('api_count', 0)}
Backend File: {file_info.get('is_backend', False)}

Code Preview:
{content}

Please provide:
1. A brief description of what this file does (2-3 sentences)
2. Key functionality and responsibilities
3. How it fits into the overall application architecture

Keep the response concise and focused on the main functionality."""
        
        return prompt
    
    async def _call_llm_api(self, api_key: str, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Call Groq LLM API."""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content'].strip()
                    
                    elif response.status_code == 429:
                        # Rate limit error
                        error_text = response.text
                        print(f"⏳ Rate limit hit: {error_text[:100]}...")
                        
                        if attempt < max_retries - 1:
                            wait_time = 10 + (attempt * 5)
                            await asyncio.sleep(wait_time)
                            continue
                        
                        raise Exception(f"Rate limit error: {response.status_code}")
                    
                    else:
                        error_text = response.text
                        raise Exception(f"API error {response.status_code}: {error_text[:100]}")
            
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    continue
                raise Exception("API request timeout")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    continue
                raise e
        
        return None