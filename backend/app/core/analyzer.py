"""Core analysis engine for GitHub repositories."""

import os
import time
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from git import Repo
from concurrent.futures import ThreadPoolExecutor

from .extractor import CodeExtractor
from .llm_processor import LLMProcessor
from ..models import AnalysisResult, FileSummary


class GitHubAnalyzer:
    """Main analyzer for GitHub repositories."""
    
    def __init__(self):
        self.temp_dir = None
        self.extractor = CodeExtractor()
    
    async def analyze_repository(self, repo_url: str, api_keys: List[str]) -> AnalysisResult:
        """Analyze a GitHub repository comprehensively."""
        
        start_time = time.time()
        
        try:
            # Step 1: Clone repository
            repo_path = await self._clone_repository(repo_url)
            
            # Step 2: Scan and analyze files
            analyzed_files = await self._analyze_files(repo_path)
            
            # Step 3: LLM processing for enhanced documentation
            llm_results = {}
            if api_keys and analyzed_files:
                llm_processor = LLMProcessor(api_keys)
                llm_results = await llm_processor.process_files(analyzed_files)
            
            # Step 4: Compile results
            results = self._compile_results(
                repo_url, analyzed_files, llm_results, start_time
            )
            
            return results
            
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def _clone_repository(self, repo_url: str) -> str:
        """Clone the GitHub repository to a temporary directory."""
        
        self.temp_dir = tempfile.mkdtemp(prefix="github_analysis_")
        
        try:
            Repo.clone_from(repo_url, self.temp_dir)
            return self.temp_dir
        except Exception as e:
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    async def _analyze_files(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze all code files in the repository."""
        
        # Scan for code files
        code_files = self._scan_code_files(repo_path)
        
        if not code_files:
            return []
        
        # Analyze files in parallel
        analyzed_files = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for file_path, content, language in code_files:
                future = executor.submit(
                    self.extractor.analyze_file,
                    file_path, content, language
                )
                futures.append(future)
            
            for future in futures:
                try:
                    file_analysis = future.result()
                    if file_analysis:
                        analyzed_files.append(file_analysis)
                except Exception as e:
                    print(f"Error analyzing file: {e}")
        
        return analyzed_files
    
    def _scan_code_files(self, repo_path: str) -> List[tuple]:
        """Scan repository for code files."""
        
        supported_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', 
            '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt'
        }
        
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', 'env', 'build', 
                'dist', 'target', '.git', 'vendor'
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in supported_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Skip very large files
                        if len(content) > 100000:  # 100KB limit
                            continue
                        
                        language = self._detect_language(ext)
                        code_files.append((rel_path, content, language))
                        
                    except Exception as e:
                        print(f"Error reading {rel_path}: {e}")
                        continue
        
        return code_files
    
    def _detect_language(self, ext: str) -> str:
        """Detect programming language from file extension."""
        
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        
        return lang_map.get(ext, 'unknown')
    
    def _compile_results(self, repo_url: str, analyzed_files: List[Dict], 
                        llm_results: Dict, start_time: float) -> AnalysisResult:
        """Compile final analysis results."""
        
        # Extract repository info
        repo_info = self._extract_repo_info(repo_url)
        
        # Calculate statistics
        backend_files = [f for f in analyzed_files if f.get('is_backend', False)]
        total_apis = sum(f.get('api_count', 0) for f in analyzed_files)
        total_functions = sum(f.get('function_count', 0) for f in analyzed_files)
        languages = list(set(f.get('language') for f in analyzed_files if f.get('language')))
        
        return AnalysisResult(
            repository_url=repo_url,
            repository_info=repo_info,
            analysis_time=time.time() - start_time,
            summary=FileSummary(
                total_files=len(analyzed_files),
                backend_files=len(backend_files),
                total_apis=total_apis,
                total_functions=total_functions,
                languages=languages
            ),
            all_files=analyzed_files,
            backend_files=backend_files,
            llm_analysis=llm_results
        )
    
    def _extract_repo_info(self, repo_url: str) -> Dict[str, str]:
        """Extract repository information from URL."""
        
        # Parse GitHub URL
        parts = repo_url.rstrip('/').split('/')
        
        if len(parts) >= 2:
            owner = parts[-2]
            repo_name = parts[-1].replace('.git', '')
        else:
            owner = 'unknown'
            repo_name = 'repository'
        
        return {
            'name': repo_name,
            'owner': owner,
            'url': repo_url,
            'description': f'Analysis of {owner}/{repo_name}'
        }