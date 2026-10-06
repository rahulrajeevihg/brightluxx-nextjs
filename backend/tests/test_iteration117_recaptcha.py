"""Iteration 117 — reCAPTCHA v3 graceful degradation + anti-spam regression.

Context: no RECAPTCHA_SECRET_KEY is configured, so check_recaptcha() must skip
verification entirely and every lead endpoint must keep working without an
X-Recaptcha-Token header.

Rate limiter is in-memory per-IP (10/hour) derived from X-Forwarded-For, so each
test sends a unique fake IP.
"""
import asyncio
import os
import sys
import uuid

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
BASE_URL = base_url.rstrip("/")

TIMEOUT = 45


def ip_headers(extra=None):
    """Unique per-request client IP so the shared rate limiter doesn't interfere."""
    n = uuid.uuid4().int
    ip = "203.0.%d.%d" % (n % 250 + 1, (n >> 8) % 250 + 1)
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip}
    if extra:
        h.update(extra)
    return h


@pytest.fixture(scope="module")
def client():
    return requests.Session()


# ── Module-level config: reCAPTCHA must be unconfigured (graceful degradation) ──
class TestRecaptchaConfig:
    def test_secret_key_not_configured(self):
        assert not os.environ.get("RECAPTCHA_SECRET_KEY"), "RECAPTCHA_SECRET_KEY unexpectedly set in test env"
        backend_env = dotenv_values("/app/backend/.env")
        assert not backend_env.get("RECAPTCHA_SECRET_KEY")

    def test_site_key_not_configured_frontend(self):
        assert not frontend_env.get("REACT_APP_RECAPTCHA_SITE_KEY")

    def test_verify_recaptcha_skips_when_unconfigured(self):
        sys.path.insert(0, "/app/backend")
        import anti_spam
        assert anti_spam.RECAPTCHA_SECRET_KEY == ""
        res = asyncio.run(anti_spam.verify_recaptcha("", "1.2.3.4"))
        assert res == {"success": True, "score": 1.0, "skipped": True}
        res2 = asyncio.run(anti_spam.verify_recaptcha("some-garbage-token", "1.2.3.4"))
        assert res2.get("skipped") is True


# ── Backend health ─────────────────────────────────────────────────
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("status") == "ok"


