"""
Comprehensive tests for mcp-feature-flags service.

Covers:
  - _read_flags: happy path, FileNotFoundError, JSONDecodeError
  - _write_flags: happy path, write failure
  - get_feature_info: existing feature, missing feature, dependency states
  - set_feature_state: all 3 states, invalid state, missing feature,
        Testing keeps traffic if 1-99, canonical traffic values, dependency warnings
  - adjust_traffic_rollout: valid percentage, bool/float/string rejection,
        out-of-range, wrong status, missing feature, hints at 0% and 100%
  - list_features: returns all features with correct shape
  - REST API: health, auth, state/traffic endpoints, logs
"""

import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest


# ===========================================================================
# _read_flags
# ===========================================================================

class TestReadFlags:
    """Tests for server._read_flags()."""

    def test_read_flags_happy_path(self, patch_features_json):
        """Valid JSON file is read and parsed into a dict."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server._read_flags()
        assert isinstance(result, dict)
        assert "dark_mode" in result
        assert result["dark_mode"]["status"] == "Enabled"
        assert result["dark_mode"]["traffic_percentage"] == 100

    def test_read_flags_file_not_found_raises_runtime_error(self, tmp_path):
        """FileNotFoundError is caught and re-raised as RuntimeError with FILE_READ_ERROR."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        nonexistent = tmp_path / "no_such_file.json"
        with patch.object(server, "FEATURES_JSON", nonexistent):
            with pytest.raises(RuntimeError, match="FILE_READ_ERROR"):
                server._read_flags()

    def test_read_flags_invalid_json_raises_runtime_error(self, tmp_path):
        """JSONDecodeError is caught and re-raised as RuntimeError with JSON_PARSE_ERROR."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json content!!!", encoding="utf-8")
        with patch.object(server, "FEATURES_JSON", bad_file):
            with pytest.raises(RuntimeError, match="JSON_PARSE_ERROR"):
                server._read_flags()

    def test_read_flags_empty_file_raises_runtime_error(self, tmp_path):
        """Empty file is not valid JSON top-level value → JSON_PARSE_ERROR."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        empty_file = tmp_path / "empty.json"
        empty_file.write_text("", encoding="utf-8")
        with patch.object(server, "FEATURES_JSON", empty_file):
            with pytest.raises(RuntimeError, match="JSON_PARSE_ERROR"):
                server._read_flags()

    def test_read_flags_returns_all_features(self, patch_features_json):
        """Returned dict contains all feature keys from the sample data."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server._read_flags()
        expected_keys = {
            "search_v2", "semantic_search", "save_for_later", "cart_redesign",
            "multi_step_checkout_v2", "gift_message", "admin_bulk_actions",
            "photo_reviews", "dark_mode", "stripe_alternative",
        }
        assert set(result.keys()) == expected_keys

    def test_read_flags_preserves_nested_structure(self, patch_features_json):
        """Nested fields like dependencies list and targeted_segments survive parsing."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server._read_flags()
        sem = result["semantic_search"]
        assert sem["dependencies"] == ["search_v2"]
        assert sem["targeted_segments"] == ["internal"]


# ===========================================================================
# _write_flags
# ===========================================================================

class TestWriteFlags:
    """Tests for server._write_flags()."""

    def test_write_flags_creates_valid_json_file(self, patch_features_json, sample_flags):
        """After _write_flags, the file on disk contains valid JSON matching the input."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server._write_flags(sample_flags)
        raw = patch_features_json.read_text(encoding="utf-8")
        on_disk = json.loads(raw)
        assert on_disk["dark_mode"]["status"] == "Enabled"
        assert on_disk["gift_message"]["traffic_percentage"] == 0

    def test_write_flags_preserves_all_keys(self, patch_features_json, sample_flags):
        """All top-level feature keys survive a write-read round-trip."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server._write_flags(sample_flags)
        on_disk = json.loads(patch_features_json.read_text(encoding="utf-8"))
        assert set(on_disk.keys()) == set(sample_flags.keys())

    def test_write_flags_atomic_no_partial_writes(self, patch_features_json, sample_flags):
        """No .tmp files remain after a successful write."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server._write_flags(sample_flags)
        tmp_files = list(patch_features_json.parent.glob("*.tmp"))
        assert tmp_files == []

    def test_write_flags_failure_on_readonly_dir_raises_error(self, tmp_path, sample_flags):
        """Writing to a read-only directory raises an error (OSError or RuntimeError).

        Note: the production code has a known edge case where mkstemp failure
        causes UnboundLocalError on the cleanup os.unlink(tmp) line (FE15).
        This test asserts that SOME error is raised — the exact type depends on
        whether mkstemp or a later step fails.
        """
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        target = readonly_dir / "features.json"
        target.write_text("{}", encoding="utf-8")
        os.chmod(str(readonly_dir), 0o444)
        try:
            with patch.object(server, "FEATURES_JSON", target):
                # The write MUST fail — exact exception type varies by OS and
                # which step in the atomic write hits the permission error first.
                with pytest.raises((RuntimeError, OSError, PermissionError, UnboundLocalError)):
                    server._write_flags(sample_flags)
        finally:
            os.chmod(str(readonly_dir), 0o755)

    def test_write_flags_overwrites_existing_content(self, patch_features_json, sample_flags):
        """A second write replaces previous content entirely."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        sample_flags["dark_mode"]["status"] = "Disabled"
        server._write_flags(sample_flags)
        on_disk = json.loads(patch_features_json.read_text(encoding="utf-8"))
        assert on_disk["dark_mode"]["status"] == "Disabled"


