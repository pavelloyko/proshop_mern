"""
Comprehensive pytest tests for mcp-rag-search/server.py.

Tests cover:
  - _has_cyrillic: Cyrillic detection across various inputs
  - _ru_to_en_query: Russian-to-English dictionary bridging
  - _point_to_chunk: payload-to-chunk conversion with truncation
  - search_project_docs: full search flow with mocked model + Qdrant

All ML / vector DB dependencies are mocked via conftest.py fixtures.
Tests run without GPU, Qdrant, or model downloads.
"""

import pytest

from conftest import _FakeScoredPoint, make_scored_point


# ===================================================================
# _has_cyrillic
# ===================================================================


class TestHasCyrillic:
    """Tests for ``_has_cyrillic(text: str) -> bool``."""

    def test_pure_cyrillic_returns_true(self, server_module):
        assert server_module._has_cyrillic("какие фичи зависят от stripe") is True

    def test_single_cyrillic_char_returns_true(self, server_module):
        assert server_module._has_cyrillic("a") is False
        assert server_module._has_cyrillic("а") is True  # Cyrillic 'а'

    def test_latin_only_returns_false(self, server_module):
        assert server_module._has_cyrillic("checkout incident timeline") is False

    def test_mixed_cyrillic_and_latin_returns_true(self, server_module):
        assert server_module._has_cyrillic("checkout корзина flow") is True

    def test_empty_string_returns_false(self, server_module):
        assert server_module._has_cyrillic("") is False

    def test_special_chars_only_returns_false(self, server_module):
        assert server_module._has_cyrillic("12345 !@#$%") is False

    def test_cyrillic_with_digits_and_punctuation_returns_true(self, server_module):
        assert server_module._has_cyrillic("ADR-001: почему? 100%") is True

    def test_uppercase_cyrillic_returns_true(self, server_module):
        assert server_module._has_cyrillic("МОДЕЛЬ") is True

    def test_yo_character_returns_true(self, server_module):
        assert server_module._has_cyrillic("всё") is True

    def test_german_umlauts_are_latin_not_cyrillic(self, server_module):
        # German umlauts (ä, ö, ü) must NOT trigger Cyrillic detection
        assert server_module._has_cyrillic("Größe Über") is False


# ===================================================================
# _ru_to_en_query
# ===================================================================


class TestRuToEnQuery:
    """Tests for ``_ru_to_en_query(ru_query: str) -> str``."""

    def test_full_russian_query_translates_known_tokens(self, server_module):
        # "какие" -> "which", "фичи" -> "features", "зависят" -> "depend"
        result = server_module._ru_to_en_query("какие фичи зависят от stripe")
        # "от" is not in dictionary, so it gets dropped (Cyrillic, unrecognized)
        assert "which" in result
        assert "features" in result
        assert "depend" in result
        # "stripe" is Latin — preserved as-is
        assert "stripe" in result

    def test_mixed_russian_english_preserves_english_tokens(self, server_module):
        result = server_module._ru_to_en_query("как работает middleware")
        assert "how" in result
        assert "works" in result
        assert "middleware" in result

    def test_unknown_russian_words_are_dropped(self, server_module):
        # "абвгдеж" — not in dictionary, all Cyrillic → dropped entirely
        result = server_module._ru_to_en_query("абвгдеж xyz123")
        assert result == "xyz123"

    def test_all_unknown_russian_produces_empty_string(self, server_module):
        result = server_module._ru_to_en_query("абвгдеж")
        assert result == ""

    def test_empty_string_produces_empty_string(self, server_module):
        result = server_module._ru_to_en_query("")
        assert result == ""

    def test_pure_english_passes_through_unchanged(self, server_module):
        query = "checkout incident timeline"
        result = server_module._ru_to_en_query(query)
        assert result == query

    def test_trailing_punctuation_stripped_before_lookup(self, server_module):
        # "фича!" -> lower="фича!", strip(".,!?;:")="фича" -> "feature"
        result = server_module._ru_to_en_query("фича! фичи, модель.")
        tokens = result.split()
        assert "feature" in tokens
        assert "features" in tokens
        assert "model" in tokens

    def test_russian_tokens_with_multiple_forms_map_correctly(self, server_module):
        # Test that different word forms map to distinct English equivalents
        result_singular = server_module._ru_to_en_query("инцидент")
        assert "incident" == result_singular

        result_plural = server_module._ru_to_en_query("инциденты")
        assert "incidents" == result_plural

    def test_latin_tokens_with_trailing_punctuation_preserved(self, server_module):
        # Latin tokens with punctuation are NOT stripped — they pass through as-is
        result = server_module._ru_to_en_query("stripe! v2,")
        # "stripe!" has punctuation, lower().strip() = "stripe!" — not in dict,
        # not Cyrillic, so it passes through as the original token "stripe!"
        assert "stripe!" in result
        assert "v2," in result

    def test_mixed_script_preserves_only_english_and_translated(self, server_module):
        # "как" -> "how", "настроить" -> "configure", "PayPal" kept, "то" dropped
        result = server_module._ru_to_en_query("как настроить PayPal то")
        assert "how" in result
        assert "configure" in result
        assert "PayPal" in result
        # "то" is not in dictionary, is Cyrillic → dropped
        assert "то" not in result


