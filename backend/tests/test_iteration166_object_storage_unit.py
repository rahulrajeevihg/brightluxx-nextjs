"""
Iteration 166
# Modules/features: object storage helper safety and spec-substitution storage behavior.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

if "/app/backend" not in sys.path:
    sys.path.insert(0, "/app/backend")

object_storage = importlib.import_module("object_storage")


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_storage_url_fails_without_proxy_url(monkeypatch):
    monkeypatch.delenv("INTEGRATION_PROXY_URL", raising=False)
    with pytest.raises(RuntimeError, match="INTEGRATION_PROXY_URL"):
        object_storage._storage_url()


def test_emergent_key_fails_without_key(monkeypatch):
    monkeypatch.delenv("EMERGENT_LLM_KEY", raising=False)
    with pytest.raises(RuntimeError, match="EMERGENT_LLM_KEY"):
        object_storage._emergent_key()


def test_init_storage_caches_key_and_uses_single_init_call(monkeypatch):
    monkeypatch.setenv("INTEGRATION_PROXY_URL", "https://proxy.example")
    monkeypatch.setenv("EMERGENT_LLM_KEY", "test-key")
    object_storage._storage_key = None

    calls: list[dict] = []

    def fake_post(url, json=None, timeout=30):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse(200, {"storage_key": "cached-123"})

    monkeypatch.setattr(object_storage.requests, "post", fake_post)

    key1 = object_storage.init_storage()
    key2 = object_storage.init_storage()

    assert key1 == "cached-123"
    assert key2 == "cached-123"
    assert len(calls) == 1
    assert calls[0]["url"].endswith("/objstore/api/v1/storage/init")
    assert calls[0]["json"] == {"emergent_key": "test-key"}


def test_put_object_retries_once_on_not_found(monkeypatch):
    monkeypatch.setenv("INTEGRATION_PROXY_URL", "https://proxy.example")
    monkeypatch.setenv("EMERGENT_LLM_KEY", "test-key")
    object_storage._storage_key = "existing-key"

    init_force_calls: list[bool] = []

    def fake_init_storage(force=False):
        init_force_calls.append(force)
        return "forced-key" if force else "existing-key"

    responses = [
        FakeResponse(404, {"error": "not found"}),
        FakeResponse(200, {"path": "brightluxx/uploads/spec-submissions/x/a.pdf", "size": 5}),
    ]

    put_calls: list[dict] = []

    def fake_put(url, headers=None, data=None, timeout=120):
        put_calls.append({"url": url, "headers": headers, "data": data, "timeout": timeout})
        return responses.pop(0)

    monkeypatch.setattr(object_storage, "init_storage", fake_init_storage)
    monkeypatch.setattr(object_storage.requests, "put", fake_put)

    result = object_storage.put_object("brightluxx/uploads/spec-submissions/x/a.pdf", b"hello", "application/pdf")

    assert result["size"] == 5
    assert len(put_calls) == 2
    assert init_force_calls == [False, True]
    assert put_calls[0]["headers"]["X-Storage-Key"] == "existing-key"
    assert put_calls[1]["headers"]["X-Storage-Key"] == "forced-key"


def test_spec_substitution_source_uses_object_storage_metadata_only():
    source = Path("/app/backend/routes/spec_substitution.py").read_text(encoding="utf-8")

    assert "put_object" in source
    assert "storage_path" in source
    assert "open(" not in source
    assert "os.makedirs" not in source
    assert "/app/uploads" not in source and "./uploads" not in source
