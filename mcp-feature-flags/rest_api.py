"""
REST API wrapper for MCP Feature Flags tools.

Provides simple REST endpoints that n8n can call directly,
without needing MCP protocol (session IDs, JSON-RPC).

Also serves MCP streamable-http on the same port for AI Agent nodes.

Usage:
    python3 mcp-feature-flags/rest_api.py

Endpoints:
    GET  /health                        — health check
    GET  /api/features                  — list all features
    GET  /api/features/:name            — get one feature
    POST /api/features/:name/state      — set state {state: "Enabled"|"Disabled"|"Testing"}
    POST /api/features/:name/traffic    — set traffic {percentage: 0-100}
    GET  /api/logs                      — read traffic logs (from simulators/logs.json)
"""

import json
import os
import sys
from pathlib import Path

# Ensure imports work
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
mcp_dir = str(Path(__file__).resolve().parent)
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.requests import Request

# Import MCP tool functions from server.py
from server import get_feature_info, set_feature_state, adjust_traffic_rollout, list_features

PORT = int(os.environ.get("MCP_HTTP_PORT", "5150"))
HOST = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
AUTH_SECRET = os.environ.get("MCP_AUTH_SECRET", "proshop-secret")
LOGS_PATH = Path(project_root) / "simulators" / "logs.json"


def _check_auth(request: Request) -> JSONResponse | None:
    """Check auth header. Returns error response or None if OK."""
    auth = request.headers.get("x-auth", "")
    if auth != AUTH_SECRET:
        return JSONResponse(
            {"error": "UNAUTHORIZED", "message": "Invalid or missing x-auth header"},
            status_code=401,
        )
    return None


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "proshop-feature-flags-rest"})


async def features_list(request: Request) -> JSONResponse:
    return JSONResponse(list_features())


async def feature_get(request: Request) -> JSONResponse:
    name = request.path_params["name"]
    return JSONResponse(get_feature_info(name))


async def feature_set_state(request: Request) -> JSONResponse:
    auth_err = _check_auth(request)
    if auth_err:
        return auth_err

    name = request.path_params["name"]
    body = await request.json()

    state = body.get("state")
    if state not in ("Enabled", "Disabled", "Testing"):
        return JSONResponse(
            {
                "error": "INVALID_STATE",
                "message": f"State must be Enabled, Disabled, or Testing. Got: {state!r}",
            },
            status_code=400,
        )

    result = set_feature_state(feature_name=name, state=state)

    if "error" in result:
        return JSONResponse(result, status_code=400)

    # Format agent message
    msg = f"Готово, фича {name} переведена в {state}"
    if result.get("warnings"):
        msg += f" (warnings: {'; '.join(result['warnings'])})"

    return JSONResponse({"success": True, "message": msg, "data": result})


async def feature_set_traffic(request: Request) -> JSONResponse:
    auth_err = _check_auth(request)
    if auth_err:
        return auth_err

    name = request.path_params["name"]
    body = await request.json()

    percentage = body.get("percentage")

    # Algorithm-before-AI: strict validation
    if not isinstance(percentage, int) or isinstance(percentage, bool):
        return JSONResponse(
            {
                "error": "INVALID_PERCENTAGE",
                "message": f"percentage must be an integer. Got: {percentage!r}",
            },
            status_code=400,
        )

    if percentage < 0 or percentage > 100:
        return JSONResponse(
            {
                "error": "INVALID_PERCENTAGE",
                "message": f"percentage must be between 0 and 100. Got: {percentage}",
            },
            status_code=400,
        )

    result = adjust_traffic_rollout(feature_name=name, percentage=percentage)

    if "error" in result:
        return JSONResponse(result, status_code=400)

    msg = f"Готово, traffic для {name} установлен на {percentage}%"
    if result.get("hint"):
        msg += f" (hint: {result['hint']})"

    return JSONResponse({"success": True, "message": msg, "data": result})


async def logs_get(request: Request) -> JSONResponse:
    try:
        raw = LOGS_PATH.read_text(encoding="utf-8").strip()
        logs = json.loads(raw) if raw else []
    except FileNotFoundError:
        logs = []
    return JSONResponse({"total": len(logs), "logs": logs})


routes = [
    Route("/health", health),
    Route("/api/features", features_list),
    Route("/api/features/{name}", feature_get),
    Route("/api/features/{name}/state", feature_set_state, methods=["POST"]),
    Route("/api/features/{name}/traffic", feature_set_traffic, methods=["POST"]),
    Route("/api/logs", logs_get),
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    import uvicorn
    print(f"REST API server starting on {HOST}:{PORT}")
    print(f"Endpoints:")
    print(f"  GET  /health")
    print(f"  GET  /api/features")
    print(f"  GET  /api/features/:name")
    print(f"  POST /api/features/:name/state   {{state: ...}}")
    print(f"  POST /api/features/:name/traffic {{percentage: ...}}")
    print(f"Auth: x-auth header = {AUTH_SECRET}")
    print(f"  GET  /api/logs")
    uvicorn.run(app, host=HOST, port=PORT)