# ===================================================================
# _point_to_chunk
# ===================================================================


class TestPointToChunk:
    """Tests for ``_point_to_chunk(point) -> dict``."""

    def test_normal_payload_returns_all_fields(self, server_module, sample_point_payload):
        point = make_scored_point(
            point_id=42, score=0.8731, payload=sample_point_payload
        )
        chunk = server_module._point_to_chunk(point)

        assert chunk["source_file"] == "project-data/specs/adr-001-mongodb.md"
        assert chunk["file_path"] == "project-data/specs/adr-001-mongodb.md"
        assert chunk["title"] == "ADR-001: Choose MongoDB"
        assert chunk["parent_headings"] == ["Architecture Decisions", "Database"]
        assert chunk["type"] == "adr"
        assert chunk["score"] == 0.8731
        # Text is under 200 chars — no truncation
        assert "..." not in chunk["snippet"]
        assert chunk["snippet"] == sample_point_payload["text"]

    def test_score_is_rounded_to_four_decimals(self, server_module, sample_point_payload):
        point = make_scored_point(
            point_id=10, score=0.123456789, payload=sample_point_payload
        )
        chunk = server_module._point_to_chunk(point)
        assert chunk["score"] == 0.1235

    def test_long_text_truncated_to_200_chars_with_ellipsis(
        self, server_module, sample_point_payload_long
    ):
        point = make_scored_point(
            point_id=20, score=0.95, payload=sample_point_payload_long
        )
        chunk = server_module._point_to_chunk(point)

        snippet = chunk["snippet"]
        assert snippet.endswith("...")
        # The portion before "..." must be exactly 200 chars
        assert len(snippet) == 203  # 200 chars + "..."
        assert snippet[:200] == sample_point_payload_long["text"][:200]

    def test_short_text_returned_verbatim_without_ellipsis(
        self, server_module, sample_point_payload_short
    ):
        point = make_scored_point(
            point_id=30, score=0.71, payload=sample_point_payload_short
        )
        chunk = server_module._point_to_chunk(point)

        assert chunk["snippet"] == sample_point_payload_short["text"]
        assert not chunk["snippet"].endswith("...")

    def test_missing_text_field_defaults_to_empty_string(self, server_module):
        payload = {
            "source_file": "project-data/specs/empty.md",
            "title": "Empty",
            "type": "doc",
        }
        # No "text" key in payload
        point = make_scored_point(point_id=99, score=0.5, payload=payload)
        chunk = server_module._point_to_chunk(point)

        assert chunk["snippet"] == ""
        assert chunk["source_file"] == "project-data/specs/empty.md"

    def test_missing_optional_fields_default_to_empty(self, server_module):
        payload = {"text": "Some text here."}
        point = make_scored_point(point_id=100, score=0.6, payload=payload)
        chunk = server_module._point_to_chunk(point)

        assert chunk["source_file"] == ""
        assert chunk["file_path"] == ""
        assert chunk["title"] == ""
        assert chunk["parent_headings"] == []
        assert chunk["type"] == ""

    def test_exactly_200_char_text_not_truncated(self, server_module):
        text_exactly_200 = "x" * 200
        payload = {
            "text": text_exactly_200,
            "source_file": "test.md",
            "title": "Boundary",
            "type": "doc",
        }
        point = make_scored_point(point_id=101, score=0.88, payload=payload)
        chunk = server_module._point_to_chunk(point)

        assert chunk["snippet"] == text_exactly_200
        assert not chunk["snippet"].endswith("...")

    def test_201_char_text_is_truncated(self, server_module):
        text_201 = "x" * 201
        payload = {
            "text": text_201,
            "source_file": "test.md",
            "title": "Boundary Over",
            "type": "doc",
        }
        point = make_scored_point(point_id=102, score=0.88, payload=payload)
        chunk = server_module._point_to_chunk(point)

        assert chunk["snippet"].endswith("...")
        assert len(chunk["snippet"]) == 203

    def test_parent_headings_list_preserved(self, server_module):
        headings = ["Level 1", "Level 2", "Level 3", "Deep Nested"]
        payload = {
            "text": "content",
            "source_file": "a.md",
            "title": "T",
            "parent_headings": headings,
            "type": "runbook",
        }
        point = make_scored_point(point_id=103, score=0.92, payload=payload)
        chunk = server_module._point_to_chunk(point)

        assert chunk["parent_headings"] == headings
        assert len(chunk["parent_headings"]) == 4


