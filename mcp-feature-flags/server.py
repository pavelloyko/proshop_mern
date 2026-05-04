"""
Feature Flags MCP Server for ProShop MERN.

Reads and writes backend/features.json. The Express API (GET /api/feature-flags)
reads the same file on every request, so changes made through this MCP server
are immediately visible on the frontend without restart.
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from fastmcp import FastMCP

# Resolve path to features.json — env var overrides default
FEATURES_JSON = Path(
    os.environ.get(
        "FEATURES_JSON_PATH",
        str(Path(__file__).resolve().parent.parent / "backend" / "features.json"),
    )
)

VALID_STATES = {"Disabled", "Testing", "Enabled"}

mcp = FastMCP("proshop-feature-flags")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_flags() -> dict:
    """Read and parse features.json. Raises on file/JSON errors."""
    try:
        raw = FEATURES_JSON.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(
            f"FILE_READ_ERROR: features.json not found at {FEATURES_JSON}. "
            "Ensure the path is correct and the file exists."
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"JSON_PARSE_ERROR: features.json contains invalid JSON — {exc}"
        )


def _write_flags(flags: dict) -> None:
    """Atomic write: write to temp file, then rename over the target."""
    payload = json.dumps(flags, indent=2, ensure_ascii=False) + "\n"
    dir_path = FEATURES_JSON.parent
    try:
        fd, tmp = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, str(FEATURES_JSON))
    except OSError as exc:
        # Clean up temp file if it exists
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise RuntimeError(
            f"FILE_WRITE_ERROR: could not write features.json — {exc}"
        )


def _today() -> str:
    return date.today().isoformat()


def _check_dependencies(flags: dict, feature: dict) -> list[str]:
    """Return warning strings for dependencies that are not Enabled."""
    warnings = []
    for dep_id in feature.get("dependencies", []):
        dep = flags.get(dep_id)
        if dep and dep["status"] != "Enabled":
            warnings.append(
                f"Dependency '{dep_id}' is in status '{dep['status']}', not "
                f"'Enabled'. The feature may not function correctly."
            )
    return warnings


# ---------------------------------------------------------------------------
# Tool 1 — get_feature_info
# ---------------------------------------------------------------------------

@mcp.tool()
def get_feature_info(feature_name: str) -> dict:
    """Retrieve the full current state of a single feature flag, including the
    status of every dependency it declares.

    WHEN TO CALL:
      - The user asks "what is the status of X?" or "tell me about feature X".
      - Before calling set_feature_state or adjust_traffic_rollout, to preview
        the current state and confirm the feature exists.

    WHEN NOT TO CALL:
      - When the user wants a list of ALL features — use list_features instead.
      - When the user wants to CHANGE a feature — use set_feature_state or
        adjust_traffic_rollout.

    EXAMPLES:
      1. get_feature_info(feature_name="dark_mode")
         → returns status, traffic_percentage, dependencies, etc.
      2. get_feature_info(feature_name="semantic_search")
         → returns the flag + a warning that dependency search_v2 is not Enabled.
      3. get_feature_info(feature_name="nonexistent")
         → returns error FEATURE_NOT_FOUND.
    """
    flags = _read_flags()

    feature = flags.get(feature_name)
    if feature is None:
        return {
            "error": "FEATURE_NOT_FOUND",
            "message": f"No feature with ID '{feature_name}' exists in features.json.",
            "feature_id": feature_name,
        }

    result = {"feature_id": feature_name, **feature}

    # Attach dependency states
    deps = feature.get("dependencies", [])
    if deps:
        dep_states = {}
        for dep_id in deps:
            dep = flags.get(dep_id)
            dep_states[dep_id] = dep["status"] if dep else "NOT_FOUND"
        result["dependency_states"] = dep_states

    return result


# ---------------------------------------------------------------------------
# Tool 2 — set_feature_state
# ---------------------------------------------------------------------------

@mcp.tool()
def set_feature_state(feature_name: str, state: str) -> dict:
    """Change the status of a feature flag. Automatically adjusts
    traffic_percentage to the canonical value for the new state and updates
    last_modified.

    traffic_percentage rules:
      - Disabled  → 0
      - Enabled   → 100
      - Testing   → keeps current value if 1–99, otherwise sets to 10

    VALIDATION: If the feature has dependencies and the new state is Testing
    or Enabled, a warning is returned for every dependency that is not Enabled.
    The state change still proceeds — this is a warning, not a block.

    WHEN TO CALL:
      - "Disable stripe — there's a bug."
      - "Enable dark mode for everyone."
      - "Move search_v2 to Testing."

    WHEN NOT TO CALL:
      - To change traffic percentage on a feature already in Testing — use
        adjust_traffic_rollout instead.
      - To query the current state — use get_feature_info.

    EXAMPLES:
      1. set_feature_state(feature_name="stripe_alternative", state="Disabled")
         → sets traffic_percentage to 0, status to Disabled.
      2. set_feature_state(feature_name="search_v2", state="Enabled")
         → sets traffic_percentage to 100, status to Enabled.
      3. set_feature_state(feature_name="semantic_search", state="Testing")
         → sets traffic_percentage to 10 (was 0), warns that search_v2 is not Enabled.
    """
    if state not in VALID_STATES:
        return {
            "error": "INVALID_STATE",
            "message": (
                f"State '{state}' is not valid. "
                f"Must be one of: {', '.join(sorted(VALID_STATES))} (case-sensitive)."
            ),
            "feature_id": feature_name,
        }

    flags = _read_flags()

    feature = flags.get(feature_name)
    if feature is None:
        return {
            "error": "FEATURE_NOT_FOUND",
            "message": f"No feature with ID '{feature_name}' exists in features.json.",
            "feature_id": feature_name,
        }

    # Apply state + canonical traffic_percentage
    feature["status"] = state
    if state == "Disabled":
        feature["traffic_percentage"] = 0
    elif state == "Enabled":
        feature["traffic_percentage"] = 100
    elif state == "Testing":
        current = feature["traffic_percentage"]
        if not (1 <= current <= 99):
            feature["traffic_percentage"] = 10

    feature["last_modified"] = _today()

    # Dependency warnings (only for Testing / Enabled)
    warnings = []
    if state in ("Testing", "Enabled"):
        warnings = _check_dependencies(flags, feature)

    _write_flags(flags)

    result = {"feature_id": feature_name}
    for key in ("name", "status", "traffic_percentage", "last_modified"):
        result[key] = feature[key]
    result["warnings"] = warnings
    return result


# ---------------------------------------------------------------------------
# Tool 3 — adjust_traffic_rollout
# ---------------------------------------------------------------------------

@mcp.tool()
def adjust_traffic_rollout(feature_name: str, percentage: int) -> dict:
    """Change the traffic_percentage of a feature that is currently in Testing
    status. Does NOT change the status itself. Updates last_modified.

    VALIDATION:
      - percentage must be an integer 0–100.
      - Feature status MUST be "Testing". Use set_feature_state first to change
        status to Testing before adjusting rollout.
      - Setting percentage to 0 on a Testing feature is allowed but a hint
        suggests using set_feature_state("Disabled") instead.
      - Setting percentage to 100 on a Testing feature is allowed but a hint
        suggests promoting to Enabled via set_feature_state.

    WHEN TO CALL:
      - "Increase dark_mode rollout from 20% to 50%."
      - "Expand the canary to 75%."
      - "Bump search_autosuggest traffic up."

    WHEN NOT TO CALL:
      - Feature is Disabled or Enabled — use set_feature_state first.
      - You need to change the status itself — use set_feature_state.
      - You want to check the current percentage — use get_feature_info.

    EXAMPLES:
      1. adjust_traffic_rollout(feature_name="dark_mode", percentage=50)
         → traffic_percentage becomes 50.
      2. adjust_traffic_rollout(feature_name="search_v2", percentage=100)
         → traffic_percentage becomes 100, hint suggests promoting to Enabled.
      3. adjust_traffic_rollout(feature_name="paypal_express_buttons", percentage=50)
         → error WRONG_STATUS_FOR_ROLLOUT (feature is Enabled, not Testing).
    """
    if not isinstance(percentage, int) or isinstance(percentage, bool):
        return {
            "error": "INVALID_PERCENTAGE",
            "message": (
                f"percentage must be an integer between 0 and 100. "
                f"Got {percentage!r} ({type(percentage).__name__})."
            ),
            "feature_id": feature_name,
        }

    if percentage < 0 or percentage > 100:
        return {
            "error": "INVALID_PERCENTAGE",
            "message": f"percentage must be between 0 and 100. Got {percentage}.",
            "feature_id": feature_name,
        }

    flags = _read_flags()

    feature = flags.get(feature_name)
    if feature is None:
        return {
            "error": "FEATURE_NOT_FOUND",
            "message": f"No feature with ID '{feature_name}' exists in features.json.",
            "feature_id": feature_name,
        }

    if feature["status"] != "Testing":
        return {
            "error": "WRONG_STATUS_FOR_ROLLOUT",
            "message": (
                f"adjust_traffic_rollout can only be called on features with status "
                f"'Testing'. '{feature_name}' is currently '{feature['status']}'. "
                f"Use set_feature_state to change its status first."
            ),
            "feature_id": feature_name,
        }

    feature["traffic_percentage"] = percentage
    feature["last_modified"] = _today()

    # Hints
    hint = None
    if percentage == 0:
        hint = (
            "traffic_percentage is 0. Consider using "
            "set_feature_state(feature_name, 'Disabled') instead — "
            "it sets status to Disabled and traffic to 0 in one step."
        )
    elif percentage == 100:
        hint = (
            "traffic_percentage is 100. Consider promoting with "
            "set_feature_state(feature_name, 'Enabled') to lock in the rollout."
        )

    _write_flags(flags)

    return {
        "feature_id": feature_name,
        "name": feature["name"],
        "status": feature["status"],
        "traffic_percentage": percentage,
        "last_modified": feature["last_modified"],
        "hint": hint,
    }


# ---------------------------------------------------------------------------
# Tool 4 — list_features
# ---------------------------------------------------------------------------

@mcp.tool()
def list_features() -> dict:
    """Return a summary list of ALL feature flags: name, status, and
    traffic_percentage. Use this as the starting point when the user asks "show
    me all features", "which features are in Testing?", or "give me an overview".

    WHEN TO CALL:
      - "Show me all feature flags."
      - "Which features are currently in Testing?"
      - "Give me an overview of feature flag states."
      - At the start of a conversation about feature management, to orient
        the user.

    WHEN NOT TO CALL:
      - When the user asks about a SPECIFIC feature — use get_feature_info.
      - When the user wants to CHANGE a feature — use set_feature_state or
        adjust_traffic_rollout.

    EXAMPLES:
      1. list_features()
         → returns all 25 flags with name, status, traffic_percentage.
      2. "Which features are being tested?"
         → call list_features() first, then filter by status="Testing".
      3. "How many features are fully enabled?"
         → call list_features() to get the full picture.
    """
    flags = _read_flags()

    features = []
    for fid, obj in flags.items():
        features.append({
            "feature_id": fid,
            "name": obj["name"],
            "status": obj["status"],
            "traffic_percentage": obj["traffic_percentage"],
        })

    return {"total": len(features), "features": features}


if __name__ == "__main__":
    mcp.run()
