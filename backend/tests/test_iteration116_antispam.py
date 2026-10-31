"""Iteration 116 — Anti-spam protection on all lead endpoints + SEO structure checks.

Rate limiter is in-memory per-IP (10/hour) and derived from X-Forwarded-For,
so each test uses a unique fake IP to stay independent.
"""
import os
import uuid
import time

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

TIMEOUT = 45


def ip_headers(tag=""):
    """Unique per-test client IP so the shared rate limiter doesn't interfere."""
    octets = uuid.uuid4().int
    ip = "203.0.%d.%d" % (octets % 250 + 1, (octets >> 8) % 250 + 1)
    return {"Content-Type": "application/json", "X-Forwarded-For": ip}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    return s


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post(f"{BASE_URL}/api/admin/login",
                    json={"email": "admin@brightluxx.com", "password": "brightluxx2026"},
                    timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.fail(f"admin login failed {r.status_code}: {r.text[:300]}")
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok
    return tok


# ── Backend health ────────────────────────────────────────────────
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("status") == "ok"


# ── POST /api/leads (contact form) ────────────────────────────────
class TestLeads:
    def test_valid_lead(self, client):
        payload = {"name": "TEST Ahmed Khan", "company": "TEST Retail LLC",
                   "email": "TEST_ahmed.khan@brightretail.ae", "phone": "+971501234567",
                   "city": "Dubai", "application": "Retail",
                   "message": "We need a P2.5 indoor LED wall for our new flagship store lobby."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        assert data["success"] is True
        assert data.get("leadId") and data["leadId"] != "ok"

    def test_honeypot_fax_silently_accepted(self, client):
        payload = {"name": "Bot Name", "email": "bot@example.com", "phone": "+971500000000",
                   "message": "hello there this is a bot", "fax": "http://spam.example"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("leadId") == "ok"

    def test_honeypot_website_silently_accepted(self, client):
        payload = {"name": "Bot Name", "email": "bot2@example.com", "phone": "+971500000000",
                   "website": "http://spam.example"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("leadId") == "ok"

    def test_disposable_email_rejected(self, client):
        payload = {"name": "John Smith", "email": "john.smith@mailinator.com",
                   "phone": "+971501111111", "message": "Interested in LED walls for retail."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "temporary" in r.json()["detail"].lower()

    def test_spam_content_rejected(self, client):
        payload = {"name": "John Smith", "email": "john.smith@realco.com",
                   "phone": "+971501111111", "message": "buy viagra cheap online now"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "spam" in r.json()["detail"].lower()

    def test_gibberish_name_rejected(self, client):
        payload = {"name": "bcdfgh", "email": "someone@realco.com", "phone": "+971501111111",
                   "message": "Interested in LED walls for our retail store project."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "name" in r.json()["detail"].lower()

    def test_invalid_email_format_rejected(self, client):
        payload = {"name": "John Smith", "email": "not-an-email", "phone": "+971501111111"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_too_many_links_rejected(self, client):
        payload = {"name": "John Smith", "email": "john@realco.com", "phone": "+971501111111",
                   "message": "see http://a.com and http://b.com plus http://c.com deals"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_spam_score_and_ip_persisted(self, client, admin_token):
        marker = f"TEST_persist_{uuid.uuid4().hex[:8]}"
        hdrs = ip_headers()
        payload = {"name": "TEST Layla Hassan", "email": f"{marker}@brightretail.ae",
                   "phone": "+971502223333", "message": f"Persistence check {marker} for LED wall quote."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=hdrs, timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        time.sleep(1)
        lr = client.get(f"{BASE_URL}/api/admin/leads?limit=100",
                        headers={"Authorization": f"Bearer {admin_token}"}, timeout=TIMEOUT)
        assert lr.status_code == 200, lr.text[:300]
        body = lr.json()
        leads = body if isinstance(body, list) else body.get("leads", [])
        match = [l for l in leads if l.get("email") == f"{marker}@brightretail.ae"]
        assert match, "created lead not returned by /api/admin/leads"
        lead = match[0]
        assert "spam_score" in lead and isinstance(lead["spam_score"], int)
        assert lead.get("ip") == hdrs["X-Forwarded-For"]
        # NOTE (reported): /api/admin/leads leaks stringified Mongo _id via serialize_doc


# ── Other lead endpoints ──────────────────────────────────────────
class TestOtherEndpoints:
    def test_quick_inquiry_valid(self, client):
        payload = {"name": "TEST Omar Aziz", "email": "TEST_omar@dubaimalls.ae",
                   "phone": "+971503334444", "message": "Need pricing for P3 outdoor screen.",
                   "page_context": "products"}
        r = client.post(f"{BASE_URL}/api/quick-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_quick_inquiry_honeypot(self, client):
        payload = {"name": "Bot", "email": "bot@x.com", "fax": "filled"}
        r = client.post(f"{BASE_URL}/api/quick-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("status") == "ok"

    def test_signage_inquiry_valid(self, client):
        payload = {"name": "TEST Rashid Ali", "company": "TEST Signs LLC",
                   "email": "TEST_rashid@signsllc.ae", "phone": "+971504445555",
                   "signage_type": "channel_letters", "project_brief": "Storefront channel letters, 40cm height."}
        r = client.post(f"{BASE_URL}/api/signage-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_signage_inquiry_disposable_email(self, client):
        payload = {"name": "Rashid Ali", "email": "rashid@yopmail.com", "phone": "+971504445555",
                   "signage_type": "channel_letters"}
        r = client.post(f"{BASE_URL}/api/signage-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_franchise_request_valid(self, client):
        payload = {"name": "TEST Sara Nour", "company": "TEST Gulf Distribution",
                   "email": "TEST_sara@gulfdist.com", "phone": "+971505556666",
                   "country": "UAE", "city": "Abu Dhabi",
                   "message": "We want to distribute Brightluxx LED products in the region."}
        r = client.post(f"{BASE_URL}/api/franchise-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_franchise_request_honeypot(self, client):
        payload = {"name": "Bot", "company": "Bot Co", "email": "bot@x.com", "phone": "1",
                   "country": "X", "city": "Y", "fax": "filled"}
        r = client.post(f"{BASE_URL}/api/franchise-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("success") is True

    def test_supplier_registration_valid_with_website(self, client):
        payload = {"company_name": "TEST LED Components Co", "contact_person": "TEST Wei Chen",
                   "email": "TEST_wei@ledcomp.com", "phone": "+8613800000000", "country": "China",
                   "product_category": "Modules", "website": "https://ledcomp.com",
                   "message": "We supply P1.5 COB modules with 3-year warranty."}
        r = client.post(f"{BASE_URL}/api/supplier-registration", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_technical_support_valid(self, client):
        payload = {"name": "TEST Fatima Noor", "company": "TEST Hotel Group",
                   "email": "TEST_fatima@hotelgrp.ae", "phone": "+971506667777",
                   "product": "P2.5 Indoor", "issue_type": "display",
                   "description": "Two cabinets show flickering after firmware update."}
        r = client.post(f"{BASE_URL}/api/technical-support", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_cpd_request_valid(self, client):
        payload = {"name": "TEST Karim Zayed", "email": "TEST_karim@archfirm.ae",
                   "company": "TEST Arch Firm", "role": "Architect", "phone": "+971507778888",
                   "preferred_topic": "LED basics", "preferred_format": "in-office",
                   "message": "Please schedule a lunch and learn for our design team."}
        r = client.post(f"{BASE_URL}/api/cpd/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_cpd_request_disposable_email(self, client):
        payload = {"name": "Karim Zayed", "email": "karim@guerrillamail.com", "company": "X",
                   "role": "Architect", "preferred_topic": "LED basics"}
        r = client.post(f"{BASE_URL}/api/cpd/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_design_assist_valid(self, client):
        payload = {"name": "TEST Nadia Salim", "email": "TEST_nadia@designstudio.ae",
                   "company": "TEST Design Studio", "role": "Designer", "phone": "+971508889999",
                   "project_type": "retail", "project_stage": "concept",
                   "message": "Need help specifying a curved LED feature wall."}
        r = client.post(f"{BASE_URL}/api/design-assist/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_specpack_download_valid(self, client):
        payload = {"email": "TEST_specpack@retailgroup.ae", "name": "TEST Hind Obaid",
                   "company": "TEST Retail Group", "role": "PM"}
        r = client.post(f"{BASE_URL}/api/specpacks/retail-hospitality/download",
                        json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        # NOTE (reported): success path omits "success" key (honeypot path returns it)
        assert data.get("download_url") == "/api/specpacks/retail-hospitality/file"

    def test_cheatsheet_download_valid(self, client):
        payload = {"email": "TEST_cheat@retailgroup.ae", "name": "TEST Yusuf Amin",
                   "company": "TEST Retail Group", "role": "PM"}
        r = client.post(f"{BASE_URL}/api/downloads/cheatsheet/pixel-pitch-cheatsheet/request",
                        json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("download_url")

    def test_chat_lead_valid(self, client):
        payload = {"session_id": f"TEST_sess_{uuid.uuid4().hex[:8]}", "name": "TEST Maya Farid",
                   "email": "TEST_maya@eventco.ae", "company": "TEST Event Co", "role": "Producer"}
        r = client.post(f"{BASE_URL}/api/chat/lead", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_site_visit_request_valid(self, client):
        payload = {"name": "TEST Bilal Haq", "email": "TEST_bilal@mallco.ae",
                   "phone": "+971509990000", "company": "TEST Mall Co",
                   "project_brief": "Site survey for atrium LED installation."}
        r = client.post(f"{BASE_URL}/api/site-visit-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"


# ── Rate limiting ─────────────────────────────────────────────────
def test_rate_limit_after_10_submissions(client):
    hdrs = ip_headers()
    statuses = []
    for i in range(12):
        payload = {"name": f"TEST Rate User {i}", "email": f"TEST_rate{i}@ratelimitco.ae",
                   "phone": "+971500000001", "message": f"Rate limit probe number {i} for LED quote."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=hdrs, timeout=TIMEOUT)
        statuses.append(r.status_code)
        if r.status_code == 422 and "Too many" in r.text:
            assert i >= 10, f"rate limited too early at request {i}"
            return
    pytest.fail(f"rate limit never triggered in 12 requests: {statuses}")


# ── SEO structure ─────────────────────────────────────────────────
def test_sitemap_and_robots(client):
    r = client.get(f"{BASE_URL}/sitemap.xml", timeout=TIMEOUT)
    assert r.status_code == 200
    assert "<urlset" in r.text or "<sitemapindex" in r.text
    rb = client.get(f"{BASE_URL}/robots.txt", timeout=TIMEOUT)
    assert rb.status_code == 200
    assert "sitemap" in rb.text.lower()
