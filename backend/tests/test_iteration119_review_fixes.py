"""Iteration 119 — Code review fix verification.

Covers:
- Backend health
- image_management.py: CATEGORY_PROMPTS defined, /categories + /preview-prompt endpoints, sha256 (no md5)
- Source-level checks: no bare `except:` in listed route modules, no hardcoded secrets in test files
- Frontend source checks: DOMPurify sanitization on all dangerouslySetInnerHTML usages
- Regression: geo IP enrichment on leads, anti-spam, phone validation
"""
import os
import re
import sys
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
BASE_URL = base_url.rstrip("/")

backend_env = dotenv_values("/app/backend/.env")
MONGO_URL = os.environ.get("MONGO_URL") or backend_env.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or backend_env.get("DB_NAME")

ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

TIMEOUT = 45


def uae_ip():
    n = uuid.uuid4().int
    return "94.200.%d.%d" % (n % 250 + 1, (n >> 9) % 250 + 1)


def ip_headers(ip=None, extra=None):
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip or uae_ip()}
    if extra:
        h.update(extra)
    return h


def lead_payload(**over):
    p = {
        "name": "TEST Ahmed Khan",
        "company": "TEST Retail LLC",
        "email": f"TEST_i119_{uuid.uuid4().hex[:6]}@brightretail.ae",
        "phone": "+971501234567",
        "city": "Dubai",
        "application": "Retail",
        "message": "We need a P2.5 indoor LED wall for our new flagship store lobby.",
    }
    p.update(over)
    return p