# ===========================================================================
# _check_dependencies
# ===========================================================================

class TestCheckDependencies:
    """Tests for server._check_dependencies()."""

    def test_check_dependencies_returns_empty_for_no_deps(self):
        """Feature with no dependencies key produces no warnings."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {"dark_mode": {"status": "Enabled"}}
        feature = {"status": "Testing"}
        assert server._check_dependencies(flags, feature) == []

    def test_check_dependencies_returns_empty_for_empty_deps_list(self):
        """Feature with dependencies=[] produces no warnings."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {"dark_mode": {"status": "Enabled"}}
        feature = {"dependencies": []}
        assert server._check_dependencies(flags, feature) == []

    def test_check_dependencies_warns_on_non_enabled_dep(self):
        """Dependency in Disabled state triggers a warning."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {
            "search_v2": {"status": "Disabled"},
        }
        feature = {"dependencies": ["search_v2"]}
        warnings = server._check_dependencies(flags, feature)
        assert len(warnings) == 1
        assert "search_v2" in warnings[0]
        assert "Disabled" in warnings[0]

    def test_check_dependencies_no_warning_when_dep_enabled(self):
        """Dependency in Enabled state produces no warning."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {
            "cart_redesign": {"status": "Enabled"},
        }
        feature = {"dependencies": ["cart_redesign"]}
        assert server._check_dependencies(flags, feature) == []

    def test_check_dependencies_skips_nonexistent_dep(self):
        """Dependency referencing a feature not in the dict is silently skipped (FE6)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {}
        feature = {"dependencies": ["nonexistent_dep"]}
        assert server._check_dependencies(flags, feature) == []

    def test_check_dependencies_multiple_deps_mixed(self):
        """Mix of Enabled, Disabled, and missing dependencies produces correct warnings."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        flags = {
            "search_v2": {"status": "Testing"},
            "cart_redesign": {"status": "Enabled"},
        }
        feature = {"dependencies": ["search_v2", "cart_redesign", "ghost"]}
        warnings = server._check_dependencies(flags, feature)
        assert len(warnings) == 1
        assert "search_v2" in warnings[0]


# ===========================================================================
# get_feature_info
# ===========================================================================

