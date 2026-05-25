#!/bin/bash
# Start all services for n8n integration
# Usage: ./start-all.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== Starting ProShop + n8n Infrastructure ==="

# 1. Start Docker services (n8n, mongo, qdrant)
echo "[1/3] Starting Docker services..."
docker compose up -d

# Wait for n8n to be ready
echo "[2/3] Waiting for n8n..."
until curl -s -o /dev/null http://localhost:5678; do
    sleep 1
done
echo "  n8n ready at http://localhost:5678"

# 2. Start MCP HTTP server (background)
echo "[3/3] Starting MCP HTTP server on port 5150..."
python3 mcp-feature-flags/http_server.py &
MCP_PID=$!
sleep 2
echo "  MCP server ready at http://localhost:5150/mcp (PID: $MCP_PID)"

# 3. Start ProShop app
echo ""
echo "=== Starting ProShop App ==="
echo "  Backend:  http://localhost:5001"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Services running:"
echo "  n8n:      http://localhost:5678"
echo "  MCP HTTP: http://localhost:5150/mcp"
echo "  Mongo:    localhost:27017"
echo "  Qdrant:   localhost:6333"
echo ""
echo "MCP PID: $MCP_PID (kill with: kill $MCP_PID)"
echo ""

npm run dev
