"""Analysis service for processing repositories and generating documentation."""

import os
import asyncio
import time
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import Config
from ..models import AnalysisStatus, AnalysisResults, ProjectSummary, FileAnalysis

# Import the enhanced documentation generator components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../prototype'))

from enhanced_doc_generator import EnhancedGitHubAnalyzer

class AnalysisService:
    """Service for handling repository analysis and documentation generation."""
    
    def __init__(self):
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.analyzer = EnhancedGitHubAnalyzer()
    
    async def start_github_analysis(self, github_url: str, api_keys: Optional[List[str]] = None) -> str:
        """Start analysis of a GitHub repository."""
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Use provided API keys or fall back to config
        groq_keys = api_keys or Config.GROQ_API_KEYS
        
        if not groq_keys:
            raise ValueError("No Groq API keys available")
        
        # Initialize analysis tracking
        self.active_analyses[analysis_id] = {
            'status': AnalysisStatus.PENDING,
            'progress': 0,
            'message': 'Analysis queued',
            'github_url': github_url,
            'created_at': datetime.now().isoformat(),
            'results': None,
            'error': None
        }
        
        # Start analysis in background
        asyncio.create_task(self._run_analysis(analysis_id, github_url, groq_keys))
        
        return analysis_id
    
    async def _run_analysis(self, analysis_id: str, github_url: str, api_keys: List[str]):
        """Run the actual analysis in the background."""
        
        try:
            # Update status to processing
            self.active_analyses[analysis_id].update({
                'status': AnalysisStatus.PROCESSING,
                'message': 'Starting repository analysis...',
                'progress': 10
            })
            
            # Run the comprehensive analysis
            results = await self.analyzer.analyze_repository_comprehensive(github_url, api_keys)
            
            if "error" in results:
                raise Exception(results["error"])
            
            # Update progress
            self.active_analyses[analysis_id].update({
                'progress': 90,
                'message': 'Finalizing results...'
            })
            
            # Save results to file
            results_file = self._save_results(analysis_id, results)
            
            # Update status to completed
            self.active_analyses[analysis_id].update({
                'status': AnalysisStatus.COMPLETED,
                'progress': 100,
                'message': 'Analysis completed successfully',
                'results': results,
                'results_file': results_file
            })
            
        except Exception as e:
            # Update status to failed
            self.active_analyses[analysis_id].update({
                'status': AnalysisStatus.FAILED,
                'message': f'Analysis failed: {str(e)}',
                'error': str(e)
            })
    
    def _save_results(self, analysis_id: str, results: Dict[str, Any]) -> str:
        """Save analysis results to file."""
        
        results_file = os.path.join(Config.RESULTS_DIR, f"analysis_{analysis_id}.json")
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results_file
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an analysis."""
        return self.active_analyses.get(analysis_id)
    
    def get_analysis_results(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get the complete results of an analysis."""
        
        analysis = self.active_analyses.get(analysis_id)
        if not analysis or analysis['status'] != AnalysisStatus.COMPLETED:
            return None
        
        return analysis.get('results')
    
    def list_analyses(self) -> List[Dict[str, Any]]:
        """List all analyses with their status."""
        
        return [
            {
                'analysis_id': aid,
                'status': data['status'],
                'progress': data.get('progress', 0),
                'message': data['message'],
                'created_at': data['created_at'],
                'github_url': data.get('github_url', ''),
                'has_results': data['status'] == AnalysisStatus.COMPLETED
            }
            for aid, data in self.active_analyses.items()
        ]
    
    def cleanup_old_analyses(self, max_age_hours: int = 24):
        """Clean up old analyses to free memory."""
        
        current_time = datetime.now()
        to_remove = []
        
        for analysis_id, data in self.active_analyses.items():
            created_at = datetime.fromisoformat(data['created_at'])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                to_remove.append(analysis_id)
        
        for analysis_id in to_remove:
            del self.active_analyses[analysis_id]
        
        return len(to_remove)

# Global service instance
analysis_service = AnalysisService()