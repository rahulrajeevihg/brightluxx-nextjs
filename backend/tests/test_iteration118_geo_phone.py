"""Iteration 118 — Geo IP enrichment, country filtering, phone validation (E.164)
plus anti-spam regression across all lead endpoints.

Rate limiter is in-memory per-IP (10/hour) keyed off X-Forwarded-For, so each
request uses a unique UAE IP (94.200.x.y = Etisalat/du, resolves to AE) unless a
test specifically needs another country.
"""
import asyncio
import os
import sys
import uuid

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

TIMEOUT = 45


def uae_ip():
    """Unique UAE (AE) client IP so the shared rate limiter doesn't interfere."""
    n = uuid.uuid4().int
    return "94.200.%d.%d" % (n % 250 + 1, (n >> 9) % 250 + 1)


def ip_headers(ip=None, extra=None):
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip or uae_ip()}
    if extra:
        h.update(extra)
    return h


def email(tag):
    return f"TEST_i118_{tag}_{uuid.uuid4().hex[:6]}@brightretail.ae"


def lead_payload(**over):
    p = {
        "name": "TEST Ahmed Khan",
        "company": "TEST Retail LLC",
        "email": email("lead"),
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
def leads_col():
    if not MONGO_URL or not DB_NAME:
        pytest.skip("MONGO_URL/DB_NAME not configured")
    c = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    yield c[DB_NAME]["leads"]
    c.close()


# ── Backend health ────────────────────────────────────────────────
def test_health(client):
    r = client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.json().get("status") == "ok"


# ── anti_spam unit level: lookup_geo_ip / validate_phone / country ──
class TestAntiSpamUnits:
    def test_lookup_geo_ip_public_ip(self):
        import anti_spam
        geo = asyncio.run(anti_spam.lookup_geo_ip("94.200.5.9"))
        assert geo["country"] == "AE", geo
        assert geo["country_name"] == "United Arab Emirates"
        assert geo["city"]
        assert geo["isp"]

    def test_lookup_geo_ip_private_and_localhost(self):
        import anti_spam
        for ip in ("127.0.0.1", "::1", "10.1.2.3", ""):
            geo = asyncio.run(anti_spam.lookup_geo_ip(ip))
            assert geo["country"] == "", (ip, geo)

    def test_lookup_geo_ip_cached(self):
        import anti_spam
        asyncio.run(anti_spam.lookup_geo_ip("8.8.8.8"))
        assert "8.8.8.8" in anti_spam._geo_cache
        geo = asyncio.run(anti_spam.lookup_geo_ip("8.8.8.8"))
        assert geo["country"] == "US"

    @pytest.mark.parametrize("phone,valid,country", [
        ("", True, ""),
        ("   ", True, ""),
        ("12", False, ""),
        ("123456", False, ""),
        ("0501234567", True, "AE_LOCAL"),
        ("+971501234567", True, "AE"),
        ("+966501234567", True, "SA"),
        ("+974 5512 3456", True, "QA"),
        ("+1 415 555 2671", True, "US"),
        ("00971501234567", True, "AE"),
        ("+1234567890123456", False, ""),
        ("+99912345678", True, "OTHER"),
    ])
    def test_validate_phone(self, phone, valid, country):
        import anti_spam
        is_valid, err, detected = anti_spam.validate_phone(phone)
        assert is_valid is valid, (phone, err)
        if valid:
            assert detected == country, (phone, detected)
        else:
            assert err

    def test_check_country_allowed_or_logic(self):
        import anti_spam
        # geo allowed
        assert anti_spam.check_country_allowed("AE", "")[0] is True
        assert anti_spam.check_country_allowed("US", "")[0] is True
        # geo blocked, phone country in target list -> allowed (OR)
        assert anti_spam.check_country_allowed("JP", "AE")[0] is True
        assert anti_spam.check_country_allowed("JP", "AE_LOCAL")[0] is True
        # geo blocked, no useful phone -> blocked
        allowed, err = anti_spam.check_country_allowed("JP", "")
        assert allowed is False
        assert "UAE, GCC" in err
        assert anti_spam.check_country_allowed("JP", "OTHER")[0] is False
        # no geo data -> fail open
        assert anti_spam.check_country_allowed("", "")[0] is True

    def test_spam_score_geo_factors(self):
        import anti_spam
        base = {"name": "Ahmed Khan", "email": "a@corp.ae", "phone": "+971501234567",
                "message": "Need a P2.5 LED wall for our lobby."}
        none = anti_spam.compute_spam_score(base, None)
        bad = anti_spam.compute_spam_score(base, {"country": "JP"})
        assert bad == none + 20, (none, bad)

    def test_spam_score_free_email_higher_than_corporate(self):
        import anti_spam
        corp = {"name": "Ahmed Khan", "email": "ahmed@corp.ae", "phone": "+971501234567",
                "message": "Need a P2.5 LED wall for our lobby."}
        free = dict(corp, email="ahmed.khan@gmail.com")
        s_corp = anti_spam.compute_spam_score(corp, None)
        s_free = anti_spam.compute_spam_score(free, None)
        assert s_free > s_corp, (s_corp, s_free)
        assert s_free < 70

    def test_gcc_bonus_does_not_flatten_scores_to_zero(self):
        """KNOWN ISSUE: the -10 GCC bonus + max(0, ...) clamp makes low-signal
        leads indistinguishable (gmail and corporate both score 0 from a GCC IP),
        so the free-email penalty is lost for the primary market."""
        import anti_spam
        corp = {"name": "Ahmed Khan", "email": "ahmed@corp.ae", "phone": "+971501234567",
                "message": "Need a P2.5 LED wall for our lobby."}
        free = dict(corp, email="ahmed.khan@gmail.com")
        s_corp = anti_spam.compute_spam_score(corp, {"country": "AE"})
        s_free = anti_spam.compute_spam_score(free, {"country": "AE"})
        assert s_free > s_corp, (s_corp, s_free)


# ── Geo enrichment persisted on the lead document ──────────────────
class TestGeoPersistence:
    def test_lead_stores_geo_ae(self, client, leads_col):
        addr = uae_ip()
        payload = lead_payload(email=email("geoae"))
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(addr), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True
        doc = leads_col.find_one({"email": payload["email"]})
        assert doc is not None, "lead not persisted"
        assert doc.get("ip") == addr
        geo = doc.get("geo")
        assert isinstance(geo, dict), doc
        assert geo.get("country") == "AE", geo
        assert geo.get("country_name") == "United Arab Emirates"
        assert geo.get("city"), geo
        assert isinstance(doc.get("spam_score"), int)

    def test_lead_stores_geo_us(self, client, leads_col):
        payload = lead_payload(email=email("geous"))
        r = client.post(f"{BASE_URL}/api/leads", json=payload,
                        headers=ip_headers("8.8.8.8"), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        doc = leads_col.find_one({"email": payload["email"]})
        assert doc and doc["geo"]["country"] == "US", doc.get("geo") if doc else None
        assert doc["geo"]["country_name"] == "United States"

    def test_quick_inquiry_stores_geo(self, client, leads_col):
        addr = uae_ip()
        em = email("qi")
        payload = {"name": "TEST Omar Aziz", "email": em, "phone": "+971503334444",
                   "message": "Need pricing for P3 outdoor screen.", "page_context": "products"}
        r = client.post(f"{BASE_URL}/api/quick-inquiry", json=payload, headers=ip_headers(addr), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        doc = leads_col.find_one({"email": em})
        assert doc is not None, "quick inquiry lead not persisted in leads collection"
        assert doc.get("geo", {}).get("country") == "AE", doc.get("geo")


# ── Country filtering through the API (OR logic) ───────────────────
class TestCountryFilter:
    BLOCKED_IP = "133.242.0.1"  # JP (not in ALLOWED_COUNTRIES)

    @pytest.fixture(scope="class", autouse=True)
    def ensure_blocked_country(self, client):
        r = requests.get(f"http://ip-api.com/json/{self.BLOCKED_IP}?fields=status,countryCode", timeout=15)
        d = r.json()
        import anti_spam
        if d.get("status") != "success" or d.get("countryCode") in anti_spam.ALLOWED_COUNTRIES:
            pytest.skip(f"probe IP resolves to allowed/unknown country: {d}")

    def test_blocked_country_without_target_phone(self, client):
        payload = lead_payload(email=email("jpblock"), phone="")
        r = client.post(f"{BASE_URL}/api/leads", json=payload,
                        headers=ip_headers(self.BLOCKED_IP), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
        assert "UAE, GCC" in r.json()["detail"]

    def test_blocked_country_with_gcc_phone_allowed(self, client):
        payload = lead_payload(email=email("jpallow"), phone="+971501234567")
        r = client.post(f"{BASE_URL}/api/leads", json=payload,
                        headers=ip_headers(self.BLOCKED_IP), timeout=TIMEOUT)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
        assert r.json().get("success") is True

    def test_blocked_country_with_uae_local_phone_allowed(self, client):
        payload = lead_payload(email=email("jplocal"), phone="0501234567")
        r = client.post(f"{BASE_URL}/api/leads", json=payload,
                        headers=ip_headers(self.BLOCKED_IP), timeout=TIMEOUT)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"


# ── Phone validation via the API ──────────────────────────────────
class TestPhoneValidationAPI:
    @pytest.mark.parametrize("phone", ["12", "123456", "+1234567890123456", "0123456789012345678"])
    def test_invalid_phone_rejected(self, client, phone):
        payload = lead_payload(email=email("badphone"), phone=phone)
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{phone} -> {r.status_code}: {r.text[:300]}"
        assert "phone" in r.json()["detail"].lower()

    @pytest.mark.parametrize("phone", ["0501234567", "+971501234567", "+966501234567", "+974 5512 3456", ""])
    def test_valid_phone_accepted(self, client, phone):
        payload = lead_payload(email=email("okphone"), phone=phone)
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, f"{phone!r} -> {r.status_code}: {r.text[:300]}"
        assert r.json().get("success") is True

    def test_gmail_lead_accepted(self, client):
        payload = lead_payload(email=f"TEST_i118_{uuid.uuid4().hex[:6]}@gmail.com")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]


# ── Anti-spam regression ──────────────────────────────────────────
class TestAntiSpamRegression:
    def test_disposable_email_rejected(self, client):
        payload = lead_payload(email="john.smith@mailinator.com")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, r.text[:300]
        assert "temporary" in r.json()["detail"].lower()

    def test_honeypot_fax_silently_accepted(self, client):
        payload = lead_payload(email="bot@example.com", fax="http://spam.example")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("leadId") == "ok"

    def test_spam_content_rejected(self, client):
        payload = lead_payload(email="john.smith@realco.com", message="buy viagra cheap online now")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, r.text[:300]
        assert "spam" in r.json()["detail"].lower()

    def test_gibberish_name_rejected(self, client):
        payload = lead_payload(name="hjkstrf", email="real.person@realco.ae")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, r.text[:300]
        assert "name" in r.json()["detail"].lower()

    def test_invalid_email_rejected(self, client):
        payload = lead_payload(email="not-an-email")
        r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, r.text[:300]

    def test_rate_limit_still_enforced(self, client):
        hdrs = ip_headers()
        for i in range(12):
            payload = lead_payload(email=email(f"rate{i}"), message=f"Rate limit probe {i} for an LED quote.")
            r = client.post(f"{BASE_URL}/api/leads", json=payload, headers=hdrs, timeout=TIMEOUT)
            if r.status_code == 422 and "Too many" in r.text:
                assert i >= 10, f"rate limited too early at request {i}"
                return
        pytest.fail("rate limit never triggered in 12 requests")


# ── Endpoint coverage with valid GCC data ─────────────────────────
class TestEndpointCoverage:
    def test_signage_inquiry(self, client):
        payload = {"name": "TEST Rashid Ali", "company": "TEST Signs LLC",
                   "email": email("signage"), "phone": "+971504445555",
                   "signage_type": "channel_letters",
                   "project_brief": "Storefront channel letters, 40cm height."}
        r = client.post(f"{BASE_URL}/api/signage-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_cpd_request(self, client):
        payload = {"name": "TEST Karim Zayed", "email": email("cpd"), "company": "TEST Arch Firm",
                   "role": "Architect", "phone": "+971507778888", "preferred_topic": "LED basics",
                   "preferred_format": "in-office", "message": "Schedule a lunch and learn."}
        r = client.post(f"{BASE_URL}/api/cpd/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_franchise_request(self, client):
        payload = {"name": "TEST Sara Nour", "company": "TEST Gulf Distribution",
                   "email": email("franchise"), "phone": "+966505556666",
                   "country": "Saudi Arabia", "city": "Riyadh",
                   "message": "We want to distribute Brightluxx LED products."}
        r = client.post(f"{BASE_URL}/api/franchise-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_technical_support(self, client):
        payload = {"name": "TEST Fatima Noor", "company": "TEST Hotel Group",
                   "email": email("support"), "phone": "+971506667777", "product": "P2.5 Indoor",
                   "issue_type": "display",
                   "description": "Two cabinets show flickering after firmware update."}
        r = client.post(f"{BASE_URL}/api/technical-support", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_specpack_download(self, client):
        payload = {"email": email("specpack"), "name": "TEST Hind Obaid",
                   "company": "TEST Retail Group", "role": "PM"}
        r = client.post(f"{BASE_URL}/api/specpacks/retail-hospitality/download",
                        json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("download_url")

    def test_site_visit_request(self, client):
        payload = {"name": "TEST Bilal Haq", "email": email("sitevisit"), "phone": "+971509990000",
                   "company": "TEST Mall Co", "project_brief": "Site survey for atrium LED."}
        r = client.post(f"{BASE_URL}/api/site-visit-request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("status") == "ok"

    def test_design_assist_request(self, client):
        payload = {"name": "TEST Nadia Salim", "email": email("design"), "company": "TEST Design Studio",
                   "role": "Designer", "phone": "+971508889999", "project_type": "retail",
                   "project_stage": "concept", "message": "Need help specifying a curved LED wall."}
        r = client.post(f"{BASE_URL}/api/design-assist/request", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_chat_lead(self, client):
        payload = {"session_id": f"TEST_i118_sess_{uuid.uuid4().hex[:8]}", "name": "TEST Maya Farid",
                   "email": email("chat"), "company": "TEST Event Co", "role": "Producer"}
        r = client.post(f"{BASE_URL}/api/chat/lead", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True

    def test_invalid_phone_rejected_on_signage(self, client):
        payload = {"name": "TEST Bad Phone", "company": "TEST Signs LLC", "email": email("badsign"),
                   "phone": "12", "signage_type": "channel_letters",
                   "project_brief": "Storefront channel letters, 40cm height."}
        r = client.post(f"{BASE_URL}/api/signage-inquiry", json=payload, headers=ip_headers(), timeout=TIMEOUT)
        assert r.status_code == 422, f"{r.status_code}: {r.text[:300]}"
