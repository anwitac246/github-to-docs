"""Documentation generation utilities."""

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
        
        # Generate setup guide
        setup_path = self._generate_setup_guide(results)
        generated_files.append(setup_path)
        
        # Generate LLM insights if available
        if results.llm_analysis:
            insights_path = self._generate_llm_insights(results)
            generated_files.append(insights_path)
        
        return generated_files
    
    def _generate_readme(self, results: AnalysisResult) -> str:
        """Generate main README.md file."""
        
        repo_info = results.repository_info
        summary = results.summary
        
        content = f"""# {repo_info['name']}

{repo_info['description']}

## 📊 Project Statistics

- **Total Files**: {summary.total_files}
- **Backend Files**: {summary.backend_files}
- **API Endpoints**: {summary.total_apis}
- **Functions**: {summary.total_functions}
- **Languages**: {', '.join(summary.languages)}
- **Analysis Time**: {results.analysis_time:.2f} seconds

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone {repo_info['url']}
cd {repo_info['name']}
```

2. Install dependencies based on the technology stack:

"""
        
        # Add language-specific setup instructions
        if 'python' in summary.languages:
            content += """
### Python Setup
```bash
pip install -r requirements.txt
python main.py
```
"""
        
        if 'javascript' in summary.languages or 'typescript' in summary.languages:
            content += """
### Node.js Setup
```bash
npm install
npm start
```
"""
        
        if 'java' in summary.languages:
            content += """
### Java Setup
```bash
mvn clean install
mvn spring-boot:run
```
"""
        
        content += """
## 📖 Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [Project Summary](PROJECT_SUMMARY.md)
- [Setup Guide](SETUP_GUIDE.md)
"""
        
        if results.llm_analysis:
            content += "- [AI Insights](LLM_INSIGHTS.md)\n"
        
        content += """
## 🏗️ Architecture Overview

"""
        
        # Add backend files overview
        if results.backend_files:
            content += \"### Backend Components\\n\\n\"
            for file_info in results.backend_files[:5]:  # Show top 5
                content += f\"- **{file_info['file_path']}**: {file_info['file_purpose']}\\n\"
                if file_info['api_count'] > 0:
                    content += f\"  - API Endpoints: {file_info['api_count']}\\n\"
                if file_info['function_count'] > 0:
                    content += f\"  - Functions: {file_info['function_count']}\\n\"
                content += \"\\n\"
        
        content += \"\"\"
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

