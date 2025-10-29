"""ESP-IDF toolchain tools for MCP server."""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .artifact_manager import ArtifactManager
from .qemu_manager import QEMUManager


class IDFTools:
    """Wrapper for ESP-IDF toolchain commands."""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.target = os.getenv("ESP_IDF_TARGET", "esp32")
        self.artifact_manager = ArtifactManager(workspace_path)
        self.qemu_manager = QEMUManager(workspace_path)
    
    def _run_command(self, command: str, capture_output: bool = True) -> Dict[str, Any]:
        """Execute a shell command and return results."""
        try:
            cmd = ["bash", "-lc", command]
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timeout after 300 seconds: {command}",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }
    
    def build(self) -> Dict[str, Any]:
        """Build the ESP-IDF project and save artifacts."""
        result = self._run_command("idf.py build")
        
        # Save build artifacts if successful
        if result["success"]:
            try:
                metadata = self.artifact_manager.save_build_artifacts(
                    target=self.target,
                    project_name="my_app",
                    build_status="success",
                    build_output=result["stdout"]
                )
                result["artifacts"] = metadata
                result["stdout"] += "\n\n✅ Build artifacts saved for Flash agent"
            except Exception as e:
                result["stderr"] += f"\n⚠️  Warning: Could not save artifacts: {str(e)}"
        
        return result
    
    def flash(self, port: str = "/dev/ttyUSB0", baud: int = 460800, use_cached: bool = True) -> Dict[str, Any]:
        """
        Flash the firmware to the device using cached artifacts when available.
        
        Args:
            port: Serial port (e.g., /dev/ttyUSB0, /dev/cu.usbmodem21101)
            baud: Baud rate for flashing
            use_cached: Use cached build artifacts if available (default: True)
        """
        # Try to use cached artifacts
        if use_cached:
            artifacts = self.artifact_manager.get_build_artifacts()
            if artifacts and artifacts["build_status"] == "success":
                flash_args = self.artifact_manager.get_flash_args()
                if flash_args:
                    # Build esptool command with cached artifacts
                    flash_parts = []
                    for arg in flash_args:
                        flash_parts.append(f"{arg['address']} {arg['binary_path']}")
                    
                    flash_cmd = " ".join(flash_parts)
                    target = artifacts["target"]
                    
                    # Use esptool directly with cached binaries
                    command = (
                        f"python -m esptool --chip {target} -p {port} -b {baud} "
                        f"--before=default_reset --after=hard_reset write_flash "
                        f"--flash_mode dio --flash_freq 80m --flash_size 2MB {flash_cmd}"
                    )
                    
                    result = self._run_command(command)
                    
                    # Add artifact info to result
                    if result["success"]:
                        result["stdout"] = (
                            f"📦 Used cached build artifacts from {artifacts['timestamp']}\n"
                            f"🎯 Target: {target}\n"
                            f"⚡ Flashed without rebuilding!\n\n"
                            f"{result['stdout']}"
                        )
                    
                    return result
        
        # Fallback to idf.py flash (which will rebuild if needed)
        command = f"idf.py -p {port} -b {baud} flash"
        result = self._run_command(command)
        
        if not use_cached:
            result["stdout"] = "⚠️  Forced rebuild and flash\n\n" + result["stdout"]
        else:
            result["stdout"] = "⚠️  No cached artifacts found, rebuilding...\n\n" + result["stdout"]
        
        return result
    
    def monitor(self, port: str = "/dev/ttyUSB0") -> Dict[str, Any]:
        """Start serial monitor (non-blocking version)."""
        # For monitor, we just return instructions since it's interactive
        return {
            "success": True,
            "returncode": 0,
            "stdout": f"To start monitor, run: idf.py -p {port} monitor",
            "stderr": "",
            "command": f"idf.py -p {port} monitor"
        }
    
    def set_target(self, target: str) -> Dict[str, Any]:
        """Set the ESP-IDF target chip."""
        valid_targets = ["esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6", "esp32h2"]
        
        if target not in valid_targets:
            return {
                "success": False,
                "returncode": 1,
                "stdout": "",
                "stderr": f"Invalid target '{target}'. Valid targets: {', '.join(valid_targets)}",
                "command": f"idf.py set-target {target}"
            }
        
        self.target = target
        return self._run_command(f"idf.py set-target {target}")
    
    def clean(self) -> Dict[str, Any]:
        """Clean build artifacts."""
        return self._run_command("idf.py fullclean")
    
    def menuconfig(self) -> Dict[str, Any]:
        """Open menuconfig (returns instructions)."""
        return {
            "success": True,
            "returncode": 0,
            "stdout": "To configure, run: idf.py menuconfig",
            "stderr": "",
            "command": "idf.py menuconfig"
        }
    
    def size(self) -> Dict[str, Any]:
        """Show size information of the binary."""
        return self._run_command("idf.py size")
    
    def doctor(self) -> Dict[str, Any]:
        """Run ESP-IDF doctor diagnostics."""
        return self._run_command("idf.py doctor")
    
    def get_artifacts_summary(self) -> Dict[str, Any]:
        """Get summary of cached build artifacts."""
        summary = self.artifact_manager.get_artifact_summary()
        metadata = self.artifact_manager.get_build_artifacts(validate=False)
        
        return {
            "success": True,
            "returncode": 0,
            "stdout": summary,
            "stderr": "",
            "command": "artifact_manager.get_artifact_summary()",
            "metadata": metadata
        }
    
    # QEMU Simulation Methods
    
    def run_qemu(self, target: Optional[str] = None, elf_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Start QEMU simulation for testing without hardware.
        
        Args:
            target: ESP32 target (defaults to current target)
            elf_path: Path to ELF file (defaults to build/my_app.elf)
        """
        if target is None:
            target = self.target
        
        result = self.qemu_manager.start_qemu(
            target=target,
            elf_path=elf_path,
            monitor=True,
            graphics=False
        )
        
        # Format output for MCP
        if result["success"]:
            output = [
                f"✅ QEMU simulation started for {target}",
                f"PID: {result['pid']}",
                f"ELF: {result['elf']}",
                f"",
                "📋 Instructions:",
            ]
            for instruction in result["instructions"]:
                if instruction:
                    output.append(f"  • {instruction}")
            
            return {
                "success": True,
                "returncode": 0,
                "stdout": "\n".join(output),
                "stderr": "",
                "command": f"qemu_manager.start_qemu(target='{target}')",
                "qemu_info": result
            }
        else:
            return {
                "success": False,
                "returncode": 1,
                "stdout": "",
                "stderr": result.get("error", "Unknown error"),
                "command": "qemu_manager.start_qemu()",
                "suggestion": result.get("suggestion", "")
            }
    
    def stop_qemu(self) -> Dict[str, Any]:
        """Stop running QEMU simulation."""
        result = self.qemu_manager.stop_qemu()
        
        return {
            "success": result["success"],
            "returncode": 0 if result["success"] else 1,
            "stdout": result.get("message", ""),
            "stderr": result.get("error", ""),
            "command": "qemu_manager.stop_qemu()"
        }
    
    def qemu_status(self) -> Dict[str, Any]:
        """Get status of running QEMU simulation."""
        status = self.qemu_manager.get_status()
        
        if status["running"]:
            output = [
                "🟢 QEMU is running",
                f"PID: {status['pid']}",
                f"Status: {status['status']}",
                f"CPU: {status['cpu_percent']:.1f}%",
                f"Memory: {status['memory_mb']:.1f} MB",
                f"Runtime: {status['runtime_seconds']:.1f}s",
                f"",
                f"Log file: {status['log_file']}",
            ]
        else:
            output = ["🔴 QEMU is not running"]
        
        return {
            "success": True,
            "returncode": 0,
            "stdout": "\n".join(output),
            "stderr": "",
            "command": "qemu_manager.get_status()",
            "status": status
        }
    
    def qemu_output(self, lines: int = 50) -> Dict[str, Any]:
        """Get recent output from QEMU simulation."""
        result = self.qemu_manager.get_output(lines=lines)
        
        if result["success"]:
            header = f"📋 QEMU Output (last {result['returned_lines']} of {result['total_lines']} lines):\n" + "=" * 60 + "\n"
            output = header + result["output"]
        else:
            output = ""
        
        return {
            "success": result["success"],
            "returncode": 0 if result["success"] else 1,
            "stdout": output,
            "stderr": result.get("error", ""),
            "command": f"qemu_manager.get_output(lines={lines})"
        }
    
    def qemu_inspect(self, command: str = "info registers") -> Dict[str, Any]:
        """
        Inspect QEMU state via monitor commands.
        
        Args:
            command: QEMU monitor command (e.g., 'info registers', 'info mem', 'info mtree')
        """
        result = self.qemu_manager.send_monitor_command(command)
        
        return {
            "success": result["success"],
            "returncode": 0 if result["success"] else 1,
            "stdout": result.get("output", ""),
            "stderr": result.get("error", ""),
            "command": f"qemu_monitor: {command}"
        }

