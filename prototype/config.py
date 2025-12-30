"""Configuration and constants for GitHub documentation analyzer."""

import os

# Directory patterns to skip during analysis
SKIP_DIRECTORIES = {
    'node_modules', '.git', '__pycache__', 'dist', 'build', 
    '.next', 'coverage', '.pytest_cache', 'venv', 'env', '.venv', 'out'
}

# Language file extensions mapping
LANGUAGE_EXTENSIONS = {
    '.js': 'javascript', 
    '.mjs': 'javascript', 
    '.jsx': 'jsx', 
    '.ts': 'typescript', 
    '.tsx': 'tsx', 
    '.py': 'python'
}

# LLM Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MAX_TOKENS_PER_REQUEST = 4000
MAX_CONCURRENT_REQUESTS = 5
RATE_LIMIT_DELAY = 0.2  # seconds between requests

# Required packages for installation
REQUIRED_PACKAGES = [
    'gitpython', 'tree_sitter', 'tree_sitter_javascript', 'tree_sitter_typescript', 
    'tree_sitter_python', 'requests', 'groq', 'aiohttp', 'asyncio', 'pydantic',
    'tiktoken', 'tenacity', 'networkx'
]

def should_skip_directory(dirname: str) -> bool:
    """Check if directory should be skipped during analysis."""
    return dirname in SKIP_DIRECTORIES or dirname.startswith('.')

def get_file_language(filename: str) -> str:
    """Get programming language from file extension."""
    for ext, lang in LANGUAGE_EXTENSIONS.items():
        if filename.endswith(ext):
            return lang
    return None