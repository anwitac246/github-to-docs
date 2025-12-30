"""Rate limiting utilities for LLM API calls."""

import time
import threading
import asyncio
from typing import List, Dict, Tuple

class RobustMultiKeyRateLimiter:
    """Ultra-robust rate limiter that ensures LLM analysis completion."""
    
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
        """Ultra-conservative token estimation to avoid limits."""
        return len(content) // 2 + 200  # Very conservative estimation
    
    def update_key_health(self, api_key: str, success: bool):
        """Update key health based on success/failure."""
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
        """Mark a key as failed with adaptive cooldown based on error type."""
        with self.lock:
            self.key_failures[api_key] += 1
            
            # Adaptive cooldown based on failure count and error type
            base_cooldown = 30 if error_type == "rate_limit" else 10
            failure_multiplier = min(self.key_failures[api_key], 5)  # Cap at 5x
            cooldown_seconds = base_cooldown * failure_multiplier
            
            self.key_cooldown[api_key] = time.time() + cooldown_seconds
            self.key_health[api_key] = max(0, self.key_health[api_key] - 15)
            
            print(f"🔴 Key {api_key[-8:]}... cooldown: {cooldown_seconds}s (failure #{self.key_failures[api_key]}, health: {self.key_health[api_key]}%)")
    
    def get_best_available_key(self, estimated_tokens: int) -> Tuple[str, float]:
        """Get the healthiest available API key."""
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
        """Record a request and update key health."""
        with self.lock:
            current_time = time.time()
            self.key_usage[api_key].append((current_time, tokens_used))
            self.key_last_call[api_key] = current_time
            self.update_key_health(api_key, success)
    
    async def wait_for_available_key_async(self, estimated_tokens: int, max_wait_time: int = 300) -> str:
        """Wait for available key with maximum wait time limit."""
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
        """Get comprehensive statistics for all keys."""
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