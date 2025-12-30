"""Git repository utilities."""

import os
import tempfile
import shutil
import requests
from urllib.parse import urlparse
from git import Repo

class GitHubRepoCloner:
    """Handles cloning and managing GitHub repositories."""
    
    def __init__(self):
        self.temp_dir = None
        self.repo_info = {}
    
    def clone_repo(self, repo_url: str) -> str:
        """Clone a GitHub repository to a temporary directory."""
        print(f'📥 Cloning repository: {repo_url}')
        
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        
        owner, repo_name = path_parts[0], path_parts[1]
        
        # Remove .git suffix if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        self.repo_info = {
            'owner': owner,
            'name': repo_name,
            'url': repo_url
        }
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix=f'{repo_name}_')
        
        # Clone repository
        clone_url = f'https://github.com/{owner}/{repo_name}.git'
        Repo.clone_from(clone_url, self.temp_dir)
        print(f'✅ Repository cloned to {self.temp_dir}')

        # Get repo metadata
        try:
            api_url = f'https://api.github.com/repos/{owner}/{repo_name}'
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.repo_info.update({
                    'description': data.get('description', ''),
                    'language': data.get('language', ''),
                    'stars': data.get('stargazers_count', 0),
                    'license': data.get('license', {}).get('name', '') if data.get('license') else ''
                })
        except:
            pass

        return self.temp_dir

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                # On Windows, make files writable before deletion
                if os.name == 'nt':
                    for root, dirs, files in os.walk(self.temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, 0o777)
                            except:
                                pass
                shutil.rmtree(self.temp_dir)
                print(f'🧹 Cleaned up temporary directory')
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up temp directory: {e}")