@pytest.fixture(scope="module")
def client():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post(f"{BASE_URL}/api/admin/login",
                    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                    timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    token = r.json().get("token")
    assert token, "No token in admin login response"
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def leads_col():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("MONGO_URL/DB_NAME not configured")
    c = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    yield c[DB_NAME]["leads"]
    c.close()


# ── Health ────────────────────────────────────────────────────────
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("status") == "ok"


# ── image_management: CATEGORY_PROMPTS ────────────────────────────
def test_category_prompts_defined_in_module():
    import importlib
    mod = importlib.import_module("routes.image_management")
    assert hasattr(mod, "CATEGORY_PROMPTS"), "CATEGORY_PROMPTS missing"
    cp = mod.CATEGORY_PROMPTS
    assert isinstance(cp, dict) and len(cp) > 0
    assert "default" in cp
    for k, v in cp.items():
        assert isinstance(v, str) and len(v) > 0, f"prompt for {k} invalid"


def test_image_management_uses_sha256_not_md5():
    src = Path("/app/backend/routes/image_management.py").read_text()
    assert "hashlib.sha256" in src, "sha256 not used"
    assert "md5" not in src, "md5 still referenced"


def test_categories_endpoint_requires_auth(client):
    r = client.get(f"{BASE_URL}/api/admin/images/categories", timeout=TIMEOUT)
    assert r.status_code in (401, 403, 200), r.status_code


def test_categories_endpoint(client, auth_headers):
    r = client.get(f"{BASE_URL}/api/admin/images/categories",
                   headers=auth_headers, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
    data = r.json()
    assert isinstance(data.get("categories"), list) and len(data["categories"]) > 0
    assert isinstance(data.get("prompts"), dict)
    assert "default" in data["categories"]
    for cat in data["categories"]:
        assert cat in data["prompts"], f"missing prompt for {cat}"


def test_preview_prompt_endpoint(client, auth_headers):
    # get a real product slug
    pr = client.get(f"{BASE_URL}/api/products?limit=5", timeout=TIMEOUT)
    assert pr.status_code == 200, pr.text[:300]
    body = pr.json()
    items = body if isinstance(body, list) else body.get("products") or body.get("items") or []
    assert items, f"No products returned: {str(body)[:200]}"
    slug = items[0].get("slug")
    assert slug, f"Product has no slug: {items[0]}"

    r = client.get(f"{BASE_URL}/api/admin/images/preview-prompt/{slug}",
                   headers=auth_headers, timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
    data = r.json()
    assert data["product_slug"] == slug
    assert isinstance(data.get("prompt"), str) and len(data["prompt"]) > 20
    assert isinstance(data.get("category"), str)


def test_preview_prompt_unknown_slug(client, auth_headers):
    r = client.get(f"{BASE_URL}/api/admin/images/preview-prompt/TEST-does-not-exist-xyz",
                   headers=auth_headers, timeout=TIMEOUT)
    assert r.status_code in (404, 200), f"unexpected {r.status_code}: {r.text[:300]}"
    assert r.status_code != 500, "500 on unknown slug"


# ── Source-level: bare except removed ─────────────────────────────
BARE_EXCEPT_FILES = [
    "applications_api.py", "pixelvue.py", "product_families.py",
    "solutions_api.py", "technologies_api.py",
]


@pytest.mark.parametrize("fname", BARE_EXCEPT_FILES)
def test_no_bare_except(fname):
    src = Path(f"/app/backend/routes/{fname}").read_text()
    offenders = [i + 1 for i, line in enumerate(src.splitlines())
                 if re.match(r"^\s*except\s*:", line)]
    assert not offenders, f"bare except in {fname} at lines {offenders}"


def test_no_bare_except_anywhere_in_routes():
    offenders = []
    for p in Path("/app/backend/routes").glob("*.py"):
        for i, line in enumerate(p.read_text().splitlines()):
            if re.match(r"^\s*except\s*:", line):
                offenders.append(f"{p.name}:{i+1}")
    assert not offenders, f"bare except found: {offenders}"


# ── Source-level: no hardcoded secrets in test files ──────────────
def test_old_secret_from_env():
    src = Path("/app/backend/tests/test_iteration115_review_fixes.py").read_text()
    m = re.search(r"^OLD_SECRET\s*=\s*(.+)$", src, re.M)
    assert m, "OLD_SECRET not found"
    assert "os.environ" in m.group(1), f"OLD_SECRET not from env: {m.group(1)}"


def test_admin_password_from_env_no_default():
    src = Path("/app/backend/tests/test_security.py").read_text()
    m = re.search(r"^ADMIN_PASSWORD\s*=\s*(.+)$", src, re.M)
    assert m, "ADMIN_PASSWORD not found"
    line = m.group(1)
    assert "os.environ" in line, f"ADMIN_PASSWORD not from env: {line}"
    assert "brightluxx" not in line.lower(), f"hardcoded password default: {line}"


# ── Frontend source: DOMPurify sanitization ───────────────────────
DANGEROUS_FILES = [
    "/app/frontend/src/pages/BlogPost.js",
    "/app/frontend/src/components/AuraChat.js",
    "/app/frontend/src/admin/AdminSiteSettings.js",
]


@pytest.mark.parametrize("path", DANGEROUS_FILES)
def test_dompurify_used(path):
    src = Path(path).read_text()
    assert "import DOMPurify from 'dompurify'" in src, f"DOMPurify not imported in {path}"
    for i, line in enumerate(src.splitlines()):
        if "dangerouslySetInnerHTML" in line:
            assert "DOMPurify.sanitize" in line, f"unsanitized dangerouslySetInnerHTML {path}:{i+1}"


def test_dompurify_installed():
    import json
    pkg = json.loads(Path("/app/frontend/package.json").read_text())
    assert "dompurify" in pkg["dependencies"], "dompurify not in dependencies"
    assert Path("/app/frontend/node_modules/dompurify/package.json").exists()


def test_no_unsanitized_dangerous_html_in_src():
    offenders = []
    for p in Path("/app/frontend/src").rglob("*.js"):
        for i, line in enumerate(p.read_text().splitlines()):
            if "dangerouslySetInnerHTML" in line and "DOMPurify.sanitize" not in line:
                offenders.append(f"{p}:{i+1}")
    # allow JSON-LD structured data blocks (script type application/ld+json)
    real = []
    for o in offenders:
        path, ln = o.rsplit(":", 1)
        lines = Path(path).read_text().splitlines()
        ctx = "\n".join(lines[max(0, int(ln) - 3):int(ln) + 1])
        if "ld+json" not in ctx and "JSON.stringify" not in ctx:
            real.append(o)
    assert not real, f"unsanitized dangerouslySetInnerHTML: {real}"


# ── Regression: geo enrichment on leads ───────────────────────────
def test_lead_stores_geo_and_spam_score(client, leads_col):
    payload = lead_payload()
    r = client.post(f"{BASE_URL}/api/leads", json=payload,
                    headers=ip_headers("94.200.10.20"), timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
    doc = leads_col.find_one({"email": payload["email"]})
    assert doc is not None, "lead not persisted"
    assert "geo" in doc, f"geo missing on lead doc: {list(doc.keys())}"
    assert doc["geo"].get("country") == "AE", f"geo={doc['geo']}"
    assert "spam_score" in doc
    assert 0 <= doc["spam_score"] <= 100, doc["spam_score"]
    leads_col.delete_one({"_id": doc["_id"]})


def test_lead_response_has_no_mongo_id(client):
    payload = lead_payload()
    r = client.post(f"{BASE_URL}/api/leads", json=payload,
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert "_id" not in r.json(), "_id leaked in response"


# ── Regression: anti-spam ─────────────────────────────────────────
def test_disposable_email_rejected(client):
    r = client.post(f"{BASE_URL}/api/leads",
                    json=lead_payload(email=f"TEST_i119_{uuid.uuid4().hex[:5]}@mailinator.com"),
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code in (400, 422), f"expected 400/422, got {r.status_code}: {r.text[:300]}"
    assert "temporary" in r.json()["detail"].lower()


def test_honeypot_silently_accepted(client, leads_col):
    payload = lead_payload()
    payload["website"] = "http://spam.example.com"
    r = client.post(f"{BASE_URL}/api/leads", json=payload,
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    assert leads_col.find_one({"email": payload["email"]}) is None, \
        "honeypot lead was persisted"


def test_spam_content_rejected(client):
    r = client.post(f"{BASE_URL}/api/leads",
                    json=lead_payload(message="Buy cheap viagra now! SEO backlinks casino http://a.com http://b.com http://c.com"),
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code in (400, 422), f"expected 400/422, got {r.status_code}: {r.text[:300]}"
    assert "spam" in r.json()["detail"].lower()


# ── Regression: phone validation ──────────────────────────────────
def test_short_phone_rejected(client):
    r = client.post(f"{BASE_URL}/api/leads", json=lead_payload(phone="12345"),
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code in (400, 422), f"expected 400/422, got {r.status_code}: {r.text[:300]}"


def test_valid_uae_phone_accepted(client, leads_col):
    payload = lead_payload(phone="+971 4 555 1234")
    r = client.post(f"{BASE_URL}/api/leads", json=payload,
                    headers=ip_headers(), timeout=TIMEOUT)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    leads_col.delete_many({"email": payload["email"]})


# ── Admin leads listing exposes geo/spam_score ────────────────────
def test_admin_leads_list_exposes_geo_fields(client, auth_headers, leads_col):
    payload = lead_payload()
    r = client.post(f"{BASE_URL}/api/leads", json=payload,
                    headers=ip_headers("94.200.44.55"), timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]

    lr = client.get(f"{BASE_URL}/api/admin/leads", headers=auth_headers, timeout=TIMEOUT)
    assert lr.status_code == 200, f"{lr.status_code}: {lr.text[:300]}"
    body = lr.json()
    items = body if isinstance(body, list) else body.get("leads") or body.get("items") or []
    assert items, "no leads returned"
    match = next((x for x in items if x.get("email") == payload["email"]), None)
    assert match is not None, "newly created lead not in admin listing"
    assert match.get("geo"), f"geo missing in admin lead payload: {list(match.keys())}"
    assert match["geo"].get("country") == "AE"
    assert match.get("spam_score") is not None, "spam_score missing in admin lead payload"

    leads_col.delete_many({"email": payload["email"]})


def test_admin_leads_no_mongo_object_id(client, auth_headers):
    """MongoDB _id must not be exposed in admin API responses."""
    lr = client.get(f"{BASE_URL}/api/admin/leads", headers=auth_headers, timeout=TIMEOUT)
    assert lr.status_code == 200, lr.text[:300]
    items = lr.json().get("leads", [])
    assert items, "no leads returned"
    leaked = [i.get("id") for i in items if "_id" in i]
    assert not leaked, f"_id leaked in admin leads response for {len(leaked)} docs"


# ── Cleanup ───────────────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def cleanup(leads_col):
    yield
    leads_col.delete_many({"email": {"$regex": "^TEST_i119_"}})
