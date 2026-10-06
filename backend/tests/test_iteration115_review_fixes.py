"""Iteration 115 — Code review fix verification (JWT secret, route redirects,
internal links, ObjectId validation, prerender/llms.txt)."""
import os
import time

import pytest
import requests
from dotenv import dotenv_values
from jose import jwt

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

backend_env = dotenv_values("/app/backend/.env")
ADMIN_EMAIL = backend_env.get("ADMIN_SEED_EMAIL")
ADMIN_PASSWORD = backend_env.get("ADMIN_SEED_PASSWORD") or backend_env.get("ADMIN_PASSWORD")

OLD_SECRET = os.environ.get("OLD_JWT_SECRET", "old-insecure-placeholder-for-testing")
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def admin_token(client):
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.fail("Admin credentials missing in backend/.env")
    r = client.post(f"{BASE_URL}/api/admin/login",
                    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    tok = r.json().get("access_token") or r.json().get("token")
    if not tok:
        pytest.fail(f"No token in login response: {r.text[:300]}")
    return tok


# ── P0: JWT secret ──────────────────────────────────────────────
class TestJWTSecret:
    def test_forged_token_with_old_secret_rejected(self, client):
        forged = jwt.encode({"email": ADMIN_EMAIL, "type": "access", "exp": 9999999999},
                            OLD_SECRET, algorithm="HS256")
        r = client.get(f"{BASE_URL}/api/admin/seo/pages",
                       headers={"Authorization": f"Bearer {forged}"}, timeout=30)
        assert r.status_code == 401, f"Forged token accepted! status={r.status_code}"

    def test_no_token_rejected(self, client):
        r = client.get(f"{BASE_URL}/api/admin/seo/pages", timeout=30)
        assert r.status_code == 401

    def test_valid_login_token_works(self, client, admin_token):
        r = client.get(f"{BASE_URL}/api/admin/seo/pages",
                       headers={"Authorization": f"Bearer {admin_token}"}, timeout=60)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert isinstance(data, (list, dict))


# ── MEDIUM: ObjectId validation ─────────────────────────────────
class TestObjectIdValidation:
    @pytest.mark.parametrize("bad_id", ["invalid-id", "12345", "zzzzzzzzzzzzzzzzzzzzzzzz"])
    def test_get_invalid_id_not_500(self, client, admin_token, bad_id):
        r = client.get(f"{BASE_URL}/api/admin/seo/pages/{bad_id}",
                       headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
        assert r.status_code != 500, f"500 for id={bad_id}: {r.text[:200]}"
        # NOTE: currently returns 200 with {"error": ...} instead of 400/404 — reported as minor
        assert "error" in r.text.lower() or r.status_code in (400, 404, 422)

    def test_put_invalid_id_not_500(self, client, admin_token):
        r = client.put(f"{BASE_URL}/api/admin/seo/pages/invalid-id",
                       headers={"Authorization": f"Bearer {admin_token}"},
                       json={"meta_title": "TEST_x"}, timeout=30)
        assert r.status_code != 500, "PUT with invalid ObjectId raises 500 (no validation)"

    def test_ai_generate_invalid_id_not_500(self, client, admin_token):
        r = client.post(f"{BASE_URL}/api/admin/seo/ai-generate",
                        headers={"Authorization": f"Bearer {admin_token}"},
                        json={"page_id": "invalid-id"}, timeout=60)
        assert r.status_code != 500, "ai-generate with invalid ObjectId raises 500 (no validation)"


# ── HIGH: Route redirects (prerender server) ────────────────────
REDIRECTS = [
    ("/led-screen-dubai", "/led-screen-suppliers-dubai"),
    ("/led-display-abu-dhabi", "/abu-dhabi"),
    ("/led-screen-saudi-arabia", "/saudi-arabia"),
    ("/resource-library", "/resources"),
    ("/digital-experience", "/digital-experience-architecture"),
    ("/our-works/", "/projects"),
]


class TestRouteRedirects:
    @pytest.mark.parametrize("src,dst", REDIRECTS)
    def test_redirect(self, client, src, dst):
        r = client.get(f"{BASE_URL}{src}", headers={"User-Agent": GOOGLEBOT},
                       allow_redirects=False, timeout=60)
        assert r.status_code == 301, f"{src} -> status {r.status_code}"
        assert r.headers.get("location", "").rstrip("/") == dst.rstrip("/"), \
            f"{src} -> {r.headers.get('location')}"


# ── HIGH: Internal links no longer reference removed routes ─────
class TestInternalLinks:
    @pytest.mark.parametrize("path", ["/glassmorph", "/", "/led-screen-suppliers-dubai", "/lumimorph"])
    def test_no_stale_routes(self, client, path):
        r = client.get(f"{BASE_URL}/api/prerender/internal-links", params={"path": path}, timeout=30)
        assert r.status_code == 200, r.text[:200]
        links = r.json()
        assert isinstance(links, list) and len(links) > 0
        paths = [x["path"] for x in links]
        for stale in ["/led-screen-dubai", "/resource-library", "/led-display-abu-dhabi",
                      "/led-screen-saudi-arabia", "/digital-experience"]:
            assert stale not in paths, f"stale route {stale} in links for {path}"


# ── Prerender / SEO artifacts ───────────────────────────────────
class TestSeoArtifacts:
    def test_llms_txt(self, client):
        r = client.get(f"{BASE_URL}/llms.txt", timeout=60)
        assert r.status_code == 200
        body = r.text
        assert "/led-screen-suppliers-dubai" in body
        assert "/led-screen-dubai)" not in body and "/led-screen-dubai\n" not in body
        assert "/resource-library" not in body

    def test_googlebot_heading_hierarchy(self, client):
        r = client.get(f"{BASE_URL}/", headers={"User-Agent": GOOGLEBOT}, timeout=90)
        assert r.status_code == 200
        html = r.text
        assert "<h1" in html, "no h1 in prerendered HTML"
        assert "<h2" in html, "no h2 in prerendered HTML"

    def test_sitemap_no_stale_routes(self, client):
        r = client.get(f"{BASE_URL}/sitemap.xml", timeout=60)
        assert r.status_code == 200
        for stale in ["/led-screen-dubai<", "/resource-library<", "/digital-experience<"]:
            assert stale not in r.text, f"stale {stale} in sitemap"