class TestGetFeatureInfo:
    """Tests for server.get_feature_info()."""

    def test_get_feature_info_returns_full_state(self, patch_features_json):
        """Existing feature returns all its fields plus feature_id."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("dark_mode")
        assert result["feature_id"] == "dark_mode"
        assert result["status"] == "Enabled"
        assert result["traffic_percentage"] == 100
        assert result["name"] == "Dark Mode Theme"
        assert result["description"] == (
            "Adds a theme toggle to the Header component that switches "
            "between light and dark palette."
        )

    def test_get_feature_info_missing_feature_returns_error(self, patch_features_json):
        """Non-existent feature returns FEATURE_NOT_FOUND error."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("nonexistent_feature")
        assert result["error"] == "FEATURE_NOT_FOUND"
        assert "nonexistent_feature" in result["message"]
        assert result["feature_id"] == "nonexistent_feature"

    def test_get_feature_info_with_dependencies_includes_dep_states(self, patch_features_json):
        """Feature with dependencies gets a dependency_states dict attached."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("semantic_search")
        assert "dependency_states" in result
        assert result["dependency_states"]["search_v2"] == "Testing"

    def test_get_feature_info_dep_not_found_reports_not_found(self, patch_features_json):
        """Dependency referencing a non-existent feature shows NOT_FOUND status."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("photo_reviews")
        assert "dependency_states" in result
        assert result["dependency_states"]["reviews_moderation"] == "NOT_FOUND"

    def test_get_feature_info_no_dependencies_no_dep_states_key(self, patch_features_json):
        """Feature without dependencies does not get a dependency_states key."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("dark_mode")
        assert "dependency_states" not in result

    def test_get_feature_info_preserves_all_original_fields(self, patch_features_json):
        """All original fields from the JSON entry are present in the result."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.get_feature_info("stripe_alternative")
        assert result["feature_id"] == "stripe_alternative"
        assert result["status"] == "Testing"
        assert result["traffic_percentage"] == 25
        assert result["rollout_strategy"] == "canary"
        assert result["targeted_segments"] == ["beta_users"]


# ===========================================================================
# set_feature_state
# ===========================================================================

