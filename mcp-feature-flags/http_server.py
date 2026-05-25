"""
MCP Feature Flags Server — HTTP transport for n8n integration.

Runs the same MCP tools as server.py but exposes them via HTTP
so n8n's AI Agent node can connect.

Usage:
    python3 mcp-feature-flags/http_server.py

Default: http://localhost:5150/mcp (streamable-http)
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports work
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the shared MCP instance from the main server module
mcp_dir = str(Path(__file__).resolve().parent)
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

from server import mcp  # noqa: E402

PORT = int(os.environ.get("MCP_HTTP_PORT", "5150"))
HOST = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")

if __name__ == "__main__":
    print(f"Starting MCP Feature Flags HTTP server on {HOST}:{PORT}/mcp")
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
