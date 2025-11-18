"""
Dependency Resolver Service

This service handles parsing and managing ESP-IDF component dependencies
from idf_component.yml files in cloned projects.
"""

import os
import yaml
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from database.db import Dependency

logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    Service for parsing and managing ESP-IDF component dependencies.
    
    Supports:
    - Parsing idf_component.yml manifest files
    - Extracting component dependencies
    - Storing dependencies in database
    - Installing components (placeholder for future implementation)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_component_manifests(self, project_path: str) -> List[str]:
        """
        Find all idf_component.yml files in the project directory.
        
        Args:
            project_path: Absolute path to the cloned project
            
        Returns:
            List of absolute paths to idf_component.yml files
        """
        manifest_files = []
        
        if not os.path.exists(project_path):
            logger.warning(f"Project path does not exist: {project_path}")
            return manifest_files
        
        # Search for idf_component.yml files
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore paths
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['build', 'dist', '__pycache__']]
            
            if 'idf_component.yml' in files:
                manifest_path = os.path.join(root, 'idf_component.yml')
                manifest_files.append(manifest_path)
                logger.info(f"Found component manifest: {manifest_path}")
        
        return manifest_files
    
    def parse_component_manifest(self, manifest_path: str) -> Optional[Dict]:
        """
        Parse an idf_component.yml file and extract dependency information.
        
        Args:
            manifest_path: Absolute path to the idf_component.yml file
            
        Returns:
            Dictionary containing parsed manifest data, or None if parsing fails
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"Empty manifest file: {manifest_path}")
                return None
            
            logger.info(f"Successfully parsed manifest: {manifest_path}")
            return data
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {manifest_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading manifest {manifest_path}: {e}")
            return None
    
    def extract_dependencies(self, manifest_data: Dict) -> List[Dict[str, str]]:
        """
        Extract dependency information from parsed manifest data.
        
        The idf_component.yml format supports:
        dependencies:
          component_name: "*"  # Any version
          component_name: "^1.0.0"  # Semantic versioning
          component_name:
            version: "1.0.0"
            git: "https://github.com/user/repo.git"
        
        Args:
            manifest_data: Parsed YAML data from idf_component.yml
            
        Returns:
            List of dependency dictionaries with keys: name, version, source
        """
        dependencies = []
        
        if not manifest_data or 'dependencies' not in manifest_data:
            return dependencies
        
        deps_section = manifest_data['dependencies']
        
        for component_name, dep_info in deps_section.items():
            dependency = {
                'name': component_name,
                'version': None,
                'source': 'component-registry'
            }
            
            if isinstance(dep_info, str):
                # Simple version string: "component_name: '*'" or "component_name: '^1.0.0'"
                dependency['version'] = dep_info
                
            elif isinstance(dep_info, dict):
                # Complex dependency with version and/or git source
                dependency['version'] = dep_info.get('version', '*')
                
                if 'git' in dep_info:
                    dependency['source'] = f"git:{dep_info['git']}"
                elif 'path' in dep_info:
                    dependency['source'] = f"path:{dep_info['path']}"
            
            dependencies.append(dependency)
            logger.debug(f"Extracted dependency: {dependency}")
        
        return dependencies
    
    def scan_project_dependencies(self, project_id: str, project_path: str) -> Tuple[int, int]:
        """
        Scan a project for dependencies and store them in the database.
        
        Args:
            project_id: UUID of the project in the database
            project_path: Absolute path to the cloned project
            
        Returns:
            Tuple of (total_found, newly_added) dependency counts
        """
        # Clear existing dependencies for this project
        self.db.query(Dependency).filter(Dependency.project_id == project_id).delete()
        self.db.commit()
        
        total_found = 0
        newly_added = 0
        
        # Find all component manifests
        manifest_files = self.find_component_manifests(project_path)
        
        if not manifest_files:
            logger.info(f"No component manifests found in project {project_id}")
            return (0, 0)
        
        # Process each manifest file
        for manifest_path in manifest_files:
            manifest_data = self.parse_component_manifest(manifest_path)
            
            if not manifest_data:
                continue
            
            dependencies = self.extract_dependencies(manifest_data)
            total_found += len(dependencies)
            
            # Store dependencies in database
            for dep_info in dependencies:
                try:
                    dependency = Dependency(
                        project_id=project_id,
                        component_name=dep_info['name'],
                        version=dep_info['version'],
                        source=dep_info['source'],
                        installed=False  # Will be updated after installation
                    )
                    self.db.add(dependency)
                    newly_added += 1
                    
                except Exception as e:
                    logger.error(f"Error storing dependency {dep_info['name']}: {e}")
                    continue
        
        try:
            self.db.commit()
            logger.info(f"Project {project_id}: Found {total_found} dependencies, added {newly_added} to database")
        except Exception as e:
            logger.error(f"Error committing dependencies: {e}")
            self.db.rollback()
            return (total_found, 0)
        
        return (total_found, newly_added)
    
    def get_project_dependencies(self, project_id: str) -> List[Dependency]:
        """
        Get all dependencies for a project from the database.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            List of Dependency objects
        """
        return self.db.query(Dependency).filter(
            Dependency.project_id == project_id
        ).all()
    
    def install_dependencies(self, project_id: str, project_path: str) -> Tuple[int, int, List[str]]:
        """
        Install dependencies for a project using ESP-IDF component manager.
        
        This is a placeholder for future implementation that will:
        1. Read dependencies from database
        2. Use `idf.py add-dependency` or component manager API
        3. Update installation status in database
        
        Args:
            project_id: UUID of the project
            project_path: Absolute path to the cloned project
            
        Returns:
            Tuple of (successful_installs, failed_installs, error_messages)
        """
        dependencies = self.get_project_dependencies(project_id)
        
        if not dependencies:
            logger.info(f"No dependencies to install for project {project_id}")
            return (0, 0, [])
        
        successful = 0
        failed = 0
        errors = []
        
        # TODO: Implement actual dependency installation
        # This would involve:
        # 1. Running `idf.py add-dependency <component>` for each dependency
        # 2. Or using the component manager Python API
        # 3. Handling version constraints and git sources
        # 4. Updating the 'installed' flag in the database
        
        logger.info(f"Dependency installation not yet implemented for project {project_id}")
        logger.info(f"Would install {len(dependencies)} dependencies:")
        
        for dep in dependencies:
            logger.info(f"  - {dep.component_name} ({dep.version}) from {dep.source}")
        
        errors.append("Dependency installation feature is not yet implemented")
        
        return (successful, failed, errors)
    
    def validate_dependencies(self, project_path: str) -> Dict[str, any]:
        """
        Validate that all dependencies are properly installed and compatible.
        
        Args:
            project_path: Absolute path to the cloned project
            
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'missing': List[str],
                'conflicts': List[str],
                'warnings': List[str]
            }
        """
        result = {
            'valid': True,
            'missing': [],
            'conflicts': [],
            'warnings': []
        }
        
        # TODO: Implement dependency validation
        # This would check:
        # 1. All required components are available
        # 2. Version constraints are satisfied
        # 3. No circular dependencies
        # 4. Compatible with target ESP-IDF version
        
        logger.info("Dependency validation not yet implemented")
        result['warnings'].append("Dependency validation feature is not yet implemented")
        
        return result
    
    def get_dependency_tree(self, project_id: str) -> Dict[str, any]:
        """
        Build a dependency tree showing all direct and transitive dependencies.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Nested dictionary representing the dependency tree
        """
        dependencies = self.get_project_dependencies(project_id)
        
        tree = {
            'project_id': project_id,
            'direct_dependencies': [],
            'total_count': len(dependencies)
        }
        
        for dep in dependencies:
            tree['direct_dependencies'].append({
                'name': dep.component_name,
                'version': dep.version,
                'source': dep.source,
                'installed': dep.installed
            })
        
        return tree
    
    def generate_requirements_file(self, project_id: str, output_path: str) -> bool:
        """
        Generate a requirements file listing all dependencies.
        
        Args:
            project_id: UUID of the project
            output_path: Path where to write the requirements file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dependencies = self.get_project_dependencies(project_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# ESP-IDF Component Dependencies\n")
                f.write(f"# Project ID: {project_id}\n")
                f.write(f"# Total dependencies: {len(dependencies)}\n\n")
                
                for dep in dependencies:
                    f.write(f"{dep.component_name}")
                    if dep.version and dep.version != '*':
                        f.write(f"=={dep.version}")
                    f.write(f"  # Source: {dep.source}\n")
            
            logger.info(f"Generated requirements file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating requirements file: {e}")
            return False
