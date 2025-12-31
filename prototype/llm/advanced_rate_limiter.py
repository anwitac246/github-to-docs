"""Advanced rate limiter with exponential backoff and multiple API key rotation."""

import asyncio
import time
import random
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class RateLimitInfo:
    """Rate limit information for an API key."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 6000
    current_requests: int = 0
    current_tokens: int = 0
    last_reset: float = 0
    consecutive_errors: int = 0
    last_error_time: float = 0

class AdvancedRateLimiter:
    """Advanced rate limiter with intelligent API key rotation and backoff."""
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.current_key_index = 0
        self.global_backoff_until = 0
        
        # Initialize rate limit info for each key
        for key in api_keys:
            self.rate_limits[key] = RateLimitInfo()
    
    def _reset_limits_if_needed(self, key: str):
        """Reset rate limits if a minute has passed."""
        now = time.time()
        rate_info = self.rate_limits[key]
        
        if now - rate_info.last_reset >= 60:  # 1 minute
            rate_info.current_requests = 0
            rate_info.current_tokens = 0
            rate_info.last_reset = now
            # Reduce consecutive errors over time
            if now - rate_info.last_error_time > 300:  # 5 minutes
                rate_info.consecutive_errors = max(0, rate_info.consecutive_errors - 1)
    
    def _get_best_available_key(self, estimated_tokens: int = 1000) -> str:
        """Get the best available API key based on current usage."""
        now = time.time()
        
        # Check global backoff
        if now < self.global_backoff_until:
            return None
        
        best_key = None
        best_score = float('inf')
        
        for key in self.api_keys:
            self._reset_limits_if_needed(key)
            rate_info = self.rate_limits[key]
            
            # Skip keys with recent errors
            if rate_info.consecutive_errors > 3 and now - rate_info.last_error_time < 60:
                continue
            
            # Check if key can handle the request
            if (rate_info.current_requests >= rate_info.requests_per_minute or
                rate_info.current_tokens + estimated_tokens > rate_info.tokens_per_minute):
                continue
            
            # Calculate score (lower is better)
            usage_score = (rate_info.current_requests / rate_info.requests_per_minute + 
                          rate_info.current_tokens / rate_info.tokens_per_minute)
            error_penalty = rate_info.consecutive_errors * 0.5
            score = usage_score + error_penalty
            
            if score < best_score:
                best_score = score
                best_key = key
        
        return best_key
    
    def _calculate_backoff_delay(self, error_count: int) -> float:
        """Calculate exponential backoff delay."""
        base_delay = 2 ** min(error_count, 6)  # Cap at 64 seconds
        jitter = random.uniform(0.5, 1.5)  # Add jitter
        return base_delay * jitter
    
    async def wait_if_needed(self, estimated_tokens: int = 1000) -> str:
        """Wait if needed and return the best available API key."""
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            key = self._get_best_available_key(estimated_tokens)
            
            if key:
                # Reserve the tokens/requests
                rate_info = self.rate_limits[key]
                rate_info.current_requests += 1
                rate_info.current_tokens += estimated_tokens
                return key
            
            # All keys are rate limited, wait and retry
            retry_count += 1
            wait_time = self._calculate_backoff_delay(retry_count)
            print(f"⏳ All API keys rate limited. Waiting {wait_time:.1f}s (attempt {retry_count}/{max_retries})")
            await asyncio.sleep(wait_time)
        
        raise Exception("All API keys are rate limited. Please try again later.")
    
    def record_success(self, key: str, actual_tokens: int):
        """Record a successful API call."""
        if key in self.rate_limits:
            rate_info = self.rate_limits[key]
            # Adjust token count based on actual usage
            rate_info.current_tokens = rate_info.current_tokens - 1000 + actual_tokens
            # Reset consecutive errors on success
            rate_info.consecutive_errors = 0
    
    def record_error(self, key: str, error_code: int = None):
        """Record an API error."""
        if key in self.rate_limits:
            rate_info = self.rate_limits[key]
            rate_info.consecutive_errors += 1
            rate_info.last_error_time = time.time()
            
            # Handle specific error codes
            if error_code == 429:  # Rate limit error
                # Immediately max out this key's limits
                rate_info.current_requests = rate_info.requests_per_minute
                rate_info.current_tokens = rate_info.tokens_per_minute
                print(f"🚫 API key rate limited: {key[:10]}...")
            elif error_code in [500, 502, 503, 504]:  # Server errors
                # Set global backoff for server issues
                self.global_backoff_until = time.time() + 30
                print(f"🔄 Server error detected. Global backoff for 30s")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        now = time.time()
        status = {
            "total_keys": len(self.api_keys),
            "global_backoff": max(0, self.global_backoff_until - now),
            "keys": {}
        }
        
        for i, key in enumerate(self.api_keys):
            self._reset_limits_if_needed(key)
            rate_info = self.rate_limits[key]
            
            status["keys"][f"key_{i+1}"] = {
                "requests_used": rate_info.current_requests,
                "requests_limit": rate_info.requests_per_minute,
                "tokens_used": rate_info.current_tokens,
                "tokens_limit": rate_info.tokens_per_minute,
                "consecutive_errors": rate_info.consecutive_errors,
                "available": (rate_info.current_requests < rate_info.requests_per_minute and 
                            rate_info.current_tokens < rate_info.tokens_per_minute and
                            rate_info.consecutive_errors < 3)
            }
        
        return status