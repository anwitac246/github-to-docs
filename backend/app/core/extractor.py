"""Code extraction and analysis utilities."""

import re
from typing import Dict, Any, List, Optional


class CodeExtractor:
    """Extract code information from files."""
    
    def analyze_file(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """Analyze a single code file."""
        
        try:
            # Basic metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            # Extract functions
            functions = self._extract_functions(content, language)
            
            # Extract API endpoints
            api_endpoints = self._extract_api_endpoints(content, language)
            
            # Determine if backend file
            is_backend = self._is_backend_file(file_path, content)
            
            # Determine file purpose
            file_purpose = self._determine_file_purpose(file_path, content)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(content, language)
            
            return {
                'file_path': file_path,
                'language': language,
                'lines_of_code': lines_of_code,
                'function_count': len(functions),
                'api_count': len(api_endpoints),
                'functions': functions,
                'api_endpoints': api_endpoints,
                'is_backend': is_backend,
                'file_purpose': file_purpose,
                'dependencies': dependencies,
                'content_preview': content[:1000] if len(content) > 1000 else content
            }
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_functions(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract function definitions from code."""
        
        functions = []
        
        if language == 'python':
            # Python function pattern
            pattern = r'^\\s*def\\s+(\\w+)\\s*\\(([^)]*)\\)\\s*(?:->\\s*([^:]+))?:'
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                func_name = match.group(1)
                params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                return_type = match.group(3).strip() if match.group(3) else None
                
                functions.append({
                    'name': func_name,
                    'parameters': params,
                    'return_type': return_type,
                    'line': content[:match.start()].count('\n') + 1
                })
        
        elif language in ['javascript', 'typescript']:
            # JavaScript/TypeScript function patterns
            patterns = [
                r'function\\s+(\\w+)\\s*\\(([^)]*)\\)',
                r'(\\w+)\\s*=\\s*function\\s*\\(([^)]*)\\)',
                r'(\\w+)\\s*=\\s*\\(([^)]*)\\)\\s*=>',
                r'async\\s+function\\s+(\\w+)\\s*\\(([^)]*)\\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    func_name = match.group(1)
                    params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                    
                    functions.append({
                        'name': func_name,
                        'parameters': params,
                        'return_type': None,
                        'line': content[:match.start()].count('\n') + 1
                    })
        
        elif language == 'java':
            # Java method pattern
            pattern = r'(public|private|protected)\\s+(?:static\\s+)?(?:\\w+\\s+)*(\\w+)\\s*\\(([^)]*)\\)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                func_name = match.group(2)
                params = [p.strip() for p in match.group(3).split(',') if p.strip()]
                
                functions.append({
                    'name': func_name,
                    'parameters': params,
                    'return_type': None,
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return functions
    
    def _extract_api_endpoints(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Extract API endpoint definitions."""
        
        endpoints = []
        
        # Flask routes
        flask_pattern = r'@app\\.route\\s*\\(\\s*["\']([^"\']+)["\'](?:[^)]*methods\\s*=\\s*\\[([^\\]]+)\\])?'
        matches = re.finditer(flask_pattern, content, re.IGNORECASE)
        
        for match in matches:
            path = match.group(1)
            methods_str = match.group(2)
            methods = ['GET']
            
            if methods_str:
                methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
            
            for method in methods:
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'framework': 'Flask',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        # FastAPI routes
        fastapi_pattern = r'@(?:app|router)\\.(get|post|put|delete|patch)\\s*\\(\\s*["\']([^"\']+)["\']'
        matches = re.finditer(fastapi_pattern, content, re.IGNORECASE)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            endpoints.append({
                'method': method,
                'path': path,
                'framework': 'FastAPI',
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Express.js routes
        express_pattern = r'(?:app|router)\\.(get|post|put|delete|patch)\\s*\\(\\s*["\']([^"\']+)["\']'
        matches = re.finditer(express_pattern, content, re.IGNORECASE)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            endpoints.append({
                'method': method,
                'path': path,
                'framework': 'Express',
                'line': content[:match.start()].count('\n') + 1
            })
        
        return endpoints
    
    def _is_backend_file(self, file_path: str, content: str) -> bool:
        """Determine if file is backend-related."""
        
        # Check file path indicators
        backend_path_indicators = [
            'api', 'server', 'backend', 'service', 'controller', 
            'route', 'model', 'handler', 'middleware'
        ]
        
        path_lower = file_path.lower()
        if any(indicator in path_lower for indicator in backend_path_indicators):
            return True
        
        # Check content indicators
        backend_content_indicators = [
            'fastapi', 'flask', 'express', 'django', 'spring',
            '@app.route', 'app.get', 'app.post', 'router.',
            'RestController', 'RequestMapping', 'GetMapping'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in backend_content_indicators)
    
    def _determine_file_purpose(self, file_path: str, content: str) -> str:
        """Determine the main purpose of the file."""
        
        path_lower = file_path.lower()
        
        # Check path patterns
        if 'test' in path_lower or 'spec' in path_lower:
            return 'Testing'
        elif 'config' in path_lower or 'setting' in path_lower:
            return 'Configuration'
        elif 'model' in path_lower or 'schema' in path_lower:
            return 'Data Model'
        elif 'service' in path_lower:
            return 'Business Logic'
        elif 'controller' in path_lower or 'route' in path_lower or 'handler' in path_lower:
            return 'API Controller'
        elif 'component' in path_lower:
            return 'UI Component'
        elif 'page' in path_lower:
            return 'Page Component'
        elif 'util' in path_lower or 'helper' in path_lower:
            return 'Utilities'
        elif 'middleware' in path_lower:
            return 'Middleware'
        
        # Check content patterns
        content_lower = content.lower()
        if 'class.*test' in content_lower or 'def test_' in content_lower:
            return 'Testing'
        elif '@app.route' in content_lower or 'app.get' in content_lower:
            return 'API Routes'
        elif 'class.*model' in content_lower or 'basemodel' in content_lower:
            return 'Data Model'
        
        return 'General Purpose'
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract dependencies from file content."""
        
        dependencies = []
        
        if language == 'python':
            # Python imports
            import_patterns = [
                r'^from\\s+(\\w+)',
                r'^import\\s+(\\w+)'
            ]
            
            for pattern in import_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    dep = match.group(1)
                    if dep not in ['os', 'sys', 'json', 're', 'time', 'datetime']:
                        dependencies.append(dep)
        
        elif language in ['javascript', 'typescript']:
            # JavaScript/TypeScript imports
            patterns = [
                r'import.*from\\s+["\']([^"\']+)["\']',
                r'require\\s*\\(\\s*["\']([^"\']+)["\']\\)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    dep = match.group(1)
                    if not dep.startswith('.') and not dep.startswith('/'):
                        dependencies.append(dep.split('/')[0])
        
        elif language == 'java':
            # Java imports
            pattern = r'^import\\s+([\\w.]+);'
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                dep = match.group(1)
                if not dep.startswith('java.'):
                    dependencies.append(dep.split('.')[0])
        
        return list(set(dependencies))  # Remove duplicates