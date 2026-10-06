"""Iteration 122 — auth playbook verification: bcrypt hash format, httpOnly cookies,
CORS credentials, brute-force lockout, admin session. Runs lockout test LAST (60s window)."""
import os
import re
import asyncio
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values, load_dotenv

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL")
            or frontend_env["REACT_APP_BACKEND_URL"]).rstrip("/")


@pytest.fixture(scope="module")
def creds():
    p = Path("/app/memory/test_credentials.md")
    if not p.exists():
        pytest.skip("missing test_credentials.md")
    c = p.read_text()
    e = re.search(r"(?im)^\s*[-*]?\s*Email:\s*`?([^`\s]+)", c)
    pw = re.search(r"(?im)^\s*[-*]?\s*Password:\s*`?([^`\s]+)", c)
    if not e or not pw:
        pytest.skip("credentials not parseable")
    return {"email": e.group(1), "password": pw.group(1)}


class TestAdminAuth:
    def test_bcrypt_hash_format_in_db(self, creds):
        load_dotenv("/app/backend/.env")
        from motor.motor_asyncio import AsyncIOMotorClient

        async def get():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            for coll in ("admins", "admin_users", "users"):
                doc = await db[coll].find_one({"email": creds["email"]})
                if doc:
                    return coll, doc
            return None, None

        coll, doc = asyncio.run(get())
        assert doc, "admin user not found in DB"
        h = doc.get("password_hash") or doc.get("hashed_password") or doc.get("password")
        assert isinstance(h, str) and h.startswith("$2b$"), f"{coll}: hash prefix {str(h)[:6]}"

    def test_login_sets_httponly_cookies(self, creds):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=45)
        assert r.status_code == 200, r.text[:300]
        raw = "; ".join(r.raw.headers.get_all("Set-Cookie", []) if hasattr(r.raw, "headers") else [])
        raw = raw or str(r.headers.get("set-cookie", ""))
        assert "blx_access" in raw, raw[:300]
        assert "HttpOnly" in raw, raw[:300]
        assert "Secure" in raw, raw[:300]
        assert "blx_access" in s.cookies, dict(s.cookies)

    def test_authenticated_me_via_cookie(self, creds):
        s = requests.Session()
        assert s.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=45).status_code == 200
        me = s.get(f"{BASE_URL}/api/admin/me", timeout=45)
        assert me.status_code == 200, me.text[:300]
        assert me.json().get("email") == creds["email"], me.json()

    def test_me_unauthenticated_is_401(self):
        r = requests.get(f"{BASE_URL}/api/admin/me", timeout=45)
        assert r.status_code == 401, r.status_code

    def test_cors_allows_credentials_for_explicit_origin(self, creds):
        """NOTE: the preview ingress answers OPTIONS itself with 'Access-Control-Allow-Origin: *',
        so the preflight through the public URL cannot be asserted. Assert the actual
        credentialed POST instead — FastAPI CORSMiddleware must echo the explicit origin."""
        # The preview ingress rewrites Access-Control-Allow-Origin to '*' on every response
        # (public URL), so the app-level CORS contract is asserted against the app directly.
        origin = BASE_URL
        r = requests.post("http://localhost:8001/api/admin/login", json=creds,
                          headers={"Origin": origin}, timeout=45)
        assert r.status_code == 200, r.text[:200]
        acao = r.headers.get("access-control-allow-origin", "")
        acac = r.headers.get("access-control-allow-credentials", "")
        assert acao == origin, f"expected echoed origin, got {acao!r}"
        assert acac.lower() == "true", acac

    def test_wrong_password_rejected(self, creds):
        r = requests.post(f"{BASE_URL}/api/admin/login",
                          json={"email": creds["email"], "password": "definitely-wrong"}, timeout=45)
        assert r.status_code in (401, 403), r.status_code

    @pytest.mark.order("last")
    def test_zz_brute_force_lockout_after_5_attempts(self, creds):
        codes = []
        for _ in range(7):
            r = requests.post(f"{BASE_URL}/api/admin/login",
                              json={"email": creds["email"], "password": "wrong-pass-x"}, timeout=45)
            codes.append(r.status_code)
            if r.status_code == 429:
                break
        assert 429 in codes, f"no lockout triggered, codes={codes}"