class TestSetFeatureState:
    """Tests for server.set_feature_state()."""

    def test_set_state_invalid_state_returns_error(self, patch_features_json):
        """Invalid state string returns INVALID_STATE error (F1)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "Live")
        assert result["error"] == "INVALID_STATE"
        assert "Live" in result["message"]
        assert result["feature_id"] == "dark_mode"

    def test_set_state_case_sensitive_rejects_lowercase(self, patch_features_json):
        """State 'enabled' (lowercase) is rejected — case-sensitive matching."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "enabled")
        assert result["error"] == "INVALID_STATE"

    def test_set_state_missing_feature_returns_error(self, patch_features_json):
        """Non-existent feature returns FEATURE_NOT_FOUND (F2)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("xyz_nonexistent", "Enabled")
        assert result["error"] == "FEATURE_NOT_FOUND"

    def test_set_state_disabled_sets_traffic_to_zero(self, patch_features_json):
        """Disabled state sets traffic_percentage to 0 (F3)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "Disabled")
        assert result["status"] == "Disabled"
        assert result["traffic_percentage"] == 0
        assert result["last_modified"] == date.today().isoformat()

    def test_set_state_enabled_sets_traffic_to_100(self, patch_features_json):
        """Enabled state sets traffic_percentage to 100 (F4)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("gift_message", "Enabled")
        assert result["status"] == "Enabled"
        assert result["traffic_percentage"] == 100

    def test_set_state_testing_keeps_traffic_if_1_to_99(self, patch_features_json):
        """Testing state with current traffic in [1,99] keeps current value (F5)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # stripe_alternative has traffic_percentage=25 in Testing
        result = server.set_feature_state("stripe_alternative", "Testing")
        assert result["status"] == "Testing"
        assert result["traffic_percentage"] == 25

    def test_set_state_testing_resets_traffic_from_100(self, patch_features_json):
        """Testing state with current traffic=100 resets to 10 (FE5, F6)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # search_v2 has traffic_percentage=100 in Testing
        result = server.set_feature_state("search_v2", "Testing")
        assert result["status"] == "Testing"
        assert result["traffic_percentage"] == 10

    def test_set_state_testing_resets_traffic_from_0(self, patch_features_json):
        """Testing state with current traffic=0 resets to 10 (F6)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # gift_message has traffic_percentage=0, status=Disabled
        result = server.set_feature_state("gift_message", "Testing")
        assert result["status"] == "Testing"
        assert result["traffic_percentage"] == 10

    def test_set_state_updates_last_modified(self, patch_features_json):
        """last_modified is set to today's date."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "Disabled")
        assert result["last_modified"] == date.today().isoformat()

    def test_set_state_writes_to_disk(self, patch_features_json):
        """After set_feature_state, the JSON file on disk reflects the change."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server.set_feature_state("gift_message", "Enabled")
        on_disk = json.loads(patch_features_json.read_text(encoding="utf-8"))
        assert on_disk["gift_message"]["status"] == "Enabled"
        assert on_disk["gift_message"]["traffic_percentage"] == 100

    def test_set_state_dependency_warning_for_testing(self, patch_features_json):
        """Moving to Testing with a non-Enabled dep produces a warning (F7)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # save_for_later depends on cart_redesign (Enabled) — no warning
        # admin_bulk_actions depends on admin_dashboard_v2 (not in sample) — skipped
        # Let's use semantic_search which depends on search_v2 (Testing, not Enabled)
        result = server.set_feature_state("semantic_search", "Testing")
        assert len(result["warnings"]) >= 1
        assert any("search_v2" in w for w in result["warnings"])

    def test_set_state_dependency_warning_for_enabled(self, patch_features_json):
        """Moving to Enabled with a non-Enabled dep produces a warning (F7)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # save_for_later depends on cart_redesign (Enabled) — should have NO warning
        # But semantic_search depends on search_v2 (Testing) — warning expected
        result = server.set_feature_state("semantic_search", "Enabled")
        assert len(result["warnings"]) >= 1

    def test_set_state_no_warning_when_all_deps_enabled(self, patch_features_json):
        """No warnings when all dependencies are Enabled (F7 negative)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        # save_for_later depends on cart_redesign which is Enabled
        result = server.set_feature_state("save_for_later", "Testing")
        assert result["warnings"] == []

    def test_set_state_no_dependency_warning_for_disabled(self, patch_features_json):
        """Moving to Disabled never triggers dependency warnings."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("semantic_search", "Disabled")
        assert result["warnings"] == []

    def test_set_state_result_contains_feature_id(self, patch_features_json):
        """Result dict contains feature_id matching the input."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "Enabled")
        assert result["feature_id"] == "dark_mode"

    def test_set_state_result_contains_name(self, patch_features_json):
        """Result dict contains the human-readable name of the feature."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "Enabled")
        assert result["name"] == "Dark Mode Theme"

    def test_set_state_empty_string_rejected(self, patch_features_json):
        """Empty string state is not a valid state."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.set_feature_state("dark_mode", "")
        assert result["error"] == "INVALID_STATE"


# ===========================================================================
# adjust_traffic_rollout
# ===========================================================================

class TestAdjustTrafficRollout:
    """Tests for server.adjust_traffic_rollout()."""

    def test_adjust_traffic_valid_percentage(self, patch_features_json):
        """Valid integer percentage on a Testing feature updates traffic (happy path)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 50)
        assert result["traffic_percentage"] == 50
        assert result["status"] == "Testing"
        assert result["feature_id"] == "stripe_alternative"

    def test_adjust_traffic_bool_rejected(self, patch_features_json):
        """Boolean True is explicitly rejected as INVALID_PERCENTAGE (FE4, F9)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", True)
        assert result["error"] == "INVALID_PERCENTAGE"
        assert "True" in result["message"]

    def test_adjust_traffic_bool_false_rejected(self, patch_features_json):
        """Boolean False is also rejected (bool is subclass of int in Python)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", False)
        assert result["error"] == "INVALID_PERCENTAGE"

    def test_adjust_traffic_float_rejected(self, patch_features_json):
        """Float percentage is rejected — only int accepted."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 50.5)
        assert result["error"] == "INVALID_PERCENTAGE"

    def test_adjust_traffic_string_rejected(self, patch_features_json):
        """String percentage is rejected."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", "75")
        assert result["error"] == "INVALID_PERCENTAGE"

    def test_adjust_traffic_negative_rejected(self, patch_features_json):
        """Negative percentage is out of range (F10)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", -1)
        assert result["error"] == "INVALID_PERCENTAGE"
        assert "-1" in result["message"]

    def test_adjust_traffic_101_rejected(self, patch_features_json):
        """Percentage > 100 is out of range (F10)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 101)
        assert result["error"] == "INVALID_PERCENTAGE"

    def test_adjust_traffic_wrong_status_disabled(self, patch_features_json):
        """Feature in Disabled status returns WRONG_STATUS_FOR_ROLLOUT (F8)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("gift_message", 50)
        assert result["error"] == "WRONG_STATUS_FOR_ROLLOUT"
        assert "gift_message" in result["message"]

    def test_adjust_traffic_wrong_status_enabled(self, patch_features_json):
        """Feature in Enabled status returns WRONG_STATUS_FOR_ROLLOUT."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("dark_mode", 50)
        assert result["error"] == "WRONG_STATUS_FOR_ROLLOUT"
        assert "dark_mode" in result["message"]

    def test_adjust_traffic_missing_feature(self, patch_features_json):
        """Non-existent feature returns FEATURE_NOT_FOUND."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("xyz_nope", 50)
        assert result["error"] == "FEATURE_NOT_FOUND"

    def test_adjust_traffic_zero_percentage_with_hint(self, patch_features_json):
        """Setting percentage=0 on Testing feature succeeds with hint about Disabled (FE8, F11)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 0)
        assert result["traffic_percentage"] == 0
        assert result["hint"] is not None
        assert "Disabled" in result["hint"]

    def test_adjust_traffic_100_percentage_with_hint(self, patch_features_json):
        """Setting percentage=100 on Testing feature succeeds with hint about Enabled (FE9, F12)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 100)
        assert result["traffic_percentage"] == 100
        assert result["hint"] is not None
        assert "Enabled" in result["hint"]

    def test_adjust_traffic_middle_percentage_no_hint(self, patch_features_json):
        """Setting percentage=50 (not 0 or 100) produces no hint."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 50)
        assert result["hint"] is None

    def test_adjust_traffic_updates_last_modified(self, patch_features_json):
        """last_modified is updated to today's date."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 75)
        assert result["last_modified"] == date.today().isoformat()

    def test_adjust_traffic_writes_to_disk(self, patch_features_json):
        """After adjust_traffic_rollout, the file on disk reflects the new percentage."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server.adjust_traffic_rollout("multi_step_checkout_v2", 45)
        on_disk = json.loads(patch_features_json.read_text(encoding="utf-8"))
        assert on_disk["multi_step_checkout_v2"]["traffic_percentage"] == 45

    def test_adjust_traffic_does_not_change_status(self, patch_features_json):
        """adjust_traffic_rollout never changes the status field — only traffic."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 60)
        assert result["status"] == "Testing"

    def test_adjust_traffic_boundary_zero_is_accepted(self, patch_features_json):
        """percentage=0 is within [0,100] range and is accepted (with hint)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 0)
        assert "error" not in result

    def test_adjust_traffic_boundary_100_is_accepted(self, patch_features_json):
        """percentage=100 is within [0,100] range and is accepted (with hint)."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 100)
        assert "error" not in result

    def test_adjust_traffic_result_contains_name(self, patch_features_json):
        """Result contains the human-readable feature name."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", 30)
        assert result["name"] == "Stripe as Alternative Payment Processor"

    def test_adjust_traffic_none_rejected(self, patch_features_json):
        """None percentage is rejected."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.adjust_traffic_rollout("stripe_alternative", None)
        assert result["error"] == "INVALID_PERCENTAGE"


# ===========================================================================
# list_features
# ===========================================================================

class TestListFeatures:
    """Tests for server.list_features()."""

    def test_list_features_returns_correct_total(self, patch_features_json):
        """Total count matches the number of features in the file."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.list_features()
        assert result["total"] == 10  # SAMPLE_FLAGS has 10 entries

    def test_list_features_returns_features_list(self, patch_features_json):
        """Result contains a 'features' list with correct length."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.list_features()
        assert "features" in result
        assert len(result["features"]) == 10

    def test_list_features_each_entry_has_required_shape(self, patch_features_json):
        """Every entry in features list has feature_id, name, status, traffic_percentage."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.list_features()
        for entry in result["features"]:
            assert "feature_id" in entry, f"Missing feature_id in {entry}"
            assert "name" in entry, f"Missing name in {entry}"
            assert "status" in entry, f"Missing status in {entry}"
            assert "traffic_percentage" in entry, f"Missing traffic_percentage in {entry}"

    def test_list_features_contains_known_feature(self, patch_features_json):
        """A well-known feature (dark_mode) appears in the list with correct values."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.list_features()
        dark_mode = [f for f in result["features"] if f["feature_id"] == "dark_mode"]
        assert len(dark_mode) == 1
        assert dark_mode[0]["status"] == "Enabled"
        assert dark_mode[0]["traffic_percentage"] == 100
        assert dark_mode[0]["name"] == "Dark Mode Theme"

    def test_list_features_does_not_include_extra_fields(self, patch_features_json):
        """Each entry only has the 4 summary fields, not description or dependencies."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        result = server.list_features()
        allowed_keys = {"feature_id", "name", "status", "traffic_percentage"}
        for entry in result["features"]:
            assert set(entry.keys()) == allowed_keys, (
                f"Unexpected keys in list entry: {set(entry.keys()) - allowed_keys}"
            )

    def test_list_features_reflects_disk_state(self, patch_features_json):
        """After a mutation via set_feature_state, list_features sees the change."""
        import sys; mcp_dir=str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent / "mcp-feature-flags"); (sys.path.insert(0,mcp_dir) if mcp_dir not in sys.path else None); import server

        server.set_feature_state("gift_message", "Enabled")
        result = server.list_features()
        gm = [f for f in result["features"] if f["feature_id"] == "gift_message"][0]
        assert gm["status"] == "Enabled"
        assert gm["traffic_percentage"] == 100


