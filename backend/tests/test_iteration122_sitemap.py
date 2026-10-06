"""Iteration 122 — Dynamic DB-driven sitemap (/api/sitemap.xml), static sitemap index,
robots.txt directives, and SSR meta / schema regression."""
import os
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")
BASE_URL = base_url.rstrip("/")
SITEMAP_BASE = "https://brightluxx.com"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@pytest.fixture(scope="module")
def sitemap_resp():
    return requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=60)


@pytest.fixture(scope="module")
def sitemap_root(sitemap_resp):
    return ET.fromstring(sitemap_resp.content)


@pytest.fixture(scope="module")
def url_entries(sitemap_root):
    out = []
    for u in sitemap_root.findall("sm:url", NS):
        out.append({
            "loc": (u.findtext("sm:loc", default="", namespaces=NS) or "").strip(),
            "lastmod": (u.findtext("sm:lastmod", default="", namespaces=NS) or "").strip(),
            "changefreq": (u.findtext("sm:changefreq", default="", namespaces=NS) or "").strip(),
            "priority": (u.findtext("sm:priority", default="", namespaces=NS) or "").strip(),
        })
    return out


# ---------- Health ----------
class TestHealth:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert str(data.get("status", "")).lower() in ("healthy", "ok"), data


# ---------- Sitemap structure ----------
class TestSitemapStructure:
    def test_status_and_content_type(self, sitemap_resp):
        assert sitemap_resp.status_code == 200
        assert "xml" in sitemap_resp.headers.get("content-type", "").lower()

    def test_xml_declaration_and_namespace(self, sitemap_resp, sitemap_root):
        text = sitemap_resp.content.decode("utf-8")
        assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert sitemap_root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"

    def test_cache_control_header(self, sitemap_resp):
        # Backend route sets "public, max-age=3600"; the preview ingress may rewrite it to
        # no-store. Accept either, but the header must exist.
        cc = sitemap_resp.headers.get("cache-control", "").lower()
        assert cc, "no Cache-Control header on sitemap response"

    def test_url_count_minimum(self, url_entries):
        assert len(url_entries) >= 280, f"expected >=280 urls, got {len(url_entries)}"

    def test_no_duplicates(self, url_entries):
        locs = [e["loc"] for e in url_entries]
        dupes = {l for l in locs if locs.count(l) > 1}
        assert not dupes, f"duplicate locs: {sorted(dupes)}"

    def test_all_use_prod_base(self, url_entries):
        bad = [e["loc"] for e in url_entries if not e["loc"].startswith(SITEMAP_BASE)]
        assert not bad, bad[:10]

    def test_lastmod_format(self, url_entries):
        bad = []
        for e in url_entries:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["lastmod"]):
                bad.append((e["loc"], e["lastmod"]))
                continue
            try:
                datetime.strptime(e["lastmod"], "%Y-%m-%d")
            except ValueError:
                bad.append((e["loc"], e["lastmod"]))
        assert not bad, bad[:10]

    def test_changefreq_valid(self, url_entries):
        allowed = {"always", "hourly", "daily", "weekly", "monthly", "yearly", "never"}
        bad = [(e["loc"], e["changefreq"]) for e in url_entries if e["changefreq"] not in allowed]
        assert not bad, bad[:10]

    def test_priority_range(self, url_entries):
        bad = []
        for e in url_entries:
            try:
                p = float(e["priority"])
            except ValueError:
                bad.append((e["loc"], e["priority"]))
                continue
            if not (0.0 <= p <= 1.0):
                bad.append((e["loc"], e["priority"]))
        assert not bad, bad[:10]

    def test_homepage_present_priority_1(self, url_entries):
        home = [e for e in url_entries if e["loc"] == f"{SITEMAP_BASE}/"]
        assert home, "homepage missing"
        assert float(home[0]["priority"]) == 1.0


