"""
Iteration 124 tests:
1) Duplicate BreadcrumbList cleanup — Googlebot crawl must have exactly 1 BreadcrumbList in JSON-LD
2) Admin reviews API (list w/ stats, filters, status update, persistence)
3) Regression: /api/health, /api/sitemap.xml (286+ URLs, no dupes)
"""
import json
import os
import re

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

GOOGLEBOT_UA = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

# Detail pages — must have exactly 1 BreadcrumbList (server-injected by ssr_meta)
DETAIL_PAGES = [
    "/products/gamewall-sim-180",
    "/technology/cob-led",
    "/solutions/retail",
    "/knowledge/pixel-pitch-guide",
    "/case-studies/jumeirah-al-naseem-lobby",
    "/blog/microled-vs-oled-2025",
    "/applications/stadium-led-screens",
    "/digital-experience-architecture",
]

# Hub/index pages — must never have duplicates (currently emit 0, tracked regression)
HUB_PAGES = [
    "/",
    "/about",
    "/contact",
    "/products",
    "/case-studies",
    "/blog",
    "/technology",
    "/solutions",
    "/knowledge",
    "/led-screen-dubai",
]

JSONLD_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S
)


def _count_breadcrumbs(html):
    """Parse all JSON-LD blocks and count BreadcrumbList entries (handles @graph/arrays)."""
    count = 0
    blocks = JSONLD_RE.findall(html)
    parse_errors = []
    for raw in blocks:
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            parse_errors.append(f"{exc}: {raw[:120]}")
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                if node.get("@type") == "BreadcrumbList":
                    count += 1
                if "@graph" in node:
                    stack.append(node["@graph"])
    return count, len(blocks), parse_errors


@pytest.fixture(scope="session")
def bot_session():
    s = requests.Session()
    s.headers.update({"User-Agent": GOOGLEBOT_UA})
    return s


# ---------- Health / regression ----------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert data.get("database") == "healthy"

    def test_sitemap_urls_no_duplicates(self):
        r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=60)
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "")
        locs = re.findall(r"<loc>(.*?)</loc>", r.text)
        assert len(locs) >= 286, f"Expected >=286 URLs, got {len(locs)}"
        dupes = {u for u in locs if locs.count(u) > 1}
        assert not dupes, f"Duplicate sitemap URLs: {list(dupes)[:10]}"


# ---------- BreadcrumbList de-duplication ----------
class TestBreadcrumbSingleSource:
    @pytest.mark.parametrize("path", DETAIL_PAGES)
    def test_detail_page_exactly_one_breadcrumblist(self, bot_session, path):
        r = bot_session.get(f"{BASE_URL}{path}", timeout=60)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        count, blocks, errors = _count_breadcrumbs(r.text)
        assert not errors, f"{path} invalid JSON-LD: {errors}"
        assert blocks > 0, f"{path} has no JSON-LD blocks"
        assert count == 1, f"{path} has {count} BreadcrumbList (expected 1)"

    @pytest.mark.parametrize("path", HUB_PAGES)
    def test_hub_page_no_duplicate_breadcrumblist(self, bot_session, path):
        r = bot_session.get(f"{BASE_URL}{path}", timeout=60)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        count, blocks, errors = _count_breadcrumbs(r.text)
        assert not errors, f"{path} invalid JSON-LD: {errors}"
        assert blocks > 0, f"{path} has no JSON-LD blocks"
        assert count <= 1, f"{path} has {count} BreadcrumbList (duplicate)"

    def test_ssr_meta_endpoint_single_breadcrumb(self):
        r = requests.get(
            f"{BASE_URL}/api/ssr/meta",
            params={"path": "/products/gamewall-sim-180"},
            timeout=30,
        )
        assert r.status_code == 200
        raw_schemas = r.json().get("schemas") or []
        schemas = [json.loads(s) if isinstance(s, str) else s for s in raw_schemas]
        bc = [s for s in schemas if s.get("@type") == "BreadcrumbList"]
        assert len(bc) == 1, f"ssr/meta returned {len(bc)} BreadcrumbList"
        items = bc[0].get("itemListElement", [])
        assert len(items) >= 2
        assert items[0]["position"] == 1


# ---------- Admin auth + reviews API ----------
@pytest.fixture(scope="session")
def admin_client():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": "admin@brightluxx.com", "password": "brightluxx2026"},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    token = r.json().get("token") or r.json().get("access_token")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


class TestAdminLoginSecurity:
    def test_login_sets_httponly_cookie(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": "admin@brightluxx.com", "password": "brightluxx2026"},
            timeout=30,
        )
        assert r.status_code == 200
        set_cookie = r.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie, f"No HttpOnly cookie: {set_cookie[:200]}"

    def test_login_wrong_password_rejected(self):
        r = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": "admin@brightluxx.com", "password": "definitely-wrong"},
            timeout=30,
        )
        assert r.status_code in (401, 403, 423, 429), r.status_code

    def test_admin_reviews_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/reviews", timeout=30)
        assert r.status_code in (401, 403), r.status_code


