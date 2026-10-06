"""Iteration 120: httpOnly cookie auth, anti-spam regression, health."""
import os
import re
import time
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")


@pytest.fixture(scope="session")
def creds():
    p = Path("/app/memory/test_credentials.md")
    if not p.exists():
        pytest.skip("missing test_credentials.md")
    c = p.read_text(encoding="utf-8")
    e = re.search(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?email(?:\*\*)?\s*:\s*`?([^`\s]+)', c)
    pw = re.search(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?password(?:\*\*)?\s*:\s*`?([^`\s]+)', c)
    if not e or not pw:
        pytest.skip("credentials not parseable")
    return {"email": e.group(1), "password": pw.group(1)}


@pytest.fixture(scope="session")
def login_response(creds):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=30)
    if r.status_code == 429:
        time.sleep(65)
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"login failed {r.status_code}: {r.text[:300]}")
    return s, r


# ---------- HEALTH ----------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200
        assert r.json().get("status") in ("ok", "healthy")


# ---------- COOKIE AUTH ----------
class TestCookieAuth:
    def test_login_sets_httponly_cookies(self, login_response):
        s, r = login_response
        data = r.json()
        assert "token" in data and "refresh_token" in data
        assert data["admin"]["email"]
        raw = r.headers.get("set-cookie", "") or ""
        cookie_names = {c.name for c in s.cookies}
        assert "blx_access" in cookie_names, f"cookies={cookie_names} raw={raw[:400]}"
        assert "blx_refresh" in cookie_names
        low = raw.lower()
        assert "httponly" in low, f"HttpOnly flag missing: {raw[:400]}"
        assert "samesite=none" in low, f"SameSite=None missing: {raw[:400]}"
        assert "secure" in low, f"Secure missing: {raw[:400]}"

    def test_bcrypt_hash_format(self, login_response):
        # login success implies bcrypt verify worked; check stored hash prefix via DB
        import asyncio
        import sys
        sys.path.insert(0, "/app/backend")
        from motor.motor_asyncio import AsyncIOMotorClient
        be = dotenv_values("/app/backend/.env")

        async def _check():
            cl = AsyncIOMotorClient(be["MONGO_URL"])
            doc = await cl[be["DB_NAME"]]["admins"].find_one({})
            cl.close()
            return doc
        doc = asyncio.get_event_loop().run_until_complete(_check())
        assert doc is not None
        assert doc["password"].startswith("$2b$"), doc["password"][:10]

    def test_me_with_cookie_only(self, login_response):
        s, _ = login_response
        r = s.get(f"{BASE_URL}/api/admin/me", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert r.json()["email"]

    def test_me_with_bearer_only(self, login_response):
        _, lr = login_response
        token = lr.json()["token"]
        r = requests.get(f"{BASE_URL}/api/admin/me",
                         headers={"Authorization": f"Bearer {token}"}, timeout=30)
        assert r.status_code == 200, r.text[:300]

    def test_me_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/admin/me", timeout=30)
        assert r.status_code == 401

    def test_me_invalid_token(self):
        r = requests.get(f"{BASE_URL}/api/admin/me",
                         headers={"Authorization": "Bearer bogus.token.value"}, timeout=30)
        assert r.status_code == 401

    def test_refresh_from_cookie(self, login_response):
        s, _ = login_response
        r = s.post(f"{BASE_URL}/api/admin/refresh", timeout=30)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("token")
        assert "blx_access" in (r.headers.get("set-cookie", "") or "")

    def test_refresh_no_token(self):
        r = requests.post(f"{BASE_URL}/api/admin/refresh", timeout=30)
        assert r.status_code == 401

    def test_stats_protected_via_cookie(self, login_response):
        s, _ = login_response
        r = s.get(f"{BASE_URL}/api/admin/stats", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("products", "leads", "categories"):
            assert k in d

    def test_logout_clears_cookies(self, creds):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=30)
        if r.status_code == 429:
            time.sleep(65)
            r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=30)
        assert r.status_code == 200
        lo = s.post(f"{BASE_URL}/api/admin/logout", timeout=30)
        assert lo.status_code == 200
        assert lo.json().get("success") is True
        names = {c.name for c in s.cookies}
        assert "blx_access" not in names, f"cookie still present: {names}"
        me = s.get(f"{BASE_URL}/api/admin/me", timeout=30)
        assert me.status_code == 401, f"session still valid after logout: {me.status_code}"

    def test_cors_allows_credentials_explicit_origin(self):
        origin = BASE_URL
        r = requests.options(
            f"{BASE_URL}/api/admin/login",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                     "Access-Control-Request-Headers": "content-type"}, timeout=30)
        allow_origin = r.headers.get("access-control-allow-origin")
        allow_creds = r.headers.get("access-control-allow-credentials")
        assert allow_creds == "true", r.headers
        assert allow_origin != "*", (
            "allow_origin '*' with credentials=true is rejected by browsers")


# ---------- BRUTE FORCE ----------
class TestBruteForce:
    def test_lockout_after_failures(self, creds):
        s = requests.Session()
        codes = []
        for _ in range(7):
            r = s.post(f"{BASE_URL}/api/admin/login",
                       json={"email": creds["email"], "password": "wrong-pass-xyz"}, timeout=30)
            codes.append(r.status_code)
            if r.status_code == 429:
                break
        assert 429 in codes, f"no lockout; codes={codes}"
        # valid creds should also be blocked while locked
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=30)
        assert r.status_code == 429
        time.sleep(62)


# ---------- ANTI-SPAM LEADS REGRESSION ----------
class TestLeadsAntiSpam:
    def test_valid_lead(self):
        payload = {
            "name": "TEST_QA Cookie",
            "email": "test.qa.cookie@gmail.com",
            "phone": "+971501234567",
            "company": "TEST_QA Co",
            "message": "This is a genuine enquiry about indoor LED display pricing for our lobby.",
        }
        r = requests.post(f"{BASE_URL}/api/leads", json=payload, timeout=40)
        assert r.status_code in (200, 201, 429), r.text[:400]
        if r.status_code in (200, 201):
            assert r.json().get("success") or r.json().get("id")

    def test_disposable_email_rejected(self):
        payload = {
            "name": "TEST_QA Spam",
            "email": "spammer@mailinator.com",
            "phone": "+971501234568",
            "message": "This is a genuine enquiry about indoor LED display pricing for lobby.",
        }
        r = requests.post(f"{BASE_URL}/api/leads", json=payload, timeout=40)
        assert r.status_code in (400, 422, 429), f"{r.status_code} {r.text[:300]}"


# ---------- PUBLIC PAGES DATA ----------
class TestPublicApis:
    def test_products_list(self):
        r = requests.get(f"{BASE_URL}/api/products", timeout=40)
        assert r.status_code == 200
        d = r.json()
        items = d if isinstance(d, list) else d.get("products", d.get("items", []))
        assert len(items) > 0
        assert all("_id" not in i for i in items[:5])