# ── All lead endpoints WITHOUT X-Recaptcha-Token header ────────────
class TestLeadEndpointsNoToken:
    def test_leads(self, client):
        payload = {"name": "TEST Ahmed Khan", "company": "TEST Retail LLC",
                   "email": f"TEST_i117_{uuid.uuid4().hex[:6]}@brightretail.ae",
                   "phone": "+971501234567", "city": "Dubai", "application": "Retail",
                   "message": "We need a P2.5 indoor LED wall for our new flagship store lobby."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        assert data["success"] is True
        assert data.get("leadId") and data["leadId"] != "ok"

    def test_quick_inquiry(self, client):
        payload = {"name": "TEST Omar Aziz", "email": "TEST_i117_omar@dubaimalls.ae",
                   "phone": "+971503334444", "message": "Need pricing for P3 outdoor screen.",
                   "page_context": "products"}
        r = client.post(f"{BASE_URL}/api/quick-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_signage_inquiry(self, client):
        payload = {"name": "TEST Rashid Ali", "company": "TEST Signs LLC",
                   "email": "TEST_i117_rashid@signsllc.ae", "phone": "+971504445555",
                   "signage_type": "channel_letters",
                   "project_brief": "Storefront channel letters, 40cm height."}
        r = client.post(f"{BASE_URL}/api/signage-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_franchise_request(self, client):
        payload = {"name": "TEST Sara Nour", "company": "TEST Gulf Distribution",
                   "email": "TEST_i117_sara@gulfdist.com", "phone": "+971505556666",
                   "country": "UAE", "city": "Abu Dhabi",
                   "message": "We want to distribute Brightluxx LED products in the region."}
        r = client.post(f"{BASE_URL}/api/franchise-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_cpd_request(self, client):
        payload = {"name": "TEST Karim Zayed", "email": "TEST_i117_karim@archfirm.ae",
                   "company": "TEST Arch Firm", "role": "Architect", "phone": "+971507778888",
                   "preferred_topic": "LED basics", "preferred_format": "in-office",
                   "message": "Please schedule a lunch and learn for our design team."}
        r = client.post(f"{BASE_URL}/api/cpd/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_design_assist_request(self, client):
        payload = {"name": "TEST Nadia Salim", "email": "TEST_i117_nadia@designstudio.ae",
                   "company": "TEST Design Studio", "role": "Designer", "phone": "+971508889999",
                   "project_type": "retail", "project_stage": "concept",
                   "message": "Need help specifying a curved LED feature wall."}
        r = client.post(f"{BASE_URL}/api/design-assist/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_specpack_download(self, client):
        payload = {"email": "TEST_i117_specpack@retailgroup.ae", "name": "TEST Hind Obaid",
                   "company": "TEST Retail Group", "role": "PM"}
        r = client.post(f"{BASE_URL}/api/specpacks/retail-hospitality/download",
                        json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("download_url") == "/api/specpacks/retail-hospitality/file"

    def test_cheatsheet_download(self, client):
        payload = {"email": "TEST_i117_cheat@retailgroup.ae", "name": "TEST Yusuf Amin",
                   "company": "TEST Retail Group", "role": "PM"}
        r = client.post(f"{BASE_URL}/api/downloads/cheatsheet/pixel-pitch-cheatsheet/request",
                        json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("download_url")

    def test_chat_lead(self, client):
        payload = {"session_id": f"TEST_i117_sess_{uuid.uuid4().hex[:8]}", "name": "TEST Maya Farid",
                   "email": "TEST_i117_maya@eventco.ae", "company": "TEST Event Co", "role": "Producer"}
        r = client.post(f"{BASE_URL}/api/chat/lead", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_site_visit_request(self, client):
        payload = {"name": "TEST Bilal Haq", "email": "TEST_i117_bilal@mallco.ae",
                   "phone": "+971509990000", "company": "TEST Mall Co",
                   "project_brief": "Site survey for atrium LED installation."}
        r = client.post(f"{BASE_URL}/api/site-visit-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_technical_support(self, client):
        payload = {"name": "TEST Fatima Noor", "company": "TEST Hotel Group",
                   "email": "TEST_i117_fatima@hotelgrp.ae", "phone": "+971506667777",
                   "product": "P2.5 Indoor", "issue_type": "display",
                   "description": "Two cabinets show flickering after firmware update."}
        r = client.post(f"{BASE_URL}/api/technical-support", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_supplier_registration(self, client):
        payload = {"company_name": "TEST LED Components Co", "contact_person": "TEST Wei Chen",
                   "email": "TEST_i117_wei@ledcomp.com", "phone": "+8613800000000",
                   "country": "China", "product_category": "Modules",
                   "message": "We supply P1.5 COB modules with 3-year warranty."}
        r = client.post(f"{BASE_URL}/api/supplier-registration", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_project_planner_pdf_with_lead(self, client):
        payload = {"name": "TEST Ravi Menon", "email": "TEST_i117_ravi@plannerco.ae",
                   "phone": "+971501010101", "company": "TEST Planner Co",
                   "project_name": "TEST Atrium Wall", "application": "Retail",
                   "width": 4.0, "height": 2.5, "environment": "indoor",
                   "viewing_distance": 3.0}
        r = client.post(f"{BASE_URL}/api/project-planner/pdf", json=payload,
                        headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]


# ── Bogus token header must be ignored while secret key is unset ────
class TestBogusTokenIgnored:
    def test_leads_with_garbage_token(self, client):
        payload = {"name": "TEST Token User", "email": f"TEST_i117_tok_{uuid.uuid4().hex[:6]}@realco.ae",
                   "phone": "+971502020202",
                   "message": "Testing that a bogus reCAPTCHA token is ignored when unconfigured."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload,
                        headers=ip_headers({"X-Recaptcha-Token": "not-a-real-token-" + uuid.uuid4().hex}),
                        timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_quick_inquiry_with_empty_token(self, client):
        payload = {"name": "TEST Empty Token", "email": "TEST_i117_empty@realco.ae",
                   "phone": "+971503030303", "message": "Empty reCAPTCHA header should be fine."}
        r = client.post(f"{BASE_URL}/api/quick-inquiry", json=payload,
                        headers=ip_headers({"X-Recaptcha-Token": ""}), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]


# ── Anti-spam regression (must still work with reCAPTCHA layer added) ──
class TestAntiSpamRegression:
    def test_disposable_email_rejected(self, client):
        payload = {"name": "John Smith", "email": "john.smith@mailinator.com",
                   "phone": "+971501111111", "message": "Interested in LED walls for retail."}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "temporary" in r.json()["detail"].lower()

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

    def test_spam_content_rejected(self, client):
        payload = {"name": "John Smith", "email": "john.smith@realco.com",
                   "phone": "+971501111111", "message": "buy viagra cheap online now"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "spam" in r.json()["detail"].lower()

    def test_invalid_email_rejected(self, client):
        payload = {"name": "John Smith", "email": "not-an-email", "phone": "+971501111111"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_too_many_links_rejected(self, client):
        payload = {"name": "John Smith", "email": "john@realco.com", "phone": "+971501111111",
                   "message": "see http://a.com and http://b.com plus http://c.com deals"}
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"

    def test_rate_limit_still_enforced(self, client):
        hdrs = ip_headers()
        for i in range(12):
            payload = {"name": f"TEST Rate User {i}", "email": f"TEST_i117_rate{i}@ratelimitco.ae",
                       "phone": "+971500000001", "message": f"Rate limit probe number {i} for LED quote."}
            r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=hdrs, timeout=TIMEOUT)
            if r.status_code == 422 and "Too many" in r.text:
                assert i >= 10, f"rate limited too early at request {i}"
                return
        pytest.fail("rate limit never triggered in 12 requests")
