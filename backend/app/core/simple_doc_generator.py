"""Simple documentation generation utilities."""

import os
import time
from typing import Dict, Any, List
from pathlib import Path

from ..models import AnalysisResult


class DocumentationGenerator:
    """Generate comprehensive documentation from analysis results."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all_docs(self, results: AnalysisResult) -> List[str]:
        """Generate all documentation files."""
        
        generated_files = []
        
        # Generate README
        readme_path = self._generate_readme(results)
        generated_files.append(readme_path)
        
        # Generate API documentation
        api_docs_path = self._generate_api_docs(results)
        generated_files.append(api_docs_path)
        
        # Generate project summary
        summary_path = self._generate_project_summary(results)
        generated_files.append(summary_path)
        
        return generated_files
    
    def _generate_readme(self, results: AnalysisResult) -> str:
        """Generate main README.md file."""
        
        repo_info = results.repository_info
        summary = results.summary
        
        content = f"# {repo_info['name']}\n\n"
        content += f"{repo_info['description']}\n\n"
        content += "## 📊 Project Statistics\n\n"
        content += f"- **Total Files**: {summary.total_files}\n"
        content += f"- **Backend Files**: {summary.backend_files}\n"
        content += f"- **API Endpoints**: {summary.total_apis}\n"
        content += f"- **Functions**: {summary.total_functions}\n"
        content += f"- **Languages**: {', '.join(summary.languages)}\n"
        content += f"- **Analysis Time**: {results.analysis_time:.2f} seconds\n\n"
        
        content += "## 🚀 Quick Start\n\n"
        content += "1. Clone the repository:\n"
        content += "```bash\n"
        content += f"git clone {repo_info['url']}\n"
        content += f"cd {repo_info['name']}\n"
        content += "```\n\n"
        content += "2. Install dependencies based on the technology stack.\n\n"
        
        # Add language-specific setup
        if 'python' in summary.languages:
            content += "### Python Setup\n"
            content += "```bash\n"
            content += "pip install -r requirements.txt\n"
            content += "python main.py\n"
            content += "```\n\n"
        
        if 'javascript' in summary.languages or 'typescript' in summary.languages:
            content += "### Node.js Setup\n"
            content += "```bash\n"
            content += "npm install\n"
            content += "npm start\n"
            content += "```\n\n"
        
        content += "## 📖 Documentation\n\n"
        content += "- [API Documentation](API_DOCUMENTATION.md)\n"
        content += "- [Project Summary](PROJECT_SUMMARY.md)\n\n"
        
        # Add backend files overview
        if results.backend_files:
            content += "## 🏗️ Backend Components\n\n"
            for file_info in results.backend_files[:5]:  # Show top 5
                content += f"- **{file_info['file_path']}**: {file_info['file_purpose']}\n"
                if file_info['api_count'] > 0:
                    content += f"  - API Endpoints: {file_info['api_count']}\n"
                if file_info['function_count'] > 0:
                    content += f"  - Functions: {file_info['function_count']}\n"
        
        content += "\n## 📄 License\n\n"
        content += "This project is licensed under the MIT License.\n\n"
        content += "---\n\n"
        content += "*Documentation generated automatically by GitHub Documentation Generator*\n"
        
        file_path = os.path.join(self.output_dir, 'README.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'README.md'
    
    def _generate_api_docs(self, results: AnalysisResult) -> str:
        """Generate API documentation."""
        
        repo_info = results.repository_info
        
        content = "# API Documentation\n\n"
        content += "## Overview\n\n"
        content += f"This document provides comprehensive API documentation for {repo_info['name']}.\n\n"
        content += f"Total API Endpoints: {results.summary.total_apis}\n\n"
        
        # Group endpoints by file
        for file_info in results.backend_files:
            if file_info.get('api_endpoints') and len(file_info['api_endpoints']) > 0:
                content += f"### {file_info['file_path']}\n\n"
                content += f"**Purpose**: {file_info['file_purpose']}\n"
                content += f"**Language**: {file_info['language']}\n\n"
                
                # List endpoints
                for endpoint in file_info['api_endpoints']:
                    content += f"#### `{endpoint['method']} {endpoint['path']}`\n\n"
                    content += f"- **Framework**: {endpoint.get('framework', 'Unknown')}\n"
                    content += f"- **Line**: {endpoint.get('line', 'Unknown')}\n\n"
                
                # Add AI analysis if available
                if results.llm_analysis and file_info['file_path'] in results.llm_analysis:
                    llm_info = results.llm_analysis[file_info['file_path']]
                    content += f"**AI Analysis**: {llm_info['description']}\n\n"
                
                content += "---\n\n"
        
        content += "## Authentication\n\n"
        content += "Please refer to the project documentation for authentication requirements.\n\n"
        content += "## Error Handling\n\n"
        content += "All endpoints return standard HTTP status codes:\n"
        content += "- 200: Success\n"
        content += "- 400: Bad Request\n"
        content += "- 401: Unauthorized\n"
        content += "- 404: Not Found\n"
        content += "- 500: Internal Server Error\n"
        
        file_path = os.path.join(self.output_dir, 'API_DOCUMENTATION.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'API_DOCUMENTATION.md'
    
    def _generate_project_summary(self, results: AnalysisResult) -> str:
        """Generate project summary."""
        
        repo_info = results.repository_info
        summary = results.summary
        
        content = "# Project Summary\n\n"
        content += "## Overview\n\n"
        content += f"{repo_info['name']} is a software project analyzed and documented automatically.\n\n"
        content += "## Technical Statistics\n\n"
        content += f"- **Repository**: {repo_info['url']}\n"
        content += f"- **Total Files Analyzed**: {summary.total_files}\n"
        content += f"- **Backend Files**: {summary.backend_files}\n"
        content += f"- **API Endpoints**: {summary.total_apis}\n"
        content += f"- **Functions**: {summary.total_functions}\n"
        content += f"- **Programming Languages**: {', '.join(summary.languages)}\n"
        content += f"- **Analysis Duration**: {results.analysis_time:.2f} seconds\n\n"
        
        content += "## File Breakdown\n\n"
        content += "### By Language\n\n"
        
        # Count files by language
        language_counts = {}
        for file_info in results.all_files:
            lang = file_info.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        for lang, count in sorted(language_counts.items()):
            content += f"- **{lang.title()}**: {count} files\n"
        
        content += "\n### By Purpose\n\n"
        
        # Count files by purpose
        purpose_counts = {}
        for file_info in results.all_files:
            purpose = file_info.get('file_purpose', 'Unknown')
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1
        
        for purpose, count in sorted(purpose_counts.items()):
            content += f"- **{purpose}**: {count} files\n"
        
        content += "\n## Architecture Insights\n\n"
        content += "### Backend Architecture\n\n"
        
        if results.backend_files:
            content += f"The project contains {len(results.backend_files)} backend files with a total of {summary.total_apis} API endpoints.\n\n"
            
            # List key backend files
            content += "#### Key Backend Files:\n\n"
            for file_info in results.backend_files[:10]:  # Top 10
                content += f"- **{file_info['file_path']}** ({file_info['language']})\n"
                content += f"  - Purpose: {file_info['file_purpose']}\n"
                if file_info['api_count'] > 0:
                    content += f"  - API Endpoints: {file_info['api_count']}\n"
                if file_info['function_count'] > 0:
                    content += f"  - Functions: {file_info['function_count']}\n"
        else:
            content += "No backend files detected in this project.\n\n"
        
        content += "\n## Recommendations\n\n"
        content += "Based on the analysis, here are some recommendations:\n\n"
        content += "1. **Documentation**: Ensure all API endpoints are properly documented\n"
        content += "2. **Testing**: Add comprehensive tests for critical functions\n"
        content += "3. **Security**: Review authentication and authorization mechanisms\n"
        content += "4. **Performance**: Monitor API response times and optimize as needed\n"
        content += "5. **Maintenance**: Keep dependencies up to date\n\n"
        content += "---\n\n"
        content += f"*Analysis completed on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        file_path = os.path.join(self.output_dir, 'PROJECT_SUMMARY.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'PROJECT_SUMMARY.md'