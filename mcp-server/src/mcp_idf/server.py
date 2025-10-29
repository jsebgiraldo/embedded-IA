"""MCP Server implementation for ESP-IDF toolchain."""

import asyncio
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import IDFTools, FileManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-idf")


class MCPIDFServer:
    """MCP Server for ESP-IDF operations."""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.app = Server("mcp-idf")
        self.idf_tools = IDFTools(workspace_path)
        self.file_manager = FileManager(workspace_path)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.app.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="build",
                    description="Build the ESP-IDF project using idf.py build",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="flash",
                    description="Flash firmware to ESP32 device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "string",
                                "description": "Serial port (default: /dev/ttyUSB0)",
                                "default": "/dev/ttyUSB0"
                            },
                            "baud": {
                                "type": "integer",
                                "description": "Baud rate (default: 460800)",
                                "default": 460800
                            }
                        },
                    },
                ),
                Tool(
                    name="monitor",
                    description="Start serial monitor (returns command to run)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "port": {
                                "type": "string",
                                "description": "Serial port (default: /dev/ttyUSB0)",
                                "default": "/dev/ttyUSB0"
                            }
                        },
                    },
                ),
                Tool(
                    name="set_target",
                    description="Set ESP-IDF target chip (esp32, esp32s2, esp32s3, esp32c3, esp32c6, esp32h2)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target chip name",
                                "enum": ["esp32", "esp32s2", "esp32s3", "esp32c3", "esp32c6", "esp32h2"]
                            }
                        },
                        "required": ["target"],
                    },
                ),
                Tool(
                    name="clean",
                    description="Clean build artifacts with idf.py fullclean",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="size",
                    description="Show binary size information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="doctor",
                    description="Run ESP-IDF doctor diagnostics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="read_file",
                    description="Read a file from the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to file from workspace root"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding (default: utf-8)",
                                "default": "utf-8"
                            }
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="write_file",
                    description="Write content to a file in the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to file from workspace root"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to file"
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding (default: utf-8)",
                                "default": "utf-8"
                            }
                        },
                        "required": ["path", "content"],
                    },
                ),
                Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to directory (default: .)",
                                "default": "."
                            }
                        },
                    },
                ),
                Tool(
                    name="file_info",
                    description="Get detailed information about a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to file or directory"
                            }
                        },
                        "required": ["path"],
                    },
                ),
            ]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Handle tool calls."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                # ESP-IDF commands
                if name == "build":
                    result = self.idf_tools.build()
                elif name == "flash":
                    port = arguments.get("port", "/dev/ttyUSB0")
                    baud = arguments.get("baud", 460800)
                    result = self.idf_tools.flash(port, baud)
                elif name == "monitor":
                    port = arguments.get("port", "/dev/ttyUSB0")
                    result = self.idf_tools.monitor(port)
                elif name == "set_target":
                    target = arguments["target"]
                    result = self.idf_tools.set_target(target)
                elif name == "clean":
                    result = self.idf_tools.clean()
                elif name == "size":
                    result = self.idf_tools.size()
                elif name == "doctor":
                    result = self.idf_tools.doctor()
                
                # File operations
                elif name == "read_file":
                    path = arguments["path"]
                    encoding = arguments.get("encoding", "utf-8")
                    result = self.file_manager.read_file(path, encoding)
                elif name == "write_file":
                    path = arguments["path"]
                    content = arguments["content"]
                    encoding = arguments.get("encoding", "utf-8")
                    result = self.file_manager.write_file(path, content, encoding)
                elif name == "list_directory":
                    path = arguments.get("path", ".")
                    result = self.file_manager.list_directory(path)
                elif name == "file_info":
                    path = arguments["path"]
                    result = self.file_manager.get_file_info(path)
                else:
                    result = {"success": False, "error": f"Unknown tool: {name}"}
                
                # Format response
                response_text = self._format_result(result)
                return [TextContent(type="text", text=response_text)]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    def _format_result(self, result: dict) -> str:
        """Format tool result as text."""
        import json
        return json.dumps(result, indent=2)
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP-IDF Server started")
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )


def main():
    """Main entry point."""
    import sys
    
    # Get workspace path from environment or argument
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    server = MCPIDFServer(workspace_path)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
