"""File management tools for MCP server."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import os


class FileManager:
    """Secure file operations within workspace."""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path).resolve()
        
    def _validate_path(self, relative_path: str) -> Optional[Path]:
        """Validate that path is within workspace."""
        try:
            full_path = (self.workspace_path / relative_path).resolve()
            
            # Ensure path is within workspace
            if not str(full_path).startswith(str(self.workspace_path)):
                return None
                
            return full_path
        except Exception:
            return None
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read a file from the workspace."""
        full_path = self._validate_path(path)
        
        if not full_path:
            return {
                "success": False,
                "error": f"Invalid path: {path}",
                "content": None
            }
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
                "content": None
            }
        
        if not full_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path}",
                "content": None
            }
        
        try:
            content = full_path.read_text(encoding=encoding)
            return {
                "success": True,
                "error": None,
                "content": content,
                "path": path,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}",
                "content": None
            }
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8", 
                   create_dirs: bool = True) -> Dict[str, Any]:
        """Write content to a file in the workspace."""
        full_path = self._validate_path(path)
        
        if not full_path:
            return {
                "success": False,
                "error": f"Invalid path: {path}"
            }
        
        try:
            # Create parent directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            full_path.write_text(content, encoding=encoding)
            
            return {
                "success": True,
                "error": None,
                "path": path,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}"
            }
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory."""
        full_path = self._validate_path(path)
        
        if not full_path:
            return {
                "success": False,
                "error": f"Invalid path: {path}",
                "entries": []
            }
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {path}",
                "entries": []
            }
        
        if not full_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path}",
                "entries": []
            }
        
        try:
            entries = []
            for item in sorted(full_path.iterdir()):
                entries.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "success": True,
                "error": None,
                "entries": entries,
                "path": path
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory: {str(e)}",
                "entries": []
            }
    
    def file_exists(self, path: str) -> Dict[str, Any]:
        """Check if a file exists."""
        full_path = self._validate_path(path)
        
        if not full_path:
            return {
                "success": False,
                "error": f"Invalid path: {path}",
                "exists": False
            }
        
        return {
            "success": True,
            "error": None,
            "exists": full_path.exists(),
            "is_file": full_path.is_file() if full_path.exists() else None,
            "is_dir": full_path.is_dir() if full_path.exists() else None
        }
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed information about a file."""
        full_path = self._validate_path(path)
        
        if not full_path:
            return {
                "success": False,
                "error": f"Invalid path: {path}"
            }
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Path not found: {path}"
            }
        
        try:
            stat = full_path.stat()
            return {
                "success": True,
                "error": None,
                "path": path,
                "type": "directory" if full_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting file info: {str(e)}"
            }