class TestAdminReviews:
    def test_list_reviews_with_stats(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/reviews", params={"page": 1, "limit": 30}, timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "reviews" in data and isinstance(data["reviews"], list)
        assert "total" in data and isinstance(data["total"], int)
        stats = data.get("stats")
        assert isinstance(stats, dict), "stats missing"
        for k in ("pending", "approved", "rejected"):
            assert k in stats, f"stats missing {k}"
            assert isinstance(stats[k], int)
        for rev in data["reviews"]:
            assert "_id" not in rev, "Mongo _id leaked"
            assert "id" in rev
            assert rev["status"] in ("pending", "approved", "rejected")

    def test_filter_by_status(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/reviews", params={"status": "approved"}, timeout=30)
        assert r.status_code == 200
        for rev in r.json()["reviews"]:
            assert rev["status"] == "approved"

    def test_filter_by_product_slug(self, admin_client):
        r = admin_client.get(
            f"{BASE_URL}/api/admin/reviews",
            params={"product_slug": "gamewall-sim-180"},
            timeout=30,
        )
        assert r.status_code == 200
        revs = r.json()["reviews"]
        assert len(revs) >= 2, f"Expected >=2 reviews for gamewall-sim-180, got {len(revs)}"
        for rev in revs:
            assert rev["product_slug"] == "gamewall-sim-180"

    def test_moderate_review_roundtrip(self, admin_client):
        # Create a test review via the public endpoint
        payload = {
            "product_slug": "gamewall-sim-180",
            "name": "TEST_QA Moderator",
            "email": "qa_test_iteration124@example.com",
            "rating": 5,
            "title": "TEST_ review title",
            "comment": "TEST_ This is an automated QA review comment for moderation testing purposes.",
        }
        cr = requests.post(f"{BASE_URL}/api/products/gamewall-sim-180/reviews", json=payload, timeout=30)
        if cr.status_code not in (200, 201):
            pytest.fail(f"Public review create failed {cr.status_code}: {cr.text[:300]}")
        assert cr.json().get("status") == "submitted"

        # POST does not return an id — locate it via admin list (pending status)
        lr0 = admin_client.get(
            f"{BASE_URL}/api/admin/reviews",
            params={"product_slug": "gamewall-sim-180", "limit": 100},
            timeout=30,
        )
        assert lr0.status_code == 200
        found = [x for x in lr0.json()["reviews"] if x.get("email") == payload["email"]]
        assert found, "Newly submitted review not visible in admin list"
        rid = found[0]["id"]
        assert found[0]["status"] == "pending", "New review should default to pending"

        try:
            # Approve
            ur = admin_client.put(f"{BASE_URL}/api/admin/reviews/{rid}", json={"status": "approved"}, timeout=30)
            assert ur.status_code == 200, ur.text[:300]
            lr = admin_client.get(f"{BASE_URL}/api/admin/reviews", params={"product_slug": "gamewall-sim-180"}, timeout=30)
            match = [x for x in lr.json()["reviews"] if x["id"] == rid]
            assert match and match[0]["status"] == "approved", "Approve did not persist"

            # Reject
            ur2 = admin_client.put(f"{BASE_URL}/api/admin/reviews/{rid}", json={"status": "rejected"}, timeout=30)
            assert ur2.status_code == 200
            lr2 = admin_client.get(f"{BASE_URL}/api/admin/reviews", params={"product_slug": "gamewall-sim-180"}, timeout=30)
            match2 = [x for x in lr2.json()["reviews"] if x["id"] == rid]
            assert match2 and match2[0]["status"] == "rejected", "Reject did not persist"
        finally:
            dr = admin_client.delete(f"{BASE_URL}/api/admin/reviews/{rid}", timeout=30)
            assert dr.status_code in (200, 204), f"Delete failed {dr.status_code}"
            lr3 = admin_client.get(f"{BASE_URL}/api/admin/reviews", params={"product_slug": "gamewall-sim-180"}, timeout=30)
            assert not [x for x in lr3.json()["reviews"] if x["id"] == rid], "Review not deleted"

    def test_invalid_status_rejected(self, admin_client):
        r = admin_client.put(
            f"{BASE_URL}/api/admin/reviews/nonexistent-id-xyz",
            json={"status": "bogus"},
            timeout=30,
        )
        assert r.status_code in (400, 404, 422), r.status_code

    def test_public_reviews_pii_safe(self):
        r = requests.get(f"{BASE_URL}/api/products/gamewall-sim-180/reviews", timeout=30)
        assert r.status_code == 200
        data = r.json()
        revs = data.get("reviews", data if isinstance(data, list) else [])
        for rev in revs:
            assert "email" not in rev, "PII email exposed in public reviews"
            assert "ip" not in rev and "ip_address" not in rev
            assert rev.get("status", "approved") == "approved"
