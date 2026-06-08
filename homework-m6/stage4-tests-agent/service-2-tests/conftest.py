"""
Shared pytest fixtures for mcp-rag-search tests.

All external dependencies (SentenceTransformer, QdrantClient, torch)
are mocked at the module level so tests never download models or
require a running Qdrant instance.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Path to the production server.py
# ---------------------------------------------------------------------------

_SERVER_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "mcp-rag-search"
    / "server.py"
)


# ---------------------------------------------------------------------------
# Fake implementations for heavy dependencies
# ---------------------------------------------------------------------------


class _FakeTorchBackendsMps:
    is_available = MagicMock(return_value=False)


class _FakeTorchBackends:
    mps = _FakeTorchBackendsMps()


class _FakeTorchModule(types.ModuleType):
    """Stand-in for ``torch`` with just enough surface area."""

    def __init__(self):
        super().__init__("torch")
        self.backends = _FakeTorchBackends()


class _FakeEmbeddingVector:
    """A fake embedding vector that supports ``.tolist()`` like a torch tensor."""

    def __init__(self, data: list):
        self._data = data

    def tolist(self):
        return self._data


class _FakeSentenceTransformer:
    """
    Stand-in for ``sentence_transformers.SentenceTransformer``.

    ``encode`` returns a list of fake embedding vectors that support
    ``.tolist()`` just like real numpy/torch tensors.
    """

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False):
        if isinstance(texts, str):
            texts = [texts]
        return [_FakeEmbeddingVector([0.1] * 8) for _ in texts]


class _FakeScoredPoint:
    """Mimics ``qdrant_client.models.ScoredPoint``."""

    def __init__(self, point_id: int, score: float, payload: dict):
        self.id = point_id
        self.score = score
        self.payload = payload


class _FakeQueryResponse:
    """Mimics the return value of ``QdrantClient.query_points``."""

    def __init__(self, points):
        self.points = points


class _FakeQdrantClient:
    """Stand-in for ``qdrant_client.QdrantClient``."""

    def __init__(self, url: str = "", timeout: int = 30, **kwargs):
        self.url = url
        self.timeout = timeout
        self._query_results: list = []

    def query_points(
        self,
        collection_name: str,
        query,
        limit: int = 10,
        query_filter=None,
        with_payload=True,
    ):
        return _FakeQueryResponse(self._query_results[:limit])

    def set_query_results(self, points: list):
        """Test helper: preload the points that ``query_points`` will return."""
        self._query_results = points


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_heavy_deps(monkeypatch):
    """
    Auto-used fixture: inject lightweight fakes for torch, fastmcp,
    sentence_transformers, and qdrant_client into ``sys.modules``
    *before* server.py is imported, so no real ML / network code runs.
    """
    monkeypatch.setitem(sys.modules, "torch", _FakeTorchModule())

    fake_st = types.ModuleType("sentence_transformers")
    fake_st.SentenceTransformer = _FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

    fake_qm = types.ModuleType("qdrant_client.models")
    fake_qm.Filter = MagicMock()
    fake_qm.FieldCondition = MagicMock()
    fake_qm.MatchValue = MagicMock()
    monkeypatch.setitem(sys.modules, "qdrant_client.models", fake_qm)

    fake_qc = types.ModuleType("qdrant_client")
    fake_qc.QdrantClient = _FakeQdrantClient
    monkeypatch.setitem(sys.modules, "qdrant_client", fake_qc)

    # FastMCP must return an object whose .tool() is an identity decorator
    # so that @mcp.tool() keeps the decorated function unchanged.
    class _FakeFastMCP:
        def __init__(self, name: str = ""):
            self.name = name

        def tool(self):
            return lambda fn: fn  # pass-through decorator

    fake_fm = types.ModuleType("fastmcp")
    fake_fm.FastMCP = _FakeFastMCP
    monkeypatch.setitem(sys.modules, "fastmcp", fake_fm)


@pytest.fixture()
def server_module(_mock_heavy_deps):
    """
    Load (or reload) server.py with all heavy dependencies mocked.
    Returns the module object so tests can call its functions directly.
    """
    import importlib.util

    mod_name = "mcp_rag_search_server"
    # Remove stale cached module so reload is clean
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    spec = importlib.util.spec_from_file_location(mod_name, str(_SERVER_FILE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def fake_client(server_module):
    """
    Return the QdrantClient instance used by the server module
    (backed by the fake injected by ``_mock_heavy_deps``).
    """
    return server_module._get_client()


@pytest.fixture()
def sample_point_payload():
    """Realistic chunk payload matching the ``proshop_chunks`` collection."""
    return {
        "text": "ADR-001: Choose MongoDB as the primary database. "
        "Decision: Use MongoDB with Mongoose ODM for schema flexibility.",
        "source_file": "project-data/specs/adr-001-mongodb.md",
        "file_path": "project-data/specs/adr-001-mongodb.md",
        "title": "ADR-001: Choose MongoDB",
        "parent_headings": ["Architecture Decisions", "Database"],
        "type": "adr",
    }


@pytest.fixture()
def sample_point_payload_short():
    """Chunk payload with text under 200 chars (no truncation expected)."""
    return {
        "text": "The auth middleware validates JWT tokens on protected routes.",
        "source_file": "project-data/specs/api-auth.md",
        "file_path": "project-data/specs/api-auth.md",
        "title": "Auth Middleware",
        "parent_headings": ["API Reference"],
        "type": "api",
    }


@pytest.fixture()
def sample_point_payload_long():
    """Chunk payload with text exceeding 200 chars (truncation expected)."""
    return {
        "text": "This is a very long chunk text that definitely exceeds two hundred "
        "characters in length. It describes the checkout flow in great detail "
        "including cart validation, inventory checks, payment processing via "
        "PayPal, order creation in MongoDB, and email notification dispatch. "
        "The flow involves multiple middleware layers and error recovery paths "
        "that handle network timeouts, payment gateway failures, and stock "
        "reservation conflicts. This sentence exists purely to exceed 200.",
        "source_file": "project-data/specs/checkout-flow.md",
        "file_path": "project-data/specs/checkout-flow.md",
        "title": "Checkout Flow",
        "parent_headings": ["Features", "Checkout"],
        "type": "doc",
    }


def make_scored_point(point_id: int, score: float, payload: dict) -> _FakeScoredPoint:
    """Utility: create a fake ScoredPoint with realistic data."""
    return _FakeScoredPoint(point_id=point_id, score=score, payload=payload)
