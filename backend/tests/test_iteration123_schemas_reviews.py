"""Iteration 123 — Structured data gaps (JSON-LD on 31+ pages), Review collection
system (submit/list/admin moderation/AggregateRating) and Smart Cache Purge.
"""
import json
import os
import time
import uuid

import pytest
import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env.get("REACT_APP_BACKEND_URL")).rstrip("/")

ADMIN = {"email": "admin@brightluxx.com", "password": "brightluxx2025"}
PRODUCT = "gamewall-sim-180"


def get_meta(path, fresh=False):
    if fresh:
        requests.post(f"{BASE_URL}/api/ssr/meta/clear-cache", timeout=45)
    r = requests.get(f"{BASE_URL}/api/ssr/meta", params={"path": path}, timeout=45)
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
    return r.json()


def schema_types(meta):
    out = []
    for s in meta.get("schemas") or []:
        try:
            out.append(json.loads(s).get("@type"))
        except Exception:
            out.append("INVALID_JSON")
    return out


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/login", json=ADMIN, timeout=45)
    if r.status_code != 200:
        pytest.fail(f"admin login failed: {r.status_code} {r.text[:300]}")
    token = r.json().get("access_token") or r.json().get("token")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# --- Feature 1: structured data on previously schema-less pages ---
class TestSchemaCoverage:

    @pytest.mark.parametrize("path,expected", [
        ("/case-studies/jumeirah-al-naseem-lobby", ["Article", "BreadcrumbList"]),
        ("/applications/retail", ["WebPage", "BreadcrumbList"]),
        ("/contractors/dvled-vs-lcd", ["Article", "BreadcrumbList"]),
        ("/latest-tech/microled", ["Article", "BreadcrumbList"]),
        ("/knowledge/pixel-pitch-guide", ["Article", "BreadcrumbList"]),
        ("/technology/cob-led", ["Article", "BreadcrumbList"]),
        ("/solutions/retail", ["WebPage", "BreadcrumbList"]),
        ("/digital-experience-architecture", ["WebPage", "BreadcrumbList"]),
        ("/sla-guide", ["WebPage"]),
        ("/", ["WebPage"]),
    ])
    def test_expected_schema_types(self, path, expected):
        types = schema_types(get_meta(path))
        for t in expected:
            assert t in types, f"{path}: expected {t}, got {types}"

    def test_product_page_schemas(self):
        types = schema_types(get_meta(f"/products/{PRODUCT}"))
        assert "Product" in types and "BreadcrumbList" in types, types
        assert "FAQPage" in types, types

    def test_blog_page_schemas(self):
        types = schema_types(get_meta("/blog/microled-vs-oled-2025"))
        for t in ("Article", "FAQPage", "BreadcrumbList"):
            assert t in types, f"expected {t}, got {types}"

    def test_all_schemas_valid_json_and_have_context(self):
        for path in ["/", "/products", "/case-studies/jumeirah-al-naseem-lobby",
                     "/applications/retail", "/sla-guide", "/knowledge/pixel-pitch-guide"]:
            meta = get_meta(path)
            assert meta.get("schemas"), f"{path} has no schemas"
            for s in meta["schemas"]:
                obj = json.loads(s)
                assert obj.get("@context") == "https://schema.org", (path, obj.get("@type"))

    def test_breadcrumb_positions_sequential(self):
        meta = get_meta("/case-studies/jumeirah-al-naseem-lobby")
        bc = [json.loads(s) for s in meta["schemas"] if json.loads(s).get("@type") == "BreadcrumbList"][0]
        positions = [i["position"] for i in bc["itemListElement"]]
        assert positions == list(range(1, len(positions) + 1)), positions

    def test_no_duplicate_schema_types(self):
        for path in ["/blog/microled-vs-oled-2025", f"/products/{PRODUCT}",
                     "/case-studies/jumeirah-al-naseem-lobby"]:
            types = schema_types(get_meta(path))
            assert len(types) == len(set(types)), f"{path} duplicate schemas: {types}"


# --- Feature 2: reviews ---
class TestPublicReviews:

    def test_get_reviews_with_stats(self):
        r = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45)
        assert r.status_code == 200
        d = r.json()
        assert d["stats"]["total_reviews"] >= 1
        assert d["stats"]["average_rating"] > 0, d["stats"]
        # Public endpoint should not expose status field
        for rv in d["reviews"]:
            assert "status" not in rv, "status should not be in public response"

    def test_public_reviews_do_not_leak_email(self):
        d = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()
        leaked = [rv.get("email") for rv in d["reviews"] if rv.get("email")]
        assert not leaked, f"PII leak: public endpoint returns reviewer emails {leaked}"

    def test_no_mongo_object_id(self):
        d = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()
        assert all("_id" not in rv for rv in d["reviews"])

    def test_unknown_product_returns_empty(self):
        r = requests.get(f"{BASE_URL}/api/products/does-not-exist-xyz/reviews", timeout=45)
        assert r.status_code == 200
        assert r.json()["stats"]["total_reviews"] == 0


class TestReviewValidation:

    def base(self, **over):
        body = {"name": "TEST_QA Reviewer", "email": f"TEST_{uuid.uuid4().hex[:8]}@example.com",
                "rating": 4, "title": "TEST title", "comment": "This is a valid QA test review comment."}
        body.update(over)
        return body

    def test_missing_rating_400(self):
        r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews",
                          json=self.base(rating=None), timeout=45)
        assert r.status_code == 400, r.text[:300]

    def test_invalid_rating_400(self):
        for bad in (0, 6, "five"):
            r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews",
                              json=self.base(rating=bad), timeout=45)
            assert r.status_code == 400, f"rating={bad} -> {r.status_code}"

    def test_short_comment_400(self):
        r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews",
                          json=self.base(comment="short"), timeout=45)
        assert r.status_code == 400, r.text[:300]

    def test_bad_email_400(self):
        r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews",
                          json=self.base(email="notanemail"), timeout=45)
        assert r.status_code == 400, r.text[:300]

    def test_short_name_400(self):
        r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews",
                          json=self.base(name="A"), timeout=45)
        assert r.status_code == 400, r.text[:300]

    def test_nonexistent_product_404(self):
        r = requests.post(f"{BASE_URL}/api/products/nonexistent-product/reviews",
                          json=self.base(), timeout=45)
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text[:300]}"


