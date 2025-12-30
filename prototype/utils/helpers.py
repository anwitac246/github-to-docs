"""Helper utility functions."""

import re
from typing import List
import tiktoken

def parse_api_keys(keys_input: str) -> List[str]:
    """Parse API keys from user input, supporting multiple formats."""
    if not keys_input:
        return []
    
    # Split by comma, semicolon, or newline
    keys = re.split(r'[,;\n]+', keys_input)
    
    # Clean and validate keys
    cleaned_keys = []
    for key in keys:
        key = key.strip()
        if key and len(key) > 20:  # Basic validation
            cleaned_keys.append(key)
    
    return cleaned_keys

def dict_to_object(d):
    """Convert dictionary to object with attribute access."""
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
    """Estimate processing time based on files and API keys."""
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

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimation
        return len(text.split()) * 1.3

def convert_to_dict(obj):
    """Convert FileAnalysis and related objects to dictionaries for JSON serialization."""
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
    """Truncate content to fit within token limits."""
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