*Documentation generated automatically by GitHub Documentation Generator*
\"\"\"
        
        file_path = os.path.join(self.output_dir, 'README.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'README.md'
    
    def _generate_api_docs(self, results: AnalysisResult) -> str:
        """Generate API documentation."""
        
        repo_info = results.repository_info
        
        content = f\"\"\"# API Documentation

## Overview

This document provides comprehensive API documentation for {repo_info['name']}.

## API Endpoints Summary

Total API Endpoints: {results.summary.total_apis}

\"\"\"
        
        # Group endpoints by file
        for file_info in results.backend_files:
            if file_info.get('api_endpoints') and len(file_info['api_endpoints']) > 0:
                content += f\"### {file_info['file_path']}\\n\\n\"
                content += f\"**Purpose**: {file_info['file_purpose']}\\n\"
                content += f\"**Language**: {file_info['language']}\\n\\n\"
                
                # List endpoints
                for endpoint in file_info['api_endpoints']:
                    content += f\"#### `{endpoint['method']} {endpoint['path']}`\\n\\n\"
                    content += f\"- **Framework**: {endpoint.get('framework', 'Unknown')}\\n\"
                    content += f\"- **Line**: {endpoint.get('line', 'Unknown')}\\n\\n\"
                
                # Add LLM analysis if available
                if results.llm_analysis and file_info['file_path'] in results.llm_analysis:
                    llm_info = results.llm_analysis[file_info['file_path']]
                    content += f\"**AI Analysis**: {llm_info['description']}\\n\\n\"
                
                content += \"---\\n\\n\"
        
        content += \"\"\"
## Authentication

Please refer to the project documentation for authentication requirements.

## Error Handling

All endpoints return standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Rate Limiting

API rate limits may apply. Please check the project configuration.
\"\"\"
        
        file_path = os.path.join(self.output_dir, 'API_DOCUMENTATION.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'API_DOCUMENTATION.md'
    
    def _generate_project_summary(self, results: AnalysisResult) -> str:
        """Generate project summary."""
        
        repo_info = results.repository_info
        summary = results.summary
        
        content = f\"\"\"# Project Summary

## Overview

{repo_info['name']} is a software project analyzed and documented automatically.

## Technical Statistics

- **Repository**: {repo_info['url']}
- **Total Files Analyzed**: {summary.total_files}
- **Backend Files**: {summary.backend_files}
- **API Endpoints**: {summary.total_apis}
- **Functions**: {summary.total_functions}
- **Programming Languages**: {', '.join(summary.languages)}
- **Analysis Duration**: {results.analysis_time:.2f} seconds

## File Breakdown

### By Language
\"\"\"
        
        # Count files by language
        language_counts = {}
        for file_info in results.all_files:
            lang = file_info.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        for lang, count in sorted(language_counts.items()):
            content += f\"- **{lang.title()}**: {count} files\\n\"
        
        content += \"\\n### By Purpose\\n\\n\"
        
        # Count files by purpose
        purpose_counts = {}
        for file_info in results.all_files:
            purpose = file_info.get('file_purpose', 'Unknown')
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1
        
        for purpose, count in sorted(purpose_counts.items()):
            content += f\"- **{purpose}**: {count} files\\n\"
        
        content += \"\"\"
## Architecture Insights

### Backend Architecture
\"\"\"
        
        if results.backend_files:
            content += f\"The project contains {len(results.backend_files)} backend files with a total of {summary.total_apis} API endpoints.\\n\\n\"
            
            # List key backend files
            content += \"#### Key Backend Files:\\n\\n\"
            for file_info in results.backend_files[:10]:  # Top 10
                content += f\"- **{file_info['file_path']}** ({file_info['language']})\\n\"
                content += f\"  - Purpose: {file_info['file_purpose']}\\n\"
                if file_info['api_count'] > 0:
                    content += f\"  - API Endpoints: {file_info['api_count']}\\n\"
                if file_info['function_count'] > 0:
                    content += f\"  - Functions: {file_info['function_count']}\\n\"
                content += \"\\n\"
        else:
            content += \"No backend files detected in this project.\\n\\n\"
        
        content += \"\"\"
## Dependencies

The project uses various dependencies across different languages. Key dependencies include:
\"\"\"
        
        # Collect all dependencies
        all_deps = set()
        for file_info in results.all_files:
            deps = file_info.get('dependencies', [])
            all_deps.update(deps)
        
        if all_deps:
            for dep in sorted(list(all_deps))[:20]:  # Top 20
                content += f\"- {dep}\\n\"
        else:
            content += \"No external dependencies detected.\\n\"
        
        content += \"\"\"
## Recommendations

Based on the analysis, here are some recommendations:

1. **Documentation**: Ensure all API endpoints are properly documented
2. **Testing**: Add comprehensive tests for critical functions
3. **Security**: Review authentication and authorization mechanisms
4. **Performance**: Monitor API response times and optimize as needed
5. **Maintenance**: Keep dependencies up to date

---

*Analysis completed on {time.strftime('%Y-%m-%d %H:%M:%S')}*
\"\"\"
        
        file_path = os.path.join(self.output_dir, 'PROJECT_SUMMARY.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'PROJECT_SUMMARY.md'
    
    def _generate_setup_guide(self, results: AnalysisResult) -> str:
        """Generate setup guide."""
        
        repo_info = results.repository_info
        summary = results.summary
        
        content = f\"\"\"# Setup Guide

## Prerequisites

Based on the analysis, this project uses the following technologies:
{', '.join(summary.languages)}

### System Requirements

\"\"\"
        
        # Add language-specific requirements
        if 'python' in summary.languages:
            content += \"\"\"
#### Python Requirements
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\\\Scripts\\\\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
\"\"\"
        
        if 'javascript' in summary.languages or 'typescript' in summary.languages:
            content += \"\"\"
#### Node.js Requirements
- Node.js 16.0 or higher
- npm or yarn package manager

```bash
# Install dependencies
npm install
# or
yarn install

# Start development server
npm start
# or
yarn start
```
\"\"\"
        
        if 'java' in summary.languages:
            content += \"\"\"
#### Java Requirements
- Java 11 or higher
- Maven or Gradle build tool

```bash
# Maven
mvn clean install
mvn spring-boot:run

# Gradle
./gradlew build
./gradlew bootRun
```
\"\"\"
        
        content += f\"\"\"
## Installation Steps

### 1. Clone the Repository

```bash
git clone {repo_info['url']}
cd {repo_info['name']}
```

### 2. Environment Configuration

Create a `.env` file in the root directory with necessary environment variables:

```env
# Add your environment variables here
# Example:
# DATABASE_URL=your_database_url
# API_KEY=your_api_key
# PORT=3000
```

### 3. Database Setup (if applicable)

If the project uses a database, set it up according to the project requirements.

### 4. Start the Application

Follow the language-specific instructions above to start the application.

## Verification

After setup, verify the installation by:

1. Checking if the application starts without errors
2. Testing API endpoints (if applicable)
3. Running any available tests

## Troubleshooting

### Common Issues

1. **Dependency conflicts**: Try clearing cache and reinstalling
2. **Port conflicts**: Change the port in configuration
3. **Environment variables**: Ensure all required variables are set
4. **Database connection**: Verify database credentials and connectivity

### Getting Help

- Check the project's issue tracker
- Review the documentation
- Contact the maintainers

---

*For more detailed information, see the [Project Summary](PROJECT_SUMMARY.md)*
\"\"\"
        
        file_path = os.path.join(self.output_dir, 'SETUP_GUIDE.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'SETUP_GUIDE.md'
    
    def _generate_llm_insights(self, results: AnalysisResult) -> str:
        """Generate LLM insights documentation."""
        
        repo_info = results.repository_info
        
        content = f\"\"\"# AI-Generated Insights

## Overview

This document contains AI-generated insights about the codebase in {repo_info['name']}.

## File Analysis

\"\"\"
        
        for file_path, analysis in results.llm_analysis.items():
            content += f\"### {file_path}\\n\\n\"
            content += f\"**Purpose**: {analysis.get('file_purpose', 'Unknown')}\\n\"
            content += f\"**API Endpoints**: {analysis.get('api_count', 0)}\\n\"
            content += f\"**Functions**: {analysis.get('function_count', 0)}\\n\\n\"
            content += f\"**AI Analysis**:\\n{analysis['description']}\\n\\n\"
            content += \"---\\n\\n\"
        
        content += \"\"\"
## Summary

The AI analysis provides insights into the key components and functionality of the codebase. This information can help developers understand the project structure and make informed decisions about modifications and enhancements.

---

*AI analysis generated using advanced language models*
\"\"\"
        
        file_path = os.path.join(self.output_dir, 'LLM_INSIGHTS.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 'LLM_INSIGHTS.md'