"""
QEMU Manager for ESP32 Simulation
Manages QEMU instances for testing without physical hardware
"""

import os
import subprocess
import signal
import time
import psutil
from pathlib import Path
from typing import Dict, Any, Optional


class QEMUManager:
    """Manages QEMU simulation for ESP32"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.build_path = self.workspace_path / "build"
        self.qemu_pid_file = self.workspace_path / ".qemu_pid"
        self.qemu_log_file = self.workspace_path / ".qemu_output.log"
    
    def start_qemu(
        self,
        target: str = "esp32",
        elf_path: Optional[str] = None,
        monitor: bool = True,
        graphics: bool = False
    ) -> Dict[str, Any]:
        """
        Start QEMU simulation
        
        Args:
            target: ESP32 target (esp32, esp32s3, etc.)
            elf_path: Path to ELF file (defaults to build/my_app.elf)
            monitor: Enable QEMU monitor
            graphics: Enable graphics display
            
        Returns:
            Dict with success status and process info
        """
        # Check if QEMU is already running
        if self._is_qemu_running():
            return {
                "success": False,
                "error": "QEMU is already running. Stop it first with stop_qemu()",
                "pid": self._get_qemu_pid()
            }
        
        # Default ELF path
        if not elf_path:
            elf_path = str(self.build_path / "my_app.elf")
        
        # Verify ELF exists
        if not Path(elf_path).exists():
            return {
                "success": False,
                "error": f"ELF file not found: {elf_path}. Build the project first.",
                "suggestion": "Run: idf_build()"
            }
        
        # Map target to QEMU machine
        qemu_machines = {
            "esp32": "esp32",
            "esp32s3": "esp32s3",
        }
        
        if target not in qemu_machines:
            return {
                "success": False,
                "error": f"QEMU not supported for target '{target}'",
                "supported_targets": list(qemu_machines.keys()),
                "suggestion": "Use esp32 or esp32s3 for QEMU simulation"
            }
        
        # Build QEMU command
        qemu_cmd = [
            "qemu-system-xtensa",
            "-M", qemu_machines[target],
            "-kernel", elf_path,
            "-serial", "stdio",
        ]
        
        if not graphics:
            qemu_cmd.extend(["-nographic"])
        
        if monitor:
            qemu_cmd.extend(["-monitor", "telnet:127.0.0.1:4444,server,nowait"])
        
        try:
            # Start QEMU in background
            log_file = open(self.qemu_log_file, 'w')
            process = subprocess.Popen(
                qemu_cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(self.workspace_path),
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Save PID
            with open(self.qemu_pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a bit to check if it started successfully
            time.sleep(1)
            
            if process.poll() is not None:
                # Process died immediately
                with open(self.qemu_log_file, 'r') as f:
                    error_output = f.read()
                return {
                    "success": False,
                    "error": "QEMU failed to start",
                    "output": error_output
                }
            
            return {
                "success": True,
                "pid": process.pid,
                "target": target,
                "elf": elf_path,
                "log_file": str(self.qemu_log_file),
                "monitor_port": 4444 if monitor else None,
                "message": f"✅ QEMU started successfully for {target}",
                "instructions": [
                    f"View output: tail -f {self.qemu_log_file}",
                    "Connect to monitor: telnet localhost 4444" if monitor else None,
                    "Stop simulation: stop_qemu()"
                ]
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "qemu-system-xtensa not found",
                "suggestion": "Install QEMU: apt-get install qemu-system-xtensa"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start QEMU: {str(e)}"
            }
    
    def stop_qemu(self) -> Dict[str, Any]:
        """Stop running QEMU simulation"""
        if not self._is_qemu_running():
            return {
                "success": False,
                "error": "No QEMU instance is running"
            }
        
        pid = self._get_qemu_pid()
        
        try:
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            
            # Force kill if still running
            if self._is_qemu_running():
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            
            # Cleanup PID file
            if self.qemu_pid_file.exists():
                self.qemu_pid_file.unlink()
            
            return {
                "success": True,
                "message": f"✅ QEMU stopped (PID: {pid})"
            }
            
        except ProcessLookupError:
            # Process already dead
            if self.qemu_pid_file.exists():
                self.qemu_pid_file.unlink()
            return {
                "success": True,
                "message": "QEMU process was already stopped"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop QEMU: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of QEMU simulation"""
        if not self._is_qemu_running():
            return {
                "running": False,
                "message": "No QEMU instance is running"
            }
        
        pid = self._get_qemu_pid()
        
        try:
            process = psutil.Process(pid)
            
            return {
                "running": True,
                "pid": pid,
                "status": process.status(),
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "runtime_seconds": time.time() - process.create_time(),
                "log_file": str(self.qemu_log_file),
                "command": " ".join(process.cmdline())
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return {
                "running": False,
                "error": f"Process exists but cannot be accessed: {str(e)}"
            }
    
    def get_output(self, lines: int = 50) -> Dict[str, Any]:
        """
        Get recent QEMU output
        
        Args:
            lines: Number of recent lines to return
            
        Returns:
            Dict with output
        """
        if not self.qemu_log_file.exists():
            return {
                "success": False,
                "error": "No QEMU log file found"
            }
        
        try:
            # Read last N lines
            with open(self.qemu_log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            return {
                "success": True,
                "output": "".join(recent_lines),
                "total_lines": len(all_lines),
                "returned_lines": len(recent_lines)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read log: {str(e)}"
            }
    
    def send_monitor_command(self, command: str) -> Dict[str, Any]:
        """
        Send command to QEMU monitor
        
        Args:
            command: QEMU monitor command (e.g., 'info registers')
            
        Returns:
            Dict with command result
        """
        if not self._is_qemu_running():
            return {
                "success": False,
                "error": "QEMU is not running"
            }
        
        try:
            # Connect to monitor via telnet
            result = subprocess.run(
                ["bash", "-c", f"echo '{command}' | nc localhost 4444"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "success": True,
                "command": command,
                "output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Monitor command timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send monitor command: {str(e)}"
            }
    
    def _is_qemu_running(self) -> bool:
        """Check if QEMU is running"""
        if not self.qemu_pid_file.exists():
            return False
        
        pid = self._get_qemu_pid()
        if pid is None:
            return False
        
        try:
            # Check if process exists and is qemu
            process = psutil.Process(pid)
            return 'qemu' in process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _get_qemu_pid(self) -> Optional[int]:
        """Get QEMU PID from file"""
        try:
            with open(self.qemu_pid_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return None