# ---------- Sitemap coverage ----------
class TestSitemapCoverage:
    @pytest.mark.parametrize("prefix,expected", [
        ("/products/", 93),
        ("/blog/", 15),
        ("/case-studies/", 8),
    ])
    def test_section_counts(self, url_entries, prefix, expected):
        n = len([e for e in url_entries if e["loc"].startswith(SITEMAP_BASE + prefix)])
        assert n == expected, f"{prefix} -> {n} (expected {expected})"

    @pytest.mark.parametrize("prefix", ["/solutions/", "/technology/", "/applications/"])
    def test_section_nonempty(self, url_entries, prefix):
        n = len([e for e in url_entries if e["loc"].startswith(SITEMAP_BASE + prefix)])
        assert n > 0, f"no urls for {prefix}"

    def test_no_non_indexable_urls(self, url_entries):
        blocked = ("/admin", "/api/", "/cart", "/configurator", "/compare?")
        bad = [e["loc"] for e in url_entries
               if any(e["loc"].startswith(SITEMAP_BASE + b) for b in blocked)]
        assert not bad, bad

    def test_no_query_or_fragment(self, url_entries):
        bad = [e["loc"] for e in url_entries if "?" in e["loc"] or "#" in e["loc"]]
        assert not bad, bad


# ---------- Static sitemap index + robots ----------
class TestStaticSeoFiles:
    def test_static_sitemap_index(self):
        r = requests.get(f"{BASE_URL}/sitemap.xml", timeout=30)
        assert r.status_code == 200, r.status_code
        text = r.text
        assert "<sitemapindex" in text, text[:300]
        root = ET.fromstring(r.content)
        locs = [e.text.strip() for e in root.findall("sm:sitemap/sm:loc", NS)]
        assert f"{SITEMAP_BASE}/api/sitemap.xml" in locs, locs

    def test_robots_txt(self):
        r = requests.get(f"{BASE_URL}/robots.txt", timeout=30)
        assert r.status_code == 200
        text = r.text
        assert f"Sitemap: {SITEMAP_BASE}/sitemap.xml" in text
        assert f"Sitemap: {SITEMAP_BASE}/api/sitemap.xml" in text
        assert "Disallow: /admin" in text
        assert "Disallow: /cart" in text


# ---------- SSR meta + schema ----------
def _get_meta(path):
    return requests.get(f"{BASE_URL}/api/ssr/meta", params={"path": path}, timeout=45)


def _schema_types(data):
    raw = data.get("schemas") or data.get("schema") or data.get("json_ld")
    if not raw:
        return [], None
    items_raw = raw if isinstance(raw, list) else [raw]
    schema = []
    for it in items_raw:
        if isinstance(it, str):
            try:
                schema.append(json.loads(it))
            except Exception:
                pass
        else:
            schema.append(it)
    types = []
    items = schema if isinstance(schema, list) else [schema]
    for it in items:
        if isinstance(it, dict):
            if "@graph" in it and isinstance(it["@graph"], list):
                for g in it["@graph"]:
                    if isinstance(g, dict) and g.get("@type"):
                        types.append(g["@type"])
            if it.get("@type"):
                types.append(it["@type"])
    flat = []
    for t in types:
        flat.extend(t if isinstance(t, list) else [t])
    return flat, schema


class TestSsrMeta:
    def test_product_meta_and_schema(self):
        path = "/products/gamewall-sim-180"
        r = _get_meta(path)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("title"), d
        assert d.get("description"), d
        assert d.get("canonical", "").endswith(path), d.get("canonical")
        types, schema = _schema_types(d)
        assert schema, "no schema returned"
        assert "Product" in types, types
        assert "FAQPage" in types, types

    def test_blog_meta_and_faq_schema(self):
        path = "/blog/microled-vs-oled-2025"
        r = _get_meta(path)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("title")
        assert d.get("description")
        assert d.get("canonical", "").endswith(path)
        types, schema = _schema_types(d)
        assert "FAQPage" in types, types

    def test_missing_path_validation(self):
        r = requests.get(f"{BASE_URL}/api/ssr/meta", timeout=30)
        assert r.status_code == 422, r.status_code


