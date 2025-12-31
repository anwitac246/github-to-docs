"""Configuration settings for the documentation generator."""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # API Keys
    GROQ_API_KEYS: List[str] = []
    
    # Directories
    RESULTS_DIR = "results"
    TEMP_DIR = "temp"
    
    # Analysis settings
    MAX_FILE_SIZE = 100000  # 100KB
    SUPPORTED_EXTENSIONS = {
        '.js': 'javascript',
        '.mjs': 'javascript', 
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.py': 'python'
    }
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_HOUR = 1000
    
    @classmethod
    def load_config(cls):
        """Load configuration from environment variables."""
        # Load Groq API keys
        groq_keys = os.getenv('GROQ_API_KEYS', '')
        if groq_keys:
            cls.GROQ_API_KEYS = [key.strip() for key in groq_keys.split(',') if key.strip()]
        
        # Override directories if specified
        cls.RESULTS_DIR = os.getenv('RESULTS_DIR', cls.RESULTS_DIR)
        cls.TEMP_DIR = os.getenv('TEMP_DIR', cls.TEMP_DIR)
        
        # Create directories if they don't exist
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        
        return cls

# Load configuration on import
Config.load_config()