"""
Shared fixtures for mcp-feature-flags tests.

Provides:
  - sample_flags: realistic feature flag dict matching backend/features.json
  - tmp_flags_file: writes sample_flags to a temp JSON file via tmp_path
  - patch_features_json: monkeypatches server.FEATURES_JSON to the temp file
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Realistic test data (subset of real features.json entries)
# ---------------------------------------------------------------------------

SAMPLE_FLAGS = {
    "search_v2": {
        "name": "New Search Algorithm",
        "description": "Replaces legacy regex-based keyword matching with a hybrid BM25 + TF-IDF ranking pipeline.",
        "status": "Testing",
        "traffic_percentage": 100,
        "last_modified": "2026-06-02T15:40:24.806Z",
        "targeted_segments": ["beta_users", "internal"],
        "rollout_strategy": "canary",
    },
    "semantic_search": {
        "name": "Semantic Vector Search",
        "description": "Augments keyword search with embedding-based semantic similarity.",
        "status": "Enabled",
        "traffic_percentage": 100,
        "last_modified": "2026-06-02T15:39:17.439Z",
        "targeted_segments": ["internal"],
        "rollout_strategy": "canary",
        "dependencies": ["search_v2"],
    },
    "save_for_later": {
        "name": "Save Items for Later",
        "description": "Adds a 'Save for Later' action on cart items.",
        "status": "Disabled",
        "traffic_percentage": 0,
        "last_modified": "2026-02-28",
        "targeted_segments": ["authenticated"],
        "rollout_strategy": "canary",
        "dependencies": ["cart_redesign"],
    },
    "cart_redesign": {
        "name": "Redesigned Cart UI",
        "description": "Replaces the current two-column CartScreen layout with a streamlined single-page cart.",
        "status": "Enabled",
        "traffic_percentage": 100,
        "last_modified": "2026-06-02",
        "targeted_segments": ["beta_users"],
        "rollout_strategy": "ab_test",
    },
    "multi_step_checkout_v2": {
        "name": "Redesigned Multi-Step Checkout",
        "description": "Replaces the current 4-step linear checkout with a validated stepper.",
        "status": "Testing",
        "traffic_percentage": 20,
        "last_modified": "2026-04-10",
        "targeted_segments": ["all"],
        "rollout_strategy": "ab_test",
    },
    "gift_message": {
        "name": "Gift Message at Checkout",
        "description": "Adds an optional gift message textarea on the PlaceOrderScreen.",
        "status": "Disabled",
        "traffic_percentage": 0,
        "last_modified": "2026-02-20",
        "targeted_segments": ["all"],
        "rollout_strategy": "full_release",
    },
    "admin_bulk_actions": {
        "name": "Bulk Product Actions in Admin",
        "description": "Adds checkboxes to the admin ProductListScreen for batch operations.",
        "status": "Disabled",
        "traffic_percentage": 0,
        "last_modified": "2026-03-14",
        "targeted_segments": ["admin"],
        "rollout_strategy": "full_release",
        "dependencies": ["admin_dashboard_v2"],
    },
    # Feature with dependency pointing to non-existent feature
    "photo_reviews": {
        "name": "Photo Attachments in Reviews",
        "description": "Allows customers to attach up to 3 photos when submitting a product review.",
        "status": "Disabled",
        "traffic_percentage": 0,
        "last_modified": "2026-03-02",
        "targeted_segments": ["authenticated"],
        "rollout_strategy": "canary",
        "dependencies": ["reviews_moderation"],
    },
    # Feature with no dependencies at all
    "dark_mode": {
        "name": "Dark Mode Theme",
        "description": "Adds a theme toggle to the Header component that switches between light and dark palette.",
        "status": "Enabled",
        "traffic_percentage": 100,
        "last_modified": "2026-06-02",
        "targeted_segments": ["all"],
        "rollout_strategy": "ab_test",
    },
    "stripe_alternative": {
        "name": "Stripe as Alternative Payment Processor",
        "description": "Enables the Stripe payment method option.",
        "status": "Testing",
        "traffic_percentage": 25,
        "last_modified": "2026-05-10",
        "targeted_segments": ["beta_users"],
        "rollout_strategy": "canary",
    },
}


@pytest.fixture()
def sample_flags() -> dict:
    """Return a deep copy of the realistic sample flags dict."""
    return json.loads(json.dumps(SAMPLE_FLAGS))


@pytest.fixture()
def tmp_flags_file(tmp_path: Path, sample_flags: dict) -> Path:
    """Write sample_flags to a temp JSON file and return its Path."""
    fp = tmp_path / "features.json"
    fp.write_text(json.dumps(sample_flags, indent=2, ensure_ascii=False), encoding="utf-8")
    return fp


@pytest.fixture()
def patch_features_json(tmp_flags_file: Path):
    """
    Monkeypatch server.FEATURES_JSON so all tool functions
    read from / write to the temp file instead of the real one.
    Yields the temp file Path so tests can re-read it.
    """
    import sys
    mcp_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags")
    if mcp_dir not in sys.path:
        sys.path.insert(0, mcp_dir)
    import server as mod

    with patch.object(mod, "FEATURES_JSON", tmp_flags_file):
        yield tmp_flags_file


@pytest.fixture()
def auth_secret():
    """Return the default auth secret used by rest_api."""
    return "proshop-secret"
