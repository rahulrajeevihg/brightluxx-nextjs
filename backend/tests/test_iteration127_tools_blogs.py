"""Iteration 127: new blogs (3), tools pages SSR/prerender, mission-critical page, location FAQ data."""
import os
import json
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

NEW_SLUGS = [
    "led-display-pricing-guide-uae",
    "indoor-vs-outdoor-led-screen-dubai",
    "led-wall-buyers-checklist",
]


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


# ---------- /api/blogs listing ----------
class TestBlogsListing:
    def test_blogs_list_has_18_including_new(self, client):
        r = client.get(f"{BASE_URL}/api/blogs")
        assert r.status_code == 200
        data = r.json()
        blogs = data if isinstance(data, list) else data.get("blogs", [])
        assert len(blogs) == 18, f"expected 18 blogs, got {len(blogs)}"
        slugs = [b["slug"] for b in blogs]
        for s in NEW_SLUGS:
            assert s in slugs, f"missing new blog {s}"
        assert all("_id" not in b for b in blogs), "MongoDB _id leaked in blog list"

    @pytest.mark.parametrize("slug", NEW_SLUGS)
    def test_blog_detail(self, client, slug):
        r = client.get(f"{BASE_URL}/api/blogs/{slug}")
        assert r.status_code == 200, r.text[:300]
        payload = r.json()
        b = payload.get("blog", payload)
        assert "_id" not in b
        assert b["slug"] == slug
        assert b.get("title")
        content = b.get("content") or ""
        assert len(content) > 1500, f"content too short ({len(content)})"
        # content should be HTML markup for renderer
        assert "<h2" in content or "<p" in content


# ---------- Prerendered / served pages ----------
PAGES = [
    "/tools",
    "/tools/led-wall-size-calculator",
    "/tools/video-wall-resolution-calculator",
    "/mission-critical-displays",
    "/led-screen-suppliers-dubai",
    "/calculator",
    "/led-calculator",
    "/blog/led-display-pricing-guide-uae",
    "/blog/indoor-vs-outdoor-led-screen-dubai",
    "/blog/led-wall-buyers-checklist",
]


@pytest.mark.parametrize("path", PAGES)
def test_page_returns_200_html(client, path):
    r = client.get(f"{BASE_URL}{path}", headers={"Accept": "text/html"}, timeout=30)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    assert "text/html" in r.headers.get("content-type", "")


def test_faq_schema_on_location_page(client):
    r = client.get(f"{BASE_URL}/led-screen-suppliers-dubai", headers={"Accept": "text/html"}, timeout=30)
    assert r.status_code == 200
    assert "FAQPage" in r.text, "FAQPage schema not present in served HTML"


# ---------- Location content data integrity ----------
def test_location_content_has_faqs():
    with open("/app/frontend/src/data/locationContent.json") as f:
        data = json.load(f)
    key = "/led-screen-suppliers-dubai"
    assert key in data, f"{key} missing from locationContent.json"
    faqs = data[key].get("faqs")
    assert faqs and len(faqs) == 5, f"expected 5 FAQs, got {faqs and len(faqs)}"
    for f_ in faqs:
        assert f_.get("q") and f_.get("a")
