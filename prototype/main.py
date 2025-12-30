"""Main orchestration script for GitHub documentation analyzer."""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Install required packages
from config import REQUIRED_PACKAGES

print('📦 Installing packages...')
for pkg in REQUIRED_PACKAGES:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], capture_output=True)

# Now import the modules
import sys
import os

# Add current directory and subdirectories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'utils'))
sys.path.insert(0, os.path.join(current_dir, 'parsers'))
sys.path.insert(0, os.path.join(current_dir, 'analyzers'))
sys.path.insert(0, os.path.join(current_dir, 'llm'))
sys.path.insert(0, os.path.join(current_dir, 'models'))

from git_utils import GitHubRepoCloner
from helpers import parse_api_keys, estimate_processing_time
from code_analyzer import DetailedCodeAnalyzer
from folder_analyzer import FolderAnalyzer
from graph_builder import KnowledgeGraphBuilder
from hierarchical_analyzer import HierarchicalAnalyzer
from processor import GuaranteedLLMProcessor
from analysis_models import DetailedFileAnalysis
from config import should_skip_directory, get_file_language

print('✅ Setup complete!')

class GitHubDocsAnalyzer:
    """Main analyzer orchestrating the entire documentation generation process."""
    
    def __init__(self):
        self.repo_cloner = GitHubRepoCloner()
        self.code_analyzer = DetailedCodeAnalyzer()
        self.folder_analyzer = None
        self.graph_builder = KnowledgeGraphBuilder()
        self.hierarchical_analyzer = None
        self.llm_processor = None
    
    async def analyze_repository(self, repo_url: str, api_keys: List[str] = None) -> Dict[str, Any]:
        """Analyze a GitHub repository and generate comprehensive documentation."""
        
        try:
            # Step 1: Clone repository
            repo_path = self.repo_cloner.clone_repo(repo_url)
            
            # Step 2: Scan and analyze files
            print("🔍 Scanning repository files...")
            files_data, file_contents = self._scan_repository(repo_path)
            
            if not files_data:
                print("❌ No analyzable files found in repository")
                return {"error": "No analyzable files found"}
            
            print(f"📊 Found {len(files_data)} files to analyze")
            
            # Step 3: Initialize LLM processor if API keys provided
            if api_keys:
                self.llm_processor = GuaranteedLLMProcessor(api_keys, max_concurrent=3)
                self.folder_analyzer = FolderAnalyzer(self.llm_processor)
                self.hierarchical_analyzer = HierarchicalAnalyzer(self.llm_processor)
                
                # Estimate processing time
                processing_time = estimate_processing_time(len(files_data), len(api_keys))
                print(f"⏱️ Estimated LLM processing time: {processing_time}")
                
                # Step 4: Process files with LLM
                files_data = await self.llm_processor.process_files_with_llm_optimized(files_data, file_contents)
            else:
                print("ℹ️ No API keys provided, skipping LLM analysis")
                self.folder_analyzer = FolderAnalyzer()
                self.hierarchical_analyzer = HierarchicalAnalyzer()
            
            # Step 5: Folder-level analysis
            print("📁 Analyzing folders...")
            folder_summaries = self.folder_analyzer.analyze_folders(files_data)
            
            # Step 6: Build knowledge graph
            print("🔗 Building knowledge graph...")
            knowledge_graph = self.graph_builder.build_graph(files_data)
            
            # Step 7: Hierarchical analysis
            print("🏗️ Performing hierarchical analysis...")
            hierarchical_results = await self.hierarchical_analyzer.perform_hierarchical_analysis(
                files_data, folder_summaries
            )
            
            # Step 8: Compile final results
            results = {
                "repository_info": self.repo_cloner.repo_info,
                "files_analyzed": len(files_data),
                "files_data": [file.__dict__ for file in files_data],
                "folder_summaries": {k: v.__dict__ for k, v in folder_summaries.items()},
                "knowledge_graph": knowledge_graph.__dict__,
                "hierarchical_analysis": hierarchical_results,
                "processing_stats": {
                    "total_files": len(files_data),
                    "folders_analyzed": len(folder_summaries),
                    "llm_processed": len([f for f in files_data if f.llm_summary]),
                    "api_keys_used": len(api_keys) if api_keys else 0
                }
            }
            
            print("✅ Analysis complete!")
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {"error": str(e)}
        
        finally:
            # Cleanup
            self.repo_cloner.cleanup()
    
    def _scan_repository(self, repo_path: str) -> tuple[List[DetailedFileAnalysis], Dict[str, str]]:
        """Scan repository and analyze all relevant files."""
        files_data = []
        file_contents = {}
        
        for root, dirs, files in os.walk(repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Check if file should be analyzed
                if get_file_language(file):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Analyze file
                        file_analysis = self.code_analyzer.analyze_file_detailed(file_path, rel_path, content)
                        
                        if file_analysis:
                            files_data.append(file_analysis)
                            file_contents[rel_path] = content
                            
                    except Exception as e:
                        print(f"⚠️ Error analyzing {rel_path}: {e}")
        
        return files_data, file_contents

async def main():
    """Main entry point for the analyzer."""
    
    # Example usage
    repo_url = input("Enter GitHub repository URL: ").strip()
    
    api_keys_input = input("Enter Groq API keys (comma-separated, optional): ").strip()
    api_keys = parse_api_keys(api_keys_input) if api_keys_input else []
    
    if api_keys:
        print(f"🔑 Using {len(api_keys)} API keys for LLM analysis")
    else:
        print("ℹ️ No API keys provided - basic analysis only")
    
    # Initialize and run analyzer
    analyzer = GitHubDocsAnalyzer()
    results = await analyzer.analyze_repository(repo_url, api_keys)
    
    # Save results
    output_file = "analysis_results.json"
    import json
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📄 Results saved to {output_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    # Print summary
    if "error" not in results:
        stats = results["processing_stats"]
        print(f"\n📊 Analysis Summary:")
        print(f"   Files analyzed: {stats['total_files']}")
        print(f"   Folders analyzed: {stats['folders_analyzed']}")
        print(f"   LLM processed: {stats['llm_processed']}")
        print(f"   Repository: {results['repository_info']['name']}")

if __name__ == "__main__":
    asyncio.run(main())