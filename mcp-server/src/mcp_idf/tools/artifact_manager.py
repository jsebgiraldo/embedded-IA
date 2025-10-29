"""
Build Artifact Manager
Manages sharing of build artifacts between Builder and Flash agents
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class ArtifactManager:
    """Manages build artifacts and metadata for sharing between agents"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.build_path = self.workspace_path / "build"
        self.artifacts_cache = self.workspace_path / ".artifacts_cache"
        self.artifacts_cache.mkdir(exist_ok=True)
        self.metadata_file = self.artifacts_cache / "build_metadata.json"
    
    def save_build_artifacts(
        self,
        target: str,
        project_name: str = "my_app",
        build_status: str = "success",
        build_output: str = ""
    ) -> Dict:
        """
        Save build artifacts metadata after successful build
        
        Args:
            target: ESP32 target (esp32, esp32c6, etc.)
            project_name: Name of the project
            build_status: Build status (success/failed)
            build_output: Build command output
            
        Returns:
            Dictionary with artifact metadata
        """
        # Define expected binary paths
        bootloader_bin = self.build_path / "bootloader" / "bootloader.bin"
        partition_table_bin = self.build_path / "partition_table" / "partition-table.bin"
        app_bin = self.build_path / f"{project_name}.bin"
        app_elf = self.build_path / f"{project_name}.elf"
        
        # Check which files exist
        artifacts = {
            "bootloader": str(bootloader_bin) if bootloader_bin.exists() else None,
            "partition_table": str(partition_table_bin) if partition_table_bin.exists() else None,
            "app_bin": str(app_bin) if app_bin.exists() else None,
            "app_elf": str(app_elf) if app_elf.exists() else None,
        }
        
        # Calculate checksums for verification
        checksums = {}
        for name, path in artifacts.items():
            if path and Path(path).exists():
                checksums[name] = self._calculate_checksum(path)
        
        # Extract memory usage from build output
        memory_usage = self._extract_memory_usage(build_output)
        
        # Create metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "project_name": project_name,
            "build_status": build_status,
            "artifacts": artifacts,
            "checksums": checksums,
            "memory_usage": memory_usage,
            "build_path": str(self.build_path),
        }
        
        # Save metadata to file
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def get_build_artifacts(self, validate: bool = True) -> Optional[Dict]:
        """
        Get latest build artifacts metadata
        
        Args:
            validate: Whether to validate checksums
            
        Returns:
            Dictionary with artifact metadata or None if not found
        """
        if not self.metadata_file.exists():
            return None
        
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Validate artifacts exist
        if validate:
            for name, path in metadata["artifacts"].items():
                if path and not Path(path).exists():
                    return None
                
                # Verify checksum
                if path and name in metadata["checksums"]:
                    current_checksum = self._calculate_checksum(path)
                    if current_checksum != metadata["checksums"][name]:
                        return None
        
        return metadata
    
    def get_flash_args(self) -> Optional[List[Dict[str, str]]]:
        """
        Get flash arguments for esptool
        
        Returns:
            List of dicts with {address, binary_path} or None
        """
        metadata = self.get_build_artifacts()
        if not metadata or metadata["build_status"] != "success":
            return None
        
        artifacts = metadata["artifacts"]
        flash_args = []
        
        # Bootloader at 0x0
        if artifacts["bootloader"]:
            flash_args.append({
                "address": "0x0",
                "binary_path": artifacts["bootloader"]
            })
        
        # Partition table at 0x8000
        if artifacts["partition_table"]:
            flash_args.append({
                "address": "0x8000",
                "binary_path": artifacts["partition_table"]
            })
        
        # Application at 0x10000
        if artifacts["app_bin"]:
            flash_args.append({
                "address": "0x10000",
                "binary_path": artifacts["app_bin"]
            })
        
        return flash_args if flash_args else None
    
    def clear_artifacts(self):
        """Clear artifact cache"""
        if self.metadata_file.exists():
            self.metadata_file.unlink()
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _extract_memory_usage(self, build_output: str) -> Dict:
        """Extract memory usage from build output"""
        memory = {}
        
        # Extract binary size
        if "binary size" in build_output:
            lines = build_output.split('\n')
            for line in lines:
                if "binary size" in line.lower():
                    # Example: "my_app.bin binary size 0x25190 bytes"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "size" and i + 1 < len(parts):
                            size_hex = parts[i + 1]
                            if size_hex.startswith("0x"):
                                memory["binary_size_bytes"] = int(size_hex, 16)
                                memory["binary_size_hex"] = size_hex
                                break
        
        # Extract free space percentage
        if "% free" in build_output or "%) free" in build_output:
            lines = build_output.split('\n')
            for line in lines:
                if "free" in line.lower() and "%" in line:
                    # Example: "0xdae70 bytes (86%) free"
                    import re
                    match = re.search(r'\((\d+)%\)', line)
                    if match:
                        memory["flash_free_percent"] = int(match.group(1))
                        break
        
        return memory
    
    def get_artifact_summary(self) -> str:
        """Get human-readable summary of artifacts"""
        metadata = self.get_build_artifacts(validate=False)
        if not metadata:
            return "❌ No build artifacts found"
        
        summary = []
        summary.append(f"📦 Build Artifacts Summary")
        summary.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        summary.append(f"🎯 Target: {metadata['target']}")
        summary.append(f"📝 Project: {metadata['project_name']}")
        summary.append(f"✅ Status: {metadata['build_status']}")
        summary.append(f"🕐 Built: {metadata['timestamp']}")
        
        if metadata['memory_usage']:
            mem = metadata['memory_usage']
            summary.append(f"\n💾 Memory Usage:")
            if 'binary_size_hex' in mem:
                summary.append(f"   Size: {mem['binary_size_hex']} ({mem.get('binary_size_bytes', 0):,} bytes)")
            if 'flash_free_percent' in mem:
                summary.append(f"   Free: {mem['flash_free_percent']}%")
        
        summary.append(f"\n📄 Artifacts:")
        for name, path in metadata['artifacts'].items():
            if path:
                exists = "✅" if Path(path).exists() else "❌"
                summary.append(f"   {exists} {name}: {Path(path).name}")
        
        return '\n'.join(summary)