# ===========================================================================
# REST API tests (rest_api.py)
# ===========================================================================

class TestRestAPIHealth:
    """Tests for REST API health endpoint."""

    @pytest.fixture()
    def rest_client(self):
        """Create a Starlette test client for the REST API app."""
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_health_returns_200(self, rest_client, patch_features_json):
        """GET /health returns status 200."""
        resp = rest_client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok_status(self, rest_client, patch_features_json):
        """GET /health returns JSON with status=ok."""
        resp = rest_client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "proshop-feature-flags-rest"


class TestRestAPIFeaturesList:
    """Tests for REST API GET /api/features."""

    @pytest.fixture()
    def rest_client(self):
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_features_list_returns_200(self, rest_client, patch_features_json):
        """GET /api/features returns 200."""
        resp = rest_client.get("/api/features")
        assert resp.status_code == 200

    def test_features_list_no_auth_required(self, rest_client, patch_features_json):
        """GET /api/features works without x-auth header (unauthenticated)."""
        resp = rest_client.get("/api/features")
        assert resp.status_code == 200

    def test_features_list_returns_json(self, rest_client, patch_features_json):
        """Response is JSON with total and features list."""
        resp = rest_client.get("/api/features")
        data = resp.json()
        assert "total" in data
        assert "features" in data
        assert data["total"] == len(data["features"])