# ---------- Sitemap URLs must be live routes (regression from iteration 121) ----------
class TestSitemapUrlsReachable:
    def test_sample_urls_return_200_for_browser(self, url_entries):
        import random
        random.seed(122)
        paths = [e["loc"].replace(SITEMAP_BASE, "") for e in url_entries]
        sample = random.sample(paths, 25)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}
        failures = []
        for p in sample:
            try:
                r = requests.get(f"{BASE_URL}{p}", headers=headers, timeout=45)
                if r.status_code != 200:
                    failures.append((p, r.status_code))
            except Exception as exc:
                failures.append((p, str(exc)[:80]))
        assert not failures, failures

    def test_sample_urls_return_200_for_googlebot(self, url_entries):
        import random
        random.seed(1222)
        paths = [e["loc"].replace(SITEMAP_BASE, "") for e in url_entries]
        sample = random.sample(paths, 25)
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
        failures = []
        for p in sample:
            try:
                r = requests.get(f"{BASE_URL}{p}", headers=headers, timeout=45)
                # NOTE: the preview ingress adds a global X-Robots-Tag: noindex,nofollow to
                # every response, so only the status code is asserted here.
                if r.status_code != 200:
                    failures.append((p, r.status_code))
            except Exception as exc:
                failures.append((p, str(exc)[:80]))
        assert not failures, failures


# ---------- Schema enrichment breadth (all blogs, product sample) ----------
class TestSchemaBreadth:
    def test_all_blog_urls_in_sitemap_return_faq_schema(self, url_entries):
        paths = [e["loc"].replace(SITEMAP_BASE, "") for e in url_entries
                 if e["loc"].startswith(SITEMAP_BASE + "/blog/")]
        assert paths
        missing = []
        for p in paths:
            d = _get_meta(p).json()
            types, _ = _schema_types(d)
            if "FAQPage" not in types:
                missing.append((p, types))
        assert not missing, missing

    def test_product_sample_returns_product_and_faq_schema(self, url_entries):
        import random
        random.seed(7)
        paths = [e["loc"].replace(SITEMAP_BASE, "") for e in url_entries
                 if e["loc"].startswith(SITEMAP_BASE + "/products/")]
        sample = random.sample(paths, 12)
        bad = []
        for p in sample:
            d = _get_meta(p).json()
            types, _ = _schema_types(d)
            if "Product" not in types or "FAQPage" not in types:
                bad.append((p, types))
        assert not bad, bad

    def test_faq_schema_questions_wellformed(self):
        d = _get_meta("/blog/cob-led-technology-explained").json()
        _, schema = _schema_types(d)
        faq = [s for s in schema if s.get("@type") == "FAQPage"][0]
        assert len(faq["mainEntity"]) >= 2
        for q in faq["mainEntity"]:
            assert q["@type"] == "Question"
            assert q["name"].strip()
            assert q["acceptedAnswer"]["@type"] == "Answer"
            assert q["acceptedAnswer"]["text"].strip()


# ---------- Sitemap must not list URLs that 301-redirect (GSC "Page with redirect") ----------
class TestSitemapNoRedirects:
    def test_no_sitemap_url_redirects(self, url_entries):
        gb = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
        redirecting = []
        for e in url_entries:
            p = e["loc"].replace(SITEMAP_BASE, "") or "/"
            r = requests.get(f"{BASE_URL}{p}", headers=gb, timeout=45, allow_redirects=False)
            if 300 <= r.status_code < 400:
                redirecting.append((p, r.status_code, r.headers.get("location")))
        assert not redirecting, f"{len(redirecting)} sitemap URLs redirect: {redirecting}"


# ---------- DB-vs-sitemap coverage gap (status filter on collections without a status field) ----------
class TestPixelVueCoverage:
    def test_all_pixelvue_products_in_sitemap(self, url_entries):
        import asyncio
        from dotenv import load_dotenv
        load_dotenv("/app/backend/.env")
        from motor.motor_asyncio import AsyncIOMotorClient

        async def slugs():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            return [p["slug"] async for p in db["pixelvue_products"].find({}, {"slug": 1})
                    if p.get("slug")]

        db_slugs = asyncio.run(slugs())
        assert db_slugs, "no pixelvue products in DB"
        sm = {e["loc"] for e in url_entries}
        missing = [s for s in db_slugs if f"{SITEMAP_BASE}/pixelvue/{s}" not in sm]
        assert not missing, f"{len(missing)}/{len(db_slugs)} pixelvue product pages missing from sitemap: {missing}"
