#!/bin/bash
# MCP Server initialization script

echo "🚀 Initializing MCP Server for ESP-IDF..."

# Install dependencies
pip install -e /mcp-server

# Verify installation
python3 -c "from mcp_idf.tools import IDFTools; print('✅ MCP Server installed successfully')"

# Keep container active
tail -f /dev/null

