"""Enhanced LLM processor with advanced rate limiting and error handling."""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional
from .advanced_rate_limiter import AdvancedRateLimiter

class EnhancedLLMProcessor:
    """Enhanced LLM processor with intelligent rate limiting and error handling."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.rate_limiter = AdvancedRateLimiter(api_keys)
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text (rough approximation)."""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4 + 100  # Add buffer for response
    
    def _create_optimized_prompt(self, file_analysis) -> str:
        """Create an optimized prompt that's more concise but still comprehensive."""
        
        prompt = f"""Analyze this {file_analysis.language} file and create concise documentation:

FILE: {file_analysis.file_path}
PURPOSE: {file_analysis.file_purpose}
STATS: {file_analysis.lines_of_code} lines, {len(file_analysis.functions)} functions, {len(file_analysis.api_endpoints)} APIs

"""
        
        # Add API information (limit to top 3)
        if file_analysis.api_endpoints:
            prompt += "KEY APIs:\n"
            for api in file_analysis.api_endpoints[:3]:
                prompt += f"- {api.method} {api.path}\n"
        
        # Add function information (limit to top 5)
        if file_analysis.functions:
            prompt += "\nKEY FUNCTIONS:\n"
            for func in file_analysis.functions[:5]:
                prompt += f"- {func.name}({', '.join(func.params[:3])})\n"
        
        prompt += """
Create CONCISE documentation with:
1. FILE PURPOSE (2-3 sentences)
2. KEY FEATURES (bullet points)
3. MAIN APIs (if any) with brief descriptions
4. USAGE EXAMPLE (if applicable)
5. DEPENDENCIES (list main ones)

Keep response under 1000 tokens. Focus on practical information."""
        
        return prompt
    
    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM API with retry logic and rate limiting."""
        
        estimated_tokens = self._estimate_tokens(prompt)
        
        for attempt in range(max_retries):
            try:
                # Wait for available API key
                api_key = await self.rate_limiter.wait_if_needed(estimated_tokens)
                
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical documentation expert. Create concise, practical documentation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 1000,  # Reduced for faster processing
                    "temperature": 0.1
                }
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Record success
                        actual_tokens = result.get('usage', {}).get('total_tokens', estimated_tokens)
                        self.rate_limiter.record_success(api_key, actual_tokens)
                        
                        return content
                    
                    elif response.status == 429:
                        # Rate limit error
                        error_text = await response.text()
                        self.rate_limiter.record_error(api_key, 429)
                        
                        # Extract wait time from error message if available
                        try:
                            error_data = json.loads(error_text)
                            error_msg = error_data.get('error', {}).get('message', '')
                            if 'try again in' in error_msg:
                                # Extract wait time and add buffer
                                import re
                                match = re.search(r'try again in ([\d.]+)s', error_msg)
                                if match:
                                    wait_time = float(match.group(1)) + 2
                                    print(f"⏳ Rate limit hit. Waiting {wait_time}s...")
                                    await asyncio.sleep(wait_time)
                                    continue
                        except:
                            pass
                        
                        # Default wait for rate limit
                        await asyncio.sleep(10 + attempt * 5)
                        continue
                    
                    else:
                        # Other HTTP errors
                        error_text = await response.text()
                        self.rate_limiter.record_error(api_key, response.status)
                        
                        if attempt == max_retries - 1:
                            return f"API Error {response.status}: {error_text[:200]}"
                        
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
            
            except asyncio.TimeoutError:
                print(f"⏰ Request timeout (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return "Request timeout - please try again"
                await asyncio.sleep(2 ** attempt)
                continue
            
            except Exception as e:
                print(f"❌ Request error: {str(e)} (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return f"Request failed: {str(e)}"
                await asyncio.sleep(2 ** attempt)
                continue
        
        return "Failed to process after multiple attempts"
    
    async def process_files_batch(self, files_data: List, batch_size: int = 5) -> Dict[str, Any]:
        """Process files in batches to avoid overwhelming the API."""
        
        if not self.api_keys:
            return {"error": "No API keys provided"}
        
        print(f"🤖 Processing {len(files_data)} files with enhanced LLM analysis...")
        print(f"📊 Rate limiter status: {len(self.api_keys)} API keys available")
        
        results = {}
        processed_count = 0
        
        # Process files in batches
        for i in range(0, len(files_data), batch_size):
            batch = files_data[i:i + batch_size]
            batch_tasks = []
            
            print(f"📦 Processing batch {i//batch_size + 1}/{(len(files_data) + batch_size - 1)//batch_size}")
            
            # Create tasks for this batch
            for file_analysis in batch:
                if hasattr(file_analysis, 'functions') and hasattr(file_analysis, 'api_endpoints'):
                    if file_analysis.functions or file_analysis.api_endpoints:
                        prompt = self._create_optimized_prompt(file_analysis)
                        task = self._call_llm_with_retry(prompt)
                        batch_tasks.append((file_analysis.file_path, task))
            
            # Execute batch concurrently
            if batch_tasks:
                batch_results = await asyncio.gather(*[task for _, task in batch_tasks], return_exceptions=True)
                
                # Process results
                for (file_path, _), result in zip(batch_tasks, batch_results):
                    if isinstance(result, Exception):
                        print(f"❌ Error processing {file_path}: {result}")
                        results[file_path] = {"error": str(result)}
                    else:
                        print(f"✅ Processed {file_path}")
                        results[file_path] = {
                            "comprehensive_documentation": result,
                            "file_analysis": {
                                "purpose": getattr(file_analysis, 'file_purpose', 'Unknown'),
                                "language": getattr(file_analysis, 'language', 'Unknown'),
                                "lines_of_code": getattr(file_analysis, 'lines_of_code', 0),
                                "function_count": len(getattr(file_analysis, 'functions', [])),
                                "api_count": len(getattr(file_analysis, 'api_endpoints', [])),
                            }
                        }
                    
                    processed_count += 1
            
            # Show progress and rate limiter status
            progress = (processed_count / len(files_data)) * 100
            print(f"📈 Progress: {processed_count}/{len(files_data)} ({progress:.1f}%)")
            
            # Brief pause between batches to be respectful to the API
            if i + batch_size < len(files_data):
                await asyncio.sleep(1)
        
        # Final status
        status = self.rate_limiter.get_status()
        print(f"🏁 Processing complete! Rate limiter final status:")
        print(f"   Available keys: {sum(1 for key_info in status['keys'].values() if key_info['available'])}/{status['total_keys']}")
        
        return results
    
    def get_rate_limiter_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        return self.rate_limiter.get_status()