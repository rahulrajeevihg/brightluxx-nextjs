"""Tests for bulk AI SEO generation + alt text features (iteration 109)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://app-router-parity.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brightluxx2026")


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, f"no token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---- Public page-meta endpoint ----
@pytest.mark.parametrize("path", ["/", "/glassmorph", "/signatouch", "/naturatex", "/pixelvue"])
def test_page_meta_returns_populated_seo(path):
    r = requests.get(f"{BASE_URL}/api/seo/page-meta", params={"path": path}, timeout=15)
    assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"
    d = r.json()
    assert d.get("meta_title"), f"{path}: empty meta_title -> {d}"
    assert d.get("meta_description"), f"{path}: empty meta_description"
    kw = d.get("keywords") or []
    assert isinstance(kw, list) and len(kw) > 0, f"{path}: keywords empty/not-list -> {kw}"
    assert d.get("image_alt"), f"{path}: empty image_alt -> {d}"


# ---- Admin stats ----
def test_admin_seo_stats(auth_headers):
    r = requests.get(f"{BASE_URL}/api/admin/seo/stats", headers=auth_headers, timeout=15)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    avg = d.get("avg_score", d.get("average_score", 0))
    missing = d.get("missing", d.get("missing_count", None))
    assert avg is not None and float(avg) > 70, f"avg_score not > 70: {avg} full={d}"
    assert missing == 0, f"missing should be 0, got {missing} full={d}"


# ---- Bulk job status ----
def test_admin_bulk_job_status(auth_headers):
    r = requests.get(f"{BASE_URL}/api/admin/seo/bulk-job-status", headers=auth_headers, timeout=15)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    assert d.get("status") == "completed", f"status != completed -> {d}"


# ---- Bulk generate all missing should say nothing_to_do ----
def test_admin_bulk_generate_nothing_to_do(auth_headers):
    r = requests.post(f"{BASE_URL}/api/admin/seo/ai-generate-all-missing",
                      headers=auth_headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code} {r.text[:300]}"
    d = r.json()
    assert d.get("status") == "nothing_to_do", f"expected nothing_to_do, got -> {d}"


# ---- Auth required checks ----
def test_admin_stats_requires_auth():
    r = requests.get(f"{BASE_URL}/api/admin/seo/stats", timeout=10)
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"
