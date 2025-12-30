"""Hierarchical analysis from folders to global architecture."""

from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'models'))

from analysis_models import DetailedFileAnalysis, FolderSummary
from summary_models import ModuleSummary, DomainSummary, GlobalArchitectureSummary

class HierarchicalAnalyzer:
    """Performs hierarchical analysis from folders to global architecture."""
    
    def __init__(self, llm_processor=None):
        self.llm_processor = llm_processor
        self.knowledge_graph = None
        self.folder_summaries = {}
        self.module_summaries = {}
        self.domain_summaries = {}
        self.global_summary = None
    
    async def perform_hierarchical_analysis(self, files_data: List[DetailedFileAnalysis], 
                                          folder_summaries: Dict[str, FolderSummary]) -> Dict[str, Any]:
        """Perform complete hierarchical analysis."""
        print("🏗️ Starting hierarchical analysis...")
        
        # Step 1: Enhanced Folder-Level Summarization (already done, enhance with LLM)
        self.folder_summaries = await self._enhance_folder_summaries(folder_summaries)
        
        # Step 2: Module-Level Summarization
        self.module_summaries = await self._create_module_summaries()
        
        # Step 3: Domain-Level Summarization
        self.domain_summaries = await self._create_domain_summaries()
        
        # Step 4: Global Architecture Summary
        self.global_summary = await self._create_global_summary()
        
        return {
            "folder_summaries": self.folder_summaries,
            "module_summaries": self.module_summaries,
            "domain_summaries": self.domain_summaries,
            "global_summary": self.global_summary
        }
    
    async def _enhance_folder_summaries(self, folder_summaries: Dict[str, FolderSummary]) -> Dict[str, FolderSummary]:
        """Enhanced folder-level summarization with LLM."""
        print("📁 Enhancing folder summaries...")
        
        enhanced_summaries = {}
        
        for folder_path, folder_summary in folder_summaries.items():
            try:
                # For now, create a basic enhanced summary
                enhanced_summary = folder_summary
                enhanced_summary.llm_summary = f"Enhanced analysis: {folder_summary.folder_purpose} with {folder_summary.total_files} files"
                
                enhanced_summaries[folder_path] = enhanced_summary
                
            except Exception as e:
                print(f"⚠️ Failed to enhance folder summary for {folder_path}: {e}")
                enhanced_summaries[folder_path] = folder_summary
        
        print(f"✅ Enhanced {len(enhanced_summaries)} folder summaries")
        return enhanced_summaries
    
    async def _create_module_summaries(self) -> Dict[str, ModuleSummary]:
        """Module-level summarization."""
        print("🔧 Creating module-level summaries...")
        
        modules = self._identify_modules()
        module_summaries = {}
        
        for module_name, module_data in modules.items():
            try:
                module_summary = ModuleSummary(
                    module_name=module_name,
                    module_path=module_data["path"],
                    folders=module_data["folders"],
                    total_files=module_data["total_files"],
                    primary_languages=module_data["languages"],
                    architecture_role=self._determine_module_role(module_name, module_data),
                    interfaces=self._extract_module_interfaces(module_data),
                    responsibilities=self._extract_module_responsibilities(module_data),
                    key_components=module_data["key_components"]
                )
                
                module_summary.llm_summary = f"Module {module_name}: {module_summary.architecture_role}"
                module_summaries[module_name] = module_summary
                
            except Exception as e:
                print(f"⚠️ Failed to create module summary for {module_name}: {e}")
        
        print(f"✅ Created {len(module_summaries)} module summaries")
        return module_summaries
    
    async def _create_domain_summaries(self) -> Dict[str, DomainSummary]:
        """Domain-level summarization."""
        print("🌐 Creating domain-level summaries...")
        
        domains = self._identify_domains()
        domain_summaries = {}
        
        for domain_name, domain_data in domains.items():
            try:
                domain_summary = DomainSummary(
                    domain_name=domain_name,
                    modules=domain_data["modules"],
                    architecture_overview=self._create_domain_architecture_overview(domain_data),
                    data_flow=self._analyze_domain_data_flow(domain_data),
                    business_logic=self._extract_domain_business_logic(domain_data),
                    integration_points=self._identify_domain_integrations(domain_data),
                    key_patterns=self._identify_domain_patterns(domain_data)
                )
                
                domain_summary.llm_summary = f"Domain {domain_name}: {domain_summary.architecture_overview}"
                domain_summaries[domain_name] = domain_summary
                
            except Exception as e:
                print(f"⚠️ Failed to create domain summary for {domain_name}: {e}")
        
        print(f"✅ Created {len(domain_summaries)} domain summaries")
        return domain_summaries
    
    async def _create_global_summary(self) -> GlobalArchitectureSummary:
        """Global architecture summary."""
        print("🌍 Creating global architecture summary...")
        
        try:
            global_summary = GlobalArchitectureSummary(
                system_overview=self._create_system_overview(),
                key_patterns=self._identify_global_patterns(),
                architectural_decisions=self._extract_architectural_decisions(),
                data_flow_summary=self._create_global_data_flow_summary(),
                scalability_analysis=self._analyze_scalability(),
                security_considerations=self._identify_security_considerations(),
                performance_insights=self._analyze_performance(),
                recommendations=self._generate_recommendations(),
                technology_stack=self._analyze_technology_stack()
            )
            
            global_summary.llm_summary = f"Global architecture: {global_summary.system_overview}"
            
            print("✅ Created global architecture summary")
            return global_summary
            
        except Exception as e:
            print(f"⚠️ Failed to create global summary: {e}")
            return GlobalArchitectureSummary(
                system_overview="Analysis failed",
                llm_summary="Could not generate global architecture summary"
            )
    
    def _identify_modules(self) -> Dict[str, Dict[str, Any]]:
        """Identify logical modules from folder structure."""
        modules = {}
        
        # Group folders into logical modules
        for folder_path, folder_summary in self.folder_summaries.items():
            # Determine module based on folder structure
            path_parts = folder_path.split('/')
            
            if len(path_parts) >= 2:
                module_name = path_parts[0]  # Top-level directory as module
            else:
                module_name = "core"
            
            if module_name not in modules:
                modules[module_name] = {
                    "path": module_name,
                    "folders": [],
                    "total_files": 0,
                    "languages": set(),
                    "key_components": []
                }
            
            modules[module_name]["folders"].append(folder_path)
            modules[module_name]["total_files"] += folder_summary.total_files
            modules[module_name]["languages"].add(folder_summary.primary_language)
            modules[module_name]["key_components"].extend(folder_summary.key_components)
        
        # Convert language sets to lists
        for module_data in modules.values():
            module_data["languages"] = list(module_data["languages"])
        
        return modules
    
    def _identify_domains(self) -> Dict[str, Dict[str, Any]]:
        """Identify business domains from modules."""
        domains = {}
        
        # Simple domain identification based on common patterns
        domain_patterns = {
            "frontend": ["frontend", "ui", "client", "web", "app"],
            "backend": ["backend", "api", "server", "services"],
            "data": ["data", "models", "database", "db"],
            "infrastructure": ["config", "deploy", "docker", "scripts"],
            "shared": ["shared", "common", "utils", "lib"]
        }
        
        for module_name, module_data in self.module_summaries.items():
            domain_assigned = False
            
            for domain_name, patterns in domain_patterns.items():
                if any(pattern in module_name.lower() for pattern in patterns):
                    if domain_name not in domains:
                        domains[domain_name] = {
                            "modules": [],
                            "total_files": 0,
                            "languages": set()
                        }
                    
                    domains[domain_name]["modules"].append(module_name)
                    domains[domain_name]["total_files"] += module_data.total_files
                    domains[domain_name]["languages"].update(module_data.primary_languages)
                    domain_assigned = True
                    break
            
            # If no domain assigned, put in "core"
            if not domain_assigned:
                if "core" not in domains:
                    domains["core"] = {
                        "modules": [],
                        "total_files": 0,
                        "languages": set()
                    }
                domains["core"]["modules"].append(module_name)
                domains["core"]["total_files"] += module_data.total_files
                domains["core"]["languages"].update(module_data.primary_languages)
        
        # Convert language sets to lists
        for domain_data in domains.values():
            domain_data["languages"] = list(domain_data["languages"])
        
        return domains
    
    def _determine_module_role(self, module_name: str, module_data: Dict[str, Any]) -> str:
        """Determine the architectural role of a module."""
        name_lower = module_name.lower()
        
        if any(pattern in name_lower for pattern in ["frontend", "ui", "client"]):
            return "User Interface Layer"
        elif any(pattern in name_lower for pattern in ["backend", "api", "server"]):
            return "Business Logic Layer"
        elif any(pattern in name_lower for pattern in ["data", "model", "db"]):
            return "Data Access Layer"
        elif any(pattern in name_lower for pattern in ["config", "deploy", "script"]):
            return "Infrastructure Layer"
        else:
            return "Core Application Logic"
    
    def _extract_module_interfaces(self, module_data: Dict[str, Any]) -> List[str]:
        """Extract interfaces exposed by the module."""
        interfaces = []
        
        # Look for API endpoints in folder summaries
        for folder_path in module_data["folders"]:
            if folder_path in self.folder_summaries:
                folder_summary = self.folder_summaries[folder_path]
                for api in folder_summary.api_endpoints[:5]:  # Limit to 5
                    method = api.get('method', 'GET')
                    path = api.get('path', '/')
                    interfaces.append(f"{method} {path}")
        
        return interfaces
    
    def _extract_module_responsibilities(self, module_data: Dict[str, Any]) -> List[str]:
        """Extract key responsibilities of the module."""
        responsibilities = []
        
        # Analyze based on folder purposes
        for folder_path in module_data["folders"]:
            if folder_path in self.folder_summaries:
                folder_summary = self.folder_summaries[folder_path]
                if folder_summary.folder_purpose:
                    responsibilities.append(folder_summary.folder_purpose)
        
        return list(set(responsibilities))  # Remove duplicates
    
    def _create_system_overview(self) -> str:
        """Create high-level system overview."""
        total_files = sum(len(folder.files) for folder in self.folder_summaries.values())
        total_modules = len(self.module_summaries)
        total_domains = len(self.domain_summaries)
        
        return f"System with {total_files} files organized into {total_modules} modules across {total_domains} domains"
    
    def _create_domain_architecture_overview(self, domain_data: Dict[str, Any]) -> str:
        """Create architecture overview for a domain."""
        return f"Domain with {len(domain_data['modules'])} modules and {domain_data['total_files']} files"
    
    def _analyze_domain_data_flow(self, domain_data: Dict[str, Any]) -> List[str]:
        """Analyze data flow within a domain."""
        return ["Data flow analysis not implemented"]
    
    def _extract_domain_business_logic(self, domain_data: Dict[str, Any]) -> List[str]:
        """Extract business logic patterns from domain."""
        return ["Business logic extraction not implemented"]
    
    def _identify_domain_integrations(self, domain_data: Dict[str, Any]) -> List[str]:
        """Identify integration points within domain."""
        return ["Integration analysis not implemented"]
    
    def _identify_domain_patterns(self, domain_data: Dict[str, Any]) -> List[str]:
        """Identify architectural patterns in domain."""
        return ["Pattern analysis not implemented"]
    
    def _identify_global_patterns(self) -> List[str]:
        """Identify global architectural patterns."""
        return ["Global pattern analysis not implemented"]
    
    def _extract_architectural_decisions(self) -> List[str]:
        """Extract key architectural decisions."""
        return ["Architectural decision analysis not implemented"]
    
    def _create_global_data_flow_summary(self) -> str:
        """Create global data flow summary."""
        return "Global data flow analysis not implemented"
    
    def _analyze_scalability(self) -> str:
        """Analyze system scalability."""
        return "Scalability analysis not implemented"
    
    def _identify_security_considerations(self) -> List[str]:
        """Identify security considerations."""
        return ["Security analysis not implemented"]
    
    def _analyze_performance(self) -> List[str]:
        """Analyze performance characteristics."""
        return ["Performance analysis not implemented"]
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        return ["Recommendation generation not implemented"]
    
    def _analyze_technology_stack(self) -> Dict[str, List[str]]:
        """Analyze technology stack."""
        return {"analysis": ["Technology stack analysis not implemented"]}