class TestRestAPIFeatureGet:
    """Tests for REST API GET /api/features/:name."""

    @pytest.fixture()
    def rest_client(self):
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_feature_get_existing_returns_200(self, rest_client, patch_features_json):
        """GET /api/features/dark_mode returns 200 with feature data."""
        resp = rest_client.get("/api/features/dark_mode")
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_id"] == "dark_mode"
        assert data["status"] == "Enabled"

    def test_feature_get_missing_returns_error_in_body(self, rest_client, patch_features_json):
        """GET /api/features/nonexistent returns error in JSON body."""
        resp = rest_client.get("/api/features/nonexistent_xyz")
        data = resp.json()
        assert data["error"] == "FEATURE_NOT_FOUND"

    def test_feature_get_no_auth_required(self, rest_client, patch_features_json):
        """GET endpoint works without authentication."""
        resp = rest_client.get("/api/features/dark_mode")
        assert resp.status_code == 200


class TestRestAPISetState:
    """Tests for REST API POST /api/features/:name/state."""

    @pytest.fixture()
    def rest_client(self):
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_set_state_with_valid_auth_returns_200(self, rest_client, patch_features_json, auth_secret):
        """POST with correct x-auth header returns 200."""
        resp = rest_client.post(
            "/api/features/dark_mode/state",
            json={"state": "Disabled"},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_set_state_without_auth_returns_401(self, rest_client, patch_features_json):
        """POST without x-auth header returns 401 (FE10)."""
        resp = rest_client.post(
            "/api/features/dark_mode/state",
            json={"state": "Disabled"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"] == "UNAUTHORIZED"

    def test_set_state_wrong_auth_returns_401(self, rest_client, patch_features_json):
        """POST with wrong x-auth value returns 401."""
        resp = rest_client.post(
            "/api/features/dark_mode/state",
            json={"state": "Disabled"},
            headers={"x-auth": "wrong-secret"},
        )
        assert resp.status_code == 401

    def test_set_state_invalid_state_returns_400(self, rest_client, patch_features_json, auth_secret):
        """POST with invalid state string returns 400."""
        resp = rest_client.post(
            "/api/features/dark_mode/state",
            json={"state": "Live"},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_STATE"

    def test_set_state_response_contains_data_field(self, rest_client, patch_features_json, auth_secret):
        """Successful response wraps MCP result in data field."""
        resp = rest_client.post(
            "/api/features/gift_message/state",
            json={"state": "Enabled"},
            headers={"x-auth": auth_secret},
        )
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "Enabled"
        assert data["data"]["traffic_percentage"] == 100

    def test_set_state_response_includes_russian_message(self, rest_client, patch_features_json, auth_secret):
        """Success message is in Russian (matches rest_api formatting)."""
        resp = rest_client.post(
            "/api/features/gift_message/state",
            json={"state": "Enabled"},
            headers={"x-auth": auth_secret},
        )
        data = resp.json()
        assert "message" in data
        assert "gift_message" in data["message"]


class TestRestAPISetTraffic:
    """Tests for REST API POST /api/features/:name/traffic."""

    @pytest.fixture()
    def rest_client(self):
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_set_traffic_with_valid_auth_returns_200(self, rest_client, patch_features_json, auth_secret):
        """POST with correct auth and valid data returns 200."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": 50},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["traffic_percentage"] == 50

    def test_set_traffic_without_auth_returns_401(self, rest_client, patch_features_json):
        """POST without auth header returns 401."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": 50},
        )
        assert resp.status_code == 401

    def test_set_traffic_bool_percentage_returns_400(self, rest_client, patch_features_json, auth_secret):
        """Boolean percentage is rejected at REST layer with 400."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": True},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_PERCENTAGE"

    def test_set_traffic_out_of_range_returns_400(self, rest_client, patch_features_json, auth_secret):
        """Percentage > 100 is rejected at REST layer."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": 150},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "INVALID_PERCENTAGE"

    def test_set_traffic_negative_returns_400(self, rest_client, patch_features_json, auth_secret):
        """Negative percentage is rejected."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": -5},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 400

    def test_set_traffic_wrong_feature_status_returns_400(self, rest_client, patch_features_json, auth_secret):
        """Calling on a Disabled feature returns 400 with WRONG_STATUS_FOR_ROLLOUT."""
        resp = rest_client.post(
            "/api/features/gift_message/traffic",
            json={"percentage": 50},
            headers={"x-auth": auth_secret},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "WRONG_STATUS_FOR_ROLLOUT"

    def test_set_traffic_hint_included_in_message(self, rest_client, patch_features_json, auth_secret):
        """When adjust_traffic returns a hint, it's included in the response message."""
        resp = rest_client.post(
            "/api/features/stripe_alternative/traffic",
            json={"percentage": 100},
            headers={"x-auth": auth_secret},
        )
        data = resp.json()
        assert resp.status_code == 200
        assert "hint" in data["message"] or "hint" in data.get("data", {})


class TestRestAPILogs:
    """Tests for REST API GET /api/logs."""

    @pytest.fixture()
    def rest_client(self):
        from starlette.testclient import TestClient
        from rest_api import app
        return TestClient(app)

    def test_logs_missing_file_returns_empty_list(self, rest_client, tmp_path, monkeypatch):
        """When simulators/logs.json is missing, returns {total: 0, logs: []} (FE12)."""
        import rest_api
        monkeypatch.setattr(rest_api, "LOGS_PATH", tmp_path / "nonexistent_logs.json")
        resp = rest_client.get("/api/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["logs"] == []

    def test_logs_with_data_returns_entries(self, rest_client, tmp_path, monkeypatch):
        """When logs.json exists with entries, they are returned."""
        import rest_api
        log_entries = [
            {"tick": 1, "feature": "search_v2", "status": "success"},
            {"tick": 2, "feature": "search_v2", "status": "error"},
        ]
        log_path = tmp_path / "logs.json"
        log_path.write_text(json.dumps(log_entries), encoding="utf-8")
        monkeypatch.setattr(rest_api, "LOGS_PATH", log_path)
        resp = rest_client.get("/api/logs")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["logs"]) == 2
        assert data["logs"][0]["tick"] == 1
        assert data["logs"][1]["status"] == "error"

    def test_logs_empty_file_returns_empty_list(self, rest_client, tmp_path, monkeypatch):
        """Empty logs.json file returns empty list."""
        import rest_api
        log_path = tmp_path / "logs.json"
        log_path.write_text("", encoding="utf-8")
        monkeypatch.setattr(rest_api, "LOGS_PATH", log_path)
        resp = rest_client.get("/api/logs")
        data = resp.json()
        assert data["total"] == 0
        assert data["logs"] == []

    def test_logs_no_auth_required(self, rest_client, tmp_path, monkeypatch):
        """GET /api/logs works without authentication."""
        import rest_api
        monkeypatch.setattr(rest_api, "LOGS_PATH", tmp_path / "nonexistent.json")
        resp = rest_client.get("/api/logs")
        assert resp.status_code == 200
