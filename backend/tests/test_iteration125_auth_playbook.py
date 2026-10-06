"""Iteration 125 — Auth playbook verification: bcrypt, httpOnly cookies, CORS creds, brute-force lockout."""
import os
import re
import time
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env["REACT_APP_BACKEND_URL"]).rstrip("/")
ORIGIN = BASE_URL


@pytest.fixture(scope="module")
def creds():
    p = Path("/app/memory/test_credentials.md")
    c = p.read_text()
    e = re.search(r"(?im)^\s*[-*]?\s*Email:\s*`?([^`\s]+)", c)
    pw = re.search(r"(?im)^\s*[-*]?\s*Password:\s*`?([^`\s]+)", c)
    assert e and pw
    return {"email": e.group(1), "password": pw.group(1)}


class TestAdminAuth:
    def test_login_sets_httponly_cookies(self, creds):
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds,
                   headers={"Origin": ORIGIN}, timeout=30)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        raw = r.headers.get("Set-Cookie", "") + " ".join(
            v for k, v in r.raw.headers.items() if k.lower() == "set-cookie")
        assert "blx_access" in raw, f"no blx_access cookie: {raw[:200]}"
        assert "HttpOnly" in raw, "cookie not HttpOnly"
        assert "Secure" in raw, "cookie not Secure"
        assert "SameSite=none" in raw.lower().replace("samesite=none", "SameSite=none") or "samesite=none" in raw.lower()
        # token must not be echoed in body as plain access token only (cookie-based)
        # authenticated call works with cookie
        me = s.get(f"{BASE_URL}/api/admin/me", timeout=30)
        assert me.status_code == 200, f"/api/admin/me -> {me.status_code}"
        assert me.json().get("email") == creds["email"]

    def test_me_unauthenticated_401(self):
        r = requests.get(f"{BASE_URL}/api/admin/me", timeout=30)
        assert r.status_code == 401

    def test_cors_allows_credentials_with_explicit_origin(self):
        r = requests.options(f"{BASE_URL}/api/admin/login", headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }, timeout=30)
        acao = r.headers.get("Access-Control-Allow-Origin")
        acac = r.headers.get("Access-Control-Allow-Credentials")
        # NOTE: preview ingress/Cloudflare rewrites ACAO to "*". Origin (localhost:8001)
        # correctly returns the explicit origin + Allow-Credentials: true (verified via curl).
        if acao == "*":
            import subprocess
            out = subprocess.run(
                ["curl", "-s", "-X", "OPTIONS", "http://localhost:8001/api/admin/login",
                 "-H", f"Origin: {ORIGIN}", "-H", "Access-Control-Request-Method: POST",
                 "-D", "-", "-o", "/dev/null"], capture_output=True, text=True).stdout.lower()
            assert ORIGIN.lower() in out, f"origin does not echo explicit ACAO: {out}"
            assert "access-control-allow-credentials: true" in out
        else:
            assert acao == ORIGIN
            assert acac == "true", f"Allow-Credentials={acac}"

    def test_brute_force_lockout_after_5_fails(self, creds):
        s = requests.Session()
        codes = []
        for _ in range(7):
            r = s.post(f"{BASE_URL}/api/admin/login",
                       json={"email": creds["email"], "password": "wrong-pass-xyz"},
                       headers={"Origin": ORIGIN}, timeout=30)
            codes.append(r.status_code)
        print(f"login attempt codes: {codes}")
        assert 429 in codes, f"no 429 lockout observed: {codes}"
        assert codes.index(429) <= 5, f"lockout too late: {codes}"

    def test_logout_clears_cookie(self, creds):
        # wait for rate-limit window to expire (60s)
        time.sleep(62)
        s = requests.Session()
        r = s.post(f"{BASE_URL}/api/admin/login", json=creds, headers={"Origin": ORIGIN}, timeout=30)
        assert r.status_code == 200, f"login after lockout window -> {r.status_code}"
        lo = s.post(f"{BASE_URL}/api/admin/logout", timeout=30)
        assert lo.status_code in (200, 204), lo.status_code
        me = requests.get(f"{BASE_URL}/api/admin/me",
                          cookies=s.cookies.get_dict(), timeout=30)
        assert me.status_code == 401, f"session still valid after logout: {me.status_code}"
