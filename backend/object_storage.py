"""Emergent Object Storage helpers for user-submitted files."""
import os
from threading import Lock

import requests

APP_NAME = "brightluxx"
_storage_key: str | None = None
_storage_lock = Lock()


def _storage_url() -> str:
    base_url = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip()
    if not base_url:
        raise RuntimeError("INTEGRATION_PROXY_URL must be configured for object storage")
    return f"{base_url.rstrip('/')}/objstore/api/v1/storage"


def _emergent_key() -> str:
    key = (os.environ.get("EMERGENT_LLM_KEY") or "").strip()
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY must be configured for object storage")
    return key


def init_storage(force: bool = False) -> str:
    """Create one reusable, session-scoped Object Storage key."""
    global _storage_key
    with _storage_lock:
        if _storage_key and not force:
            return _storage_key
        response = requests.post(
            f"{_storage_url()}/init",
            json={"emergent_key": _emergent_key()},
            timeout=30,
        )
        response.raise_for_status()
        _storage_key = response.json()["storage_key"]
        return _storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Store an object and return its canonical Object Storage reference."""
    for attempt in range(2):
        response = requests.put(
            f"{_storage_url()}/objects/{path}",
            headers={"X-Storage-Key": init_storage(force=attempt == 1), "Content-Type": content_type},
            data=data,
            timeout=120,
        )
        if response.status_code != 404 or attempt == 1:
            response.raise_for_status()
            return response.json()
    raise RuntimeError("Object Storage upload did not return a result")