# ===================================================================
# search_project_docs
# ===================================================================


class TestSearchProjectDocs:
    """Tests for ``search_project_docs(query, top_k, chunk_type) -> dict``."""

    # --- top_k clamping ---

    def test_top_k_zero_clamped_to_one(self, server_module, fake_client):
        payload = {
            "text": "Single result.",
            "source_file": "a.md",
            "title": "A",
            "type": "doc",
        }
        fake_client.set_query_results(
            [make_scored_point(1, 0.9, payload)]
        )
        result = server_module.search_project_docs(query="test", top_k=0)

        assert result["total"] == 1
        assert len(result["chunks"]) == 1

    def test_top_k_hundred_clamped_to_twenty(self, server_module, fake_client):
        # Create 25 fake points — only 20 should be returned (limit from clamping)
        points = [
            make_scored_point(
                i,
                0.9 - i * 0.01,
                {"text": f"Result {i}", "source_file": f"f{i}.md", "title": f"T{i}", "type": "doc"},
            )
            for i in range(25)
        ]
        fake_client.set_query_results(points)
        result = server_module.search_project_docs(query="test", top_k=100)

        assert result["total"] == 20
        assert len(result["chunks"]) == 20

    def test_top_k_negative_clamped_to_one(self, server_module, fake_client):
        payload = {
            "text": "Result.",
            "source_file": "b.md",
            "title": "B",
            "type": "api",
        }
        fake_client.set_query_results(
            [make_scored_point(1, 0.85, payload)]
        )
        result = server_module.search_project_docs(query="test", top_k=-5)

        assert result["total"] == 1

    def test_top_k_within_range_not_clamped(self, server_module, fake_client):
        points = [
            make_scored_point(
                i,
                0.9 - i * 0.05,
                {"text": f"Chunk {i}", "source_file": f"c{i}.md", "title": f"C{i}", "type": "feature"},
            )
            for i in range(7)
        ]
        fake_client.set_query_results(points)
        result = server_module.search_project_docs(query="test", top_k=7)

        assert result["total"] == 7

    # --- English query (single vector, no RRF) ---

    def test_english_query_returns_single_vector_results(
        self, server_module, fake_client
    ):
        payload = {
            "text": "Checkout flow involves cart validation and payment.",
            "source_file": "docs/checkout.md",
            "title": "Checkout Flow",
            "parent_headings": ["Features"],
            "type": "doc",
        }
        fake_client.set_query_results(
            [make_scored_point(42, 0.9123, payload)]
        )
        result = server_module.search_project_docs(query="checkout incident")

        assert result["total"] == 1
        chunk = result["chunks"][0]
        assert chunk["source_file"] == "docs/checkout.md"
        assert chunk["title"] == "Checkout Flow"
        assert chunk["type"] == "doc"
        assert chunk["score"] == 0.9123
        # English queries should NOT have rrf_score
        assert "rrf_score" not in chunk

    # --- Russian query triggers dual search + RRF ---

    def test_russian_query_triggers_rrf_merge(self, server_module, fake_client):
        # The model mock produces 2 vectors for [ru_query, en_query].
        # Each vector triggers a query_points call.
        # We set results that will come back from both calls.
        payload_a = {
            "text": "Feature flags control rollout.",
            "source_file": "docs/ff.md",
            "title": "Feature Flags",
            "parent_headings": [],
            "type": "feature",
        }
        payload_b = {
            "text": "Dependencies between features.",
            "source_file": "docs/dep.md",
            "title": "Dependencies",
            "parent_headings": [],
            "type": "doc",
        }
        # Both query_points calls return these same results
        fake_client.set_query_results([
            make_scored_point(1, 0.88, payload_a),
            make_scored_point(2, 0.75, payload_b),
        ])
        result = server_module.search_project_docs(
            query="какие фичи зависят от stripe", top_k=5
        )

        assert result["total"] == 2
        # RRF results must include rrf_score
        for chunk in result["chunks"]:
            assert "rrf_score" in chunk
            assert isinstance(chunk["rrf_score"], float)
            assert chunk["rrf_score"] > 0

    def test_russian_query_rrf_accumulates_for_same_point_id(
        self, server_module, fake_client
    ):
        """Same point appearing in both query sets should get accumulated RRF score."""
        payload = {
            "text": "Shared result.",
            "source_file": "shared.md",
            "title": "Shared",
            "parent_headings": [],
            "type": "doc",
        }
        # Same point ID in both result sets
        fake_client.set_query_results([
            make_scored_point(42, 0.95, payload),
        ])
        result = server_module.search_project_docs(
            query="как работает checkout", top_k=3
        )

        assert result["total"] == 1
        chunk = result["chunks"][0]
        # Point 42 appeared in both ranked lists, so RRF score = 2 * 1/(60+1)
        expected_rrf = round(2.0 / 61.0, 5)
        assert chunk["rrf_score"] == expected_rrf

    def test_russian_query_keeps_highest_cosine_for_duplicate_id(
        self, server_module, fake_client
    ):
        """When same ID appears with different scores, highest cosine is kept."""
        payload = {
            "text": "Auth middleware",
            "source_file": "auth.md",
            "title": "Auth",
            "parent_headings": [],
            "type": "api",
        }
        fake_client.set_query_results([
            make_scored_point(10, 0.99, payload),
        ])
        result = server_module.search_project_docs(
            query="как работает авторизация", top_k=5
        )

        assert result["total"] == 1
        # Both queries return the same point (id=10) with score 0.99
        # The highest score should be preserved
        assert result["chunks"][0]["score"] == 0.99

    # --- Russian query where bridged query is empty or identical ---

    def test_russian_query_all_unknown_tokens_skips_dual_search(
        self, server_module, fake_client
    ):
        """RE6: all Cyrillic tokens unknown -> bridged query is "" -> skip dual search."""
        payload = {
            "text": "Some chunk text.",
            "source_file": "x.md",
            "title": "X",
            "type": "doc",
        }
        fake_client.set_query_results([
            make_scored_point(5, 0.5, payload),
        ])
        # "абвгдеж" -> bridged = "" (empty), so condition `en_query != query`
        # is True but `en_query` is falsy, so only original query runs
        result = server_module.search_project_docs(query="абвгдеж", top_k=5)

        assert result["total"] == 1
        # Single-query path — no rrf_score
        assert "rrf_score" not in result["chunks"][0]

    # --- chunk_type filter ---

    def test_chunk_type_filter_passed_to_qdrant(
        self, server_module, fake_client
    ):
        """When chunk_type is provided, a Filter should be constructed."""
        payload = {
            "text": "ADR content.",
            "source_file": "adr.md",
            "title": "ADR",
            "type": "adr",
        }
        fake_client.set_query_results([
            make_scored_point(7, 0.91, payload),
        ])

        # We need to capture whether query_filter is passed.
        # Patch query_points to spy on the filter argument.
        original_query_points = fake_client.query_points
        captured_filter = {}

        def spy_query_points(**kwargs):
            captured_filter["value"] = kwargs.get("query_filter")
            return original_query_points(**kwargs)

        fake_client.query_points = spy_query_points

        result = server_module.search_project_docs(
            query="architecture decision", chunk_type="adr"
        )

        assert result["total"] == 1
        assert captured_filter["value"] is not None

    def test_no_chunk_type_means_no_filter(self, server_module, fake_client):
        payload = {
            "text": "Any type.",
            "source_file": "any.md",
            "title": "Any",
            "type": "doc",
        }
        fake_client.set_query_results([
            make_scored_point(8, 0.8, payload),
        ])

        captured_filter = {}
        original_query_points = fake_client.query_points

        def spy_query_points(**kwargs):
            captured_filter["value"] = kwargs.get("query_filter")
            return original_query_points(**kwargs)

        fake_client.query_points = spy_query_points

        server_module.search_project_docs(query="test query")

        assert captured_filter["value"] is None

    # --- Empty result set ---

    def test_empty_results_returns_total_zero(self, server_module, fake_client):
        fake_client.set_query_results([])
        result = server_module.search_project_docs(
            query="nonexistent_xyz_12345", chunk_type="runbook"
        )

        assert result["total"] == 0
        assert result["chunks"] == []

    # --- fetch_limit = top_k * 3 ---

    def test_fetch_limit_is_triple_top_k(self, server_module, fake_client):
        """Verify that query_points is called with limit = top_k * 3."""
        fake_client.set_query_results([])

        captured_limit = {}
        original_query_points = fake_client.query_points

        def spy_query_points(**kwargs):
            captured_limit["value"] = kwargs.get("limit")
            return original_query_points(**kwargs)

        fake_client.query_points = spy_query_points

        server_module.search_project_docs(query="test", top_k=5)

        assert captured_limit["value"] == 15

    # --- Result count limited to top_k ---

    def test_results_truncated_to_top_k(self, server_module, fake_client):
        """Even if Qdrant returns more results, only top_k are returned."""
        points = [
            make_scored_point(
                i,
                0.9 - i * 0.01,
                {"text": f"Chunk {i}", "source_file": f"f{i}.md", "title": f"T{i}", "type": "doc"},
            )
            for i in range(10)
        ]
        fake_client.set_query_results(points)
        result = server_module.search_project_docs(query="test", top_k=3)

        assert result["total"] == 3
        assert len(result["chunks"]) == 3

    # --- Chunk structure validation ---

    def test_returned_chunk_has_required_fields(self, server_module, fake_client):
        payload = {
            "text": "Required fields test.",
            "source_file": "req.md",
            "file_path": "project-data/req.md",
            "title": "Required Fields",
            "parent_headings": ["Test"],
            "type": "incident",
        }
        fake_client.set_query_results([
            make_scored_point(55, 0.77, payload),
        ])
        result = server_module.search_project_docs(query="test")

        chunk = result["chunks"][0]
        required_keys = {
            "source_file", "file_path", "title", "parent_headings",
            "type", "score", "snippet",
        }
        assert required_keys.issubset(set(chunk.keys()))
        assert chunk["source_file"] == "req.md"
        assert chunk["file_path"] == "project-data/req.md"
        assert chunk["title"] == "Required Fields"
        assert chunk["parent_headings"] == ["Test"]
        assert chunk["type"] == "incident"
        assert chunk["score"] == 0.77
        assert isinstance(chunk["snippet"], str)

    # --- RRF ranking order ---

    def test_rrf_results_sorted_by_rrf_score_descending(
        self, server_module, fake_client
    ):
        """RRF-merged results must be sorted by rrf_score in descending order."""
        payload_a = {
            "text": "High RRF.",
            "source_file": "a.md",
            "title": "A",
            "parent_headings": [],
            "type": "doc",
        }
        payload_b = {
            "text": "Low RRF.",
            "source_file": "b.md",
            "title": "B",
            "parent_headings": [],
            "type": "doc",
        }
        # Return different points so they get different RRF scores
        fake_client.set_query_results([
            make_scored_point(1, 0.95, payload_a),
            make_scored_point(2, 0.60, payload_b),
        ])
        result = server_module.search_project_docs(
            query="какие фичи", top_k=10
        )

        assert result["total"] == 2
        scores = [c["rrf_score"] for c in result["chunks"]]
        assert scores == sorted(scores, reverse=True)

    # --- Lazy singleton initialization ---

    def test_get_model_initializes_once(self, server_module):
        model1 = server_module._get_model()
        model2 = server_module._get_model()
        assert model1 is model2

    def test_get_client_initializes_once(self, server_module):
        client1 = server_module._get_client()
        client2 = server_module._get_client()
        assert client1 is client2

    # --- Device selection ---

    def test_model_loaded_on_cpu_when_mps_unavailable(self, server_module):
        """With MPS mocked as unavailable (conftest default), device should be cpu."""
        model = server_module._get_model()
        assert model.device == "cpu"
