"""MCP Client for LangChain integration."""

import json
import subprocess
from typing import Any, Dict, Optional
from langchain_core.tools import tool


class MCPClient:
    """Client to interact with MCP-IDF server."""
    
    def __init__(self, server_command: str = "mcp-idf"):
        self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            # For now, we'll use direct execution
            # In production, this would use the MCP protocol over stdio
            from mcp_idf.tools import IDFTools, FileManager
            
            idf_tools = IDFTools()
            file_manager = FileManager()
            
            # Route to appropriate tool
            if tool_name == "build":
                result = idf_tools.build()
            elif tool_name == "flash":
                result = idf_tools.flash(**arguments)
            elif tool_name == "monitor":
                result = idf_tools.monitor(**arguments)
            elif tool_name == "set_target":
                result = idf_tools.set_target(arguments["target"])
            elif tool_name == "clean":
                result = idf_tools.clean()
            elif tool_name == "size":
                result = idf_tools.size()
            elif tool_name == "doctor":
                result = idf_tools.doctor()
            elif tool_name == "get_artifacts":
                result = idf_tools.get_artifacts_summary()
            elif tool_name == "run_qemu":
                result = idf_tools.run_qemu(**arguments)
            elif tool_name == "stop_qemu":
                result = idf_tools.stop_qemu()
            elif tool_name == "qemu_status":
                result = idf_tools.qemu_status()
            elif tool_name == "qemu_output":
                result = idf_tools.qemu_output(**arguments)
            elif tool_name == "qemu_inspect":
                result = idf_tools.qemu_inspect(**arguments)
            elif tool_name == "read_file":
                result = file_manager.read_file(**arguments)
            elif tool_name == "write_file":
                result = file_manager.write_file(**arguments)
            elif tool_name == "list_directory":
                result = file_manager.list_directory(**arguments)
            elif tool_name == "file_info":
                result = file_manager.get_file_info(arguments["path"])
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
    
    def get_langchain_tools(self) -> list:
        """Get LangChain tools that wrap MCP tools."""
        
        @tool
        def idf_build(query: str = "") -> str:
            """Build the ESP-IDF project. Returns build output and errors."""
            return self._call_tool("build", {})
        
        @tool
        def idf_flash(port: str = "/dev/ttyUSB0", use_cached: bool = True) -> str:
            """
            Flash firmware to device using cached build artifacts when available.
            Input: serial port path (default: /dev/ttyUSB0), use_cached (default: True)
            Set use_cached=False to force rebuild before flashing.
            """
            return self._call_tool("flash", {"port": port, "use_cached": use_cached})
        
        @tool
        def idf_set_target(target: str) -> str:
            """Set ESP-IDF target chip. Input: target name (esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2)"""
            return self._call_tool("set_target", {"target": target})
        
        @tool
        def idf_clean(query: str = "") -> str:
            """Clean build artifacts."""
            return self._call_tool("clean", {})
        
        @tool
        def idf_size(query: str = "") -> str:
            """Show firmware size information."""
            return self._call_tool("size", {})
        
        @tool
        def idf_doctor(query: str = "") -> str:
            """Run ESP-IDF diagnostics to check environment setup."""
            return self._call_tool("doctor", {})
        
        @tool
        def read_source_file(path: str) -> str:
            """Read a source file. Input: relative path from workspace root (e.g., 'main/main.c')"""
            return self._call_tool("read_file", {"path": path})
        
        @tool
        def write_source_file(path: str, content: str) -> str:
            """Write content to a file. Input: path (relative) and content (new file content)"""
            return self._call_tool("write_file", {"path": path, "content": content})
        
        @tool
        def list_files(path: str = ".") -> str:
            """List files in a directory. Input: relative directory path (default: '.')"""
            return self._call_tool("list_directory", {"path": path})
        
        @tool
        def get_build_artifacts(query: str = "") -> str:
            """Get information about cached build artifacts from the last build."""
            return self._call_tool("get_artifacts", {})
        
        @tool
        def run_qemu_simulation(target: str = "", elf_path: str = "") -> str:
            """
            Start QEMU simulation for testing without hardware.
            Input: target (esp32, esp32s3) and optional elf_path.
            Returns simulation info and instructions.
            """
            args = {}
            if target:
                args["target"] = target
            if elf_path:
                args["elf_path"] = elf_path
            return self._call_tool("run_qemu", args)
        
        @tool
        def stop_qemu_simulation(query: str = "") -> str:
            """Stop running QEMU simulation."""
            return self._call_tool("stop_qemu", {})
        
        @tool
        def qemu_simulation_status(query: str = "") -> str:
            """Get status of running QEMU simulation (PID, CPU, memory, runtime)."""
            return self._call_tool("qemu_status", {})
        
        @tool
        def qemu_get_output(lines: int = 50) -> str:
            """Get recent output from QEMU simulation. Input: number of lines (default: 50)"""
            return self._call_tool("qemu_output", {"lines": lines})
        
        @tool
        def qemu_inspect_state(command: str = "info registers") -> str:
            """
            Inspect QEMU internal state via monitor commands.
            Input: QEMU monitor command (e.g., 'info registers', 'info mem', 'info mtree').
            Useful for debugging and connecting with idf_doctor for validation.
            """
            return self._call_tool("qemu_inspect", {"command": command})
        
        return [
            idf_build,
            idf_flash,
            idf_set_target,
            idf_clean,
            idf_size,
            idf_doctor,
            get_build_artifacts,
            run_qemu_simulation,
            stop_qemu_simulation,
            qemu_simulation_status,
            qemu_get_output,
            qemu_inspect_state,
            read_source_file,
            write_source_file,
            list_files
        ]