class TestReviewLifecycle:
    """Submit -> pending in admin -> approve -> public + AggregateRating."""

    created = []

    def test_submit_and_moderate_flow(self, admin_session):
        email = f"TEST_{uuid.uuid4().hex[:10]}@example.com"
        body = {"name": "TEST_QA Lifecycle", "email": email, "rating": 4,
                "title": "TEST lifecycle", "comment": "Automated QA lifecycle review comment text."}
        r = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews", json=body, timeout=45)
        assert r.status_code == 200, r.text[:300]
        assert r.json()["status"] == "submitted"

        # must appear as pending in admin
        adm = admin_session.get(f"{BASE_URL}/api/admin/reviews",
                                params={"product_slug": PRODUCT, "limit": 100}, timeout=45)
        assert adm.status_code == 200, adm.text[:300]
        data = adm.json()
        assert set(["pending", "approved", "rejected"]).issubset(data["stats"].keys())
        mine = [rv for rv in data["reviews"] if rv["email"] == email.lower()]
        assert mine, f"submitted review not stored (anti-spam silent drop?). stats={data['stats']}"
        rid = mine[0]["id"]
        TestReviewLifecycle.created.append(rid)
        assert mine[0]["status"] == "pending"

        # not public yet
        pub = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()
        assert rid not in [x["id"] for x in pub["reviews"]]

        # approve
        up = admin_session.put(f"{BASE_URL}/api/admin/reviews/{rid}", json={"status": "approved"}, timeout=45)
        assert up.status_code == 200, up.text[:300]
        time.sleep(1)
        pub = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()
        assert rid in [x["id"] for x in pub["reviews"]], "approved review not public"
        expected_avg = round(pub["stats"]["average_rating"], 1)

        # Smart cache purge: Product schema aggregateRating must reflect new review
        # WITHOUT manually clearing the cache.
        meta = get_meta(f"/products/{PRODUCT}")
        prod = [json.loads(s) for s in meta["schemas"] if json.loads(s).get("@type") == "Product"][0]
        assert "aggregateRating" in prod, "Product schema missing aggregateRating"
        assert prod["aggregateRating"]["reviewCount"] == pub["stats"]["total_reviews"], (
            f"stale SSR cache: schema reviewCount={prod['aggregateRating']['reviewCount']} "
            f"vs live {pub['stats']['total_reviews']} — clear_ssr_cache() did not purge")
        assert prod["aggregateRating"]["ratingValue"] == expected_avg

        # reject
        up = admin_session.put(f"{BASE_URL}/api/admin/reviews/{rid}", json={"status": "rejected"}, timeout=45)
        assert up.status_code == 200
        pub = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()
        assert rid not in [x["id"] for x in pub["reviews"]], "rejected review still public"

    def test_duplicate_submission_blocked(self):
        email = f"TEST_dup_{uuid.uuid4().hex[:8]}@example.com"
        body = {"name": "TEST_QA Dup", "email": email, "rating": 3,
                "comment": "Duplicate detection QA review comment."}
        r1 = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews", json=body, timeout=45)
        assert r1.status_code == 200, r1.text[:300]
        r2 = requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews", json=body, timeout=45)
        assert r2.status_code in (200, 409), r2.status_code
        assert r2.status_code == 409, "duplicate review was accepted twice"

    def test_admin_requires_auth(self):
        assert requests.get(f"{BASE_URL}/api/admin/reviews", timeout=45).status_code in (401, 403)

    def test_update_unknown_review_404(self, admin_session):
        r = admin_session.put(f"{BASE_URL}/api/admin/reviews/{uuid.uuid4()}",
                              json={"status": "approved"}, timeout=45)
        assert r.status_code == 404, r.status_code

    def test_update_no_valid_fields_400(self, admin_session):
        r = admin_session.put(f"{BASE_URL}/api/admin/reviews/{uuid.uuid4()}",
                              json={"foo": "bar"}, timeout=45)
        assert r.status_code == 400, r.status_code


# --- Regression ---
class TestRegression:

    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=45)
        assert r.status_code == 200
        assert r.json().get("status") in ("ok", "healthy")

    def test_sitemap_count_and_no_duplicates(self):
        r = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=60)
        assert r.status_code == 200
        locs = [m for m in r.text.split("<loc>")[1:]]
        locs = [l.split("</loc>")[0] for l in locs]
        assert len(locs) >= 286, f"only {len(locs)} URLs"
        assert len(locs) == len(set(locs)), "duplicate URLs in sitemap"


@pytest.fixture(scope="session", autouse=True)
def cleanup(admin_session):
    yield
    # remove TEST_ reviews created during the run
    r = admin_session.get(f"{BASE_URL}/api/admin/reviews", params={"limit": 200}, timeout=45)
    if r.status_code == 200:
        for rv in r.json().get("reviews", []):
            if str(rv.get("email", "")).startswith("test_") or str(rv.get("name", "")).startswith("TEST_"):
                admin_session.delete(f"{BASE_URL}/api/admin/reviews/{rv['id']}", timeout=45)
