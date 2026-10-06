"""
Anti-spam utilities for lead form submissions.
Provides honeypot validation, disposable email blocking,
content quality checks, rate limiting, reCAPTCHA v3 verification,
geo IP enrichment, country filtering, and phone validation.
"""
import os
import re
import time
import logging
from collections import defaultdict

import httpx
from fastapi import HTTPException

logger = logging.getLogger("anti_spam")

# reCAPTCHA v3 configuration (optional — graceful degradation if not set)
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))

# ── Target markets (ISO 3166-1 alpha-2) ──────────────────────────
# Primary: GCC countries
GCC_COUNTRIES = {"AE", "SA", "QA", "KW", "BH", "OM"}
# Secondary: Wider MENA + key business/expat markets
MENA_COUNTRIES = {"EG", "JO", "LB", "IQ", "MA", "TN", "LY", "PS", "SY", "YE"}
BUSINESS_COUNTRIES = {"IN", "PK", "GB", "US", "DE", "FR", "CN", "TR", "ZA", "AU", "SG", "HK"}
ALLOWED_COUNTRIES = GCC_COUNTRIES | MENA_COUNTRIES | BUSINESS_COUNTRIES

# ── Phone country codes for target markets ───────────────────────
VALID_PHONE_CODES = {
    "+971": "AE", "+966": "SA", "+974": "QA", "+965": "KW", "+973": "BH", "+968": "OM",
    "+20": "EG", "+962": "JO", "+961": "LB", "+964": "IQ", "+212": "MA", "+216": "TN",
    "+91": "IN", "+92": "PK", "+44": "GB", "+1": "US", "+49": "DE", "+33": "FR",
    "+86": "CN", "+90": "TR", "+27": "ZA", "+61": "AU", "+65": "SG", "+852": "HK",
    "+218": "LY", "+963": "SY", "+967": "YE", "+970": "PS",
}

# Phone digit extraction
DIGITS_ONLY_RE = re.compile(r'\D')

# Disposable/temporary email domains (top 80 most common)
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    "dispostable.com", "trashmail.com", "10minutemail.com", "temp-mail.org",
    "fakeinbox.com", "mailnesia.com", "maildrop.cc", "tempail.com",
    "mohmal.com", "burnermail.io", "inboxkitten.com", "emailondeck.com",
    "getnada.com", "mailsac.com", "harakirimail.com", "dropmail.me",
    "minuteinbox.com", "tempr.email", "mytemp.email", "luxusmail.org",
    "mailforspam.com", "spamgourmet.com", "trashinbox.com", "temp-mail.io",
    "tmpmail.net", "tmpmail.org", "spambox.us", "bobmail.info",
    "devnullmail.com", "discard.email", "discardmail.com", "guerrillamail.info",
    "jetable.org", "mailcatch.com", "maildx.com", "mailexpire.com",
    "mailinator.net", "mailme.lv", "meltmail.com", "mt2015.com",
    "nospam.ze.tc", "putmail.net", "rmqkr.net", "spam4.me",
    "spamfree24.org", "tempomail.fr", "throwam.com", "trashmail.me",
    "trashmail.net", "trbvm.com", "wegwerfmail.de", "yepmail.net",
    "crazymailing.com", "mailnull.com", "nomail.xl.cx", "0-mail.com",
    "mailsucker.net", "binkmail.com", "bobmail.info", "bofthew.com",
    "clrmail.com", "cool.fr.nf", "courriel.fr.nf", "dcemail.com",
    "disposemail.com", "eintagsmail.de", "emailgo.de", "emailisvalid.com",
    "emailresort.com", "emz.net", "fiifke.de", "flurred.com",
    "get-mail.cf", "ghosttexter.de", "girlsundertheinfluence.com",
}

# Known spam patterns in messages
SPAM_PATTERNS = [
    r"(?i)buy\s+(?:viagra|cialis|crypto|bitcoin)",
    r"(?i)(?:click|visit)\s+(?:here|now|this)\s+(?:http|www)",
    r"(?i)(?:earn|make)\s+\$\d+.*(?:per|a)\s+(?:day|hour|week)",
    r"(?i)(?:free|cheap)\s+(?:iphone|gift|money|card)",
    r"(?i)(?:hot|sexy)\s+(?:girl|lady|women|single)",
    r"(?i)(?:casino|poker|lottery|jackpot|slot)",
    r"(?i)(?:nigerian|prince|inheritance|beneficiary)",
    r"https?://\S+\.(?:ru|cn|tk|ml|ga|cf|gq)/",
    r"(?i)(?:weight\s*loss|diet\s*pill|fat\s*burn)",
    r"(?i)(?:seo\s+service|backlink|rank\s+#1|page\s+rank)",
]

# Fields that look like gibberish (random keyboard mashing)
GIBBERISH_RE = re.compile(r'^[bcdfghjklmnpqrstvwxyz]{5,}$', re.I)

# Valid email regex
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Rate limiter per IP
_rate_store = defaultdict(list)
RATE_WINDOW = 3600  # 1 hour
RATE_LIMIT = 10  # max submissions per hour per IP


def validate_email(email: str) -> tuple:
    """Validate email format and check for disposable domains.
    Returns (is_valid, error_message)."""
    if not email or not EMAIL_RE.match(email):
        return False, "Please enter a valid email address."
    
    domain = email.split("@")[1].lower()
    if domain in DISPOSABLE_DOMAINS:
        return False, "Please use a business or personal email, not a temporary address."
    
    # Check for obviously fake patterns
    local = email.split("@")[0].lower()
    if local in ("test", "asdf", "qwerty", "aaa", "xxx", "123", "admin", "info"):
        return False, "Please enter your real email address."
    
    if GIBBERISH_RE.match(local):
        return False, "Please enter a valid email address."
    
    return True, ""


def validate_honeypot(data: dict) -> bool:
    """Check if honeypot field was filled (bots fill hidden fields).
    Returns True if submission is spam (honeypot triggered)."""
    hp = data.get("website", "") or data.get("company_url", "") or data.get("fax", "")
    return bool(hp)


def validate_content_quality(name: str, message: str = "", company: str = "") -> tuple:
    """Check for minimum content quality.
    Returns (is_valid, error_message)."""
    # Name checks
    if not name or len(name.strip()) < 2:
        return False, "Please enter your name."
    
    if GIBBERISH_RE.match(name.replace(" ", "")):
        return False, "Please enter a valid name."
    
    # Check for spam patterns in message
    if message:
        for pattern in SPAM_PATTERNS:
            if re.search(pattern, message):
                return False, "Your message was flagged as potential spam. Please rephrase."
        
        # Count URLs in message — too many is spam
        url_count = len(re.findall(r'https?://', message))
        if url_count > 2:
            return False, "Too many links in your message. Please remove some."
    
    return True, ""


def check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded the submission rate limit.
    Returns True if allowed, False if rate limited.
    Does NOT record the attempt — call record_submission() after acceptance."""
    now = time.time()
    
    # Clean old entries
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
    
    return len(_rate_store[ip]) < RATE_LIMIT


def record_submission(ip: str):
    """Record a successful submission for rate limiting."""
    _rate_store[ip].append(time.time())
    stale = [k for k, v in _rate_store.items() if not v]
    for k in stale:
        del _rate_store[k]


# ── Geo IP cache (avoid repeated lookups for same IP) ────────────
_geo_cache = {}
_GEO_CACHE_TTL = 3600  # 1 hour


async def lookup_geo_ip(ip: str) -> dict:
    """Look up geographic location for an IP address.
    Returns {"country": "AE", "country_name": "United Arab Emirates", "city": "Dubai", "region": "Dubai", ...}
    Uses ip-api.com (free, no key, 45 req/min)."""
    if not ip or ip in ("127.0.0.1", "localhost", "::1"):
        return {"country": "", "country_name": "", "city": "", "region": "", "isp": "", "query": ip}

    # Check cache
    cached = _geo_cache.get(ip)
    if cached and time.time() - cached["_ts"] < _GEO_CACHE_TTL:
        return cached

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,isp,query")
        data = resp.json()
        if data.get("status") == "success":
            result = {
                "country": data.get("countryCode", ""),
                "country_name": data.get("country", ""),
                "city": data.get("city", ""),
                "region": data.get("regionName", ""),
                "isp": data.get("isp", ""),
                "query": ip,
                "_ts": time.time(),
            }
            _geo_cache[ip] = result
            if len(_geo_cache) > 5000:
                _geo_cache.clear()
            return result
    except Exception as e:
        logger.warning("Geo IP lookup failed for %s: %s", ip, e)

    return {"country": "", "country_name": "", "city": "", "region": "", "isp": "", "query": ip}


def validate_phone(phone: str) -> tuple:
    """Validate phone number format and country code.
    Returns (is_valid, error_message, detected_country_code)."""
    if not phone or not phone.strip():
        return True, "", ""  # Phone is optional on many forms

    cleaned = phone.strip()

    # Must have some digits
    digits = DIGITS_ONLY_RE.sub("", cleaned)
    if len(digits) < 7:
        return False, "Please enter a valid phone number with country code (e.g. +971 50 123 4567).", ""

    if len(digits) > 15:
        return False, "Phone number is too long. Please check and try again.", ""

    # Check for valid country code
    if cleaned.startswith("+") or cleaned.startswith("00"):
        normalized = "+" + digits.lstrip("0") if cleaned.startswith("00") else "+" + digits
        for code, country in sorted(VALID_PHONE_CODES.items(), key=lambda x: -len(x[0])):
            if normalized.startswith(code):
                remaining = digits[len(code.replace("+", "")):]
                if len(remaining) >= 6:
                    return True, "", country
        # Has + prefix but unrecognized code
        return True, "", "OTHER"

    # No country code — could be local format
    # UAE local numbers: 05x xxx xxxx (10 digits) or 04 xxx xxxx (9 digits)
    if len(digits) >= 9 and digits[0] == "0":
        return True, "", "AE_LOCAL"

    return True, "", "UNKNOWN"


def check_country_allowed(geo_country: str, phone_country: str) -> tuple:
    """Check if the lead is from an allowed country.
    Uses OR logic: allowed if geo IP is in target list OR phone has target country code.
    Returns (is_allowed, error_message)."""
    # If no geo data, allow (don't block on lookup failure)
    if not geo_country:
        return True, ""

    # Country is in allowed list
    if geo_country in ALLOWED_COUNTRIES:
        return True, ""

    # Not in allowed list, but phone has a target market code
    if phone_country and phone_country in ALLOWED_COUNTRIES:
        return True, ""

    # UAE local number format
    if phone_country == "AE_LOCAL":
        return True, ""

    return False, "We currently serve the UAE, GCC, and Middle East region. For inquiries outside this area, please email sales@brightluxx.com directly."


def compute_spam_score(data: dict, geo_data: dict = None) -> int:
    """Compute a spam likelihood score (0-100). Higher = more likely spam.
    Score >= 70 is considered spam."""
    score = 0
    
    name = data.get("name", "")
    email = data.get("email", "")
    message = data.get("message", "") or ""
    phone = data.get("phone", "")
    
    # Honeypot filled
    if validate_honeypot(data):
        score += 80
    
    # Disposable email
    if email and "@" in email:
        domain = email.split("@")[1].lower()
        if domain in DISPOSABLE_DOMAINS:
            score += 40
        # Free email providers — slight penalty for B2B context
        elif domain in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "mail.com", "protonmail.com"):
            score += 5
    
    # No phone number provided (for business inquiries, unusual)
    if not phone:
        score += 10
    
    # Very short name
    if len(name) < 3:
        score += 15
    
    # Gibberish name
    if GIBBERISH_RE.match(name.replace(" ", "")):
        score += 30
    
    # Spam patterns in message
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, message):
            score += 25
            break
    
    # Too many URLs in message
    if len(re.findall(r'https?://', message)) > 2:
        score += 20
    
    # All-caps message
    if message and message == message.upper() and len(message) > 20:
        score += 15
    
    # Very short or empty message for a contact form
    if len(message) < 10 and data.get("source") == "contact_form":
        score += 10

    # Geo-based scoring (applied as bonus/penalty, not absolute)
    if geo_data:
        country = geo_data.get("country", "")
        if country and country not in ALLOWED_COUNTRIES:
            score += 20  # Penalty for non-target country
    
    return max(0, min(score, 100))


async def validate_submission_full(data: dict, ip: str) -> tuple:
    """Full async validation pipeline with geo IP enrichment.
    Returns (is_valid, error_message, spam_score, geo_data).
    Only records rate-limit slot on accepted submissions."""

    # Rate limit check (does not consume a slot)
    if not check_rate_limit(ip):
        return False, "Too many submissions. Please try again later.", 100, {}

    # Honeypot
    if validate_honeypot(data):
        return False, "__honeypot__", 100, {}

    # Email validation
    email_valid, email_err = validate_email(data.get("email", ""))
    if not email_valid:
        return False, email_err, 80, {}

    # Phone validation
    phone = data.get("phone", "")
    phone_valid, phone_err, phone_country = validate_phone(phone)
    if not phone_valid:
        return False, phone_err, 70, {}

    # Content quality
    content_valid, content_err = validate_content_quality(
        data.get("name", ""),
        data.get("message", ""),
        data.get("company", ""),
    )
    if not content_valid:
        return False, content_err, 60, {}

    # Geo IP lookup
    geo_data = await lookup_geo_ip(ip)
    geo_country = geo_data.get("country", "")

    # Country + phone combined check
    country_ok, country_err = check_country_allowed(geo_country, phone_country)
    if not country_ok:
        logger.info("Blocked lead from %s (IP: %s, phone country: %s)", geo_country, ip, phone_country)
        return False, country_err, 90, geo_data

    # Spam score (includes geo factors)
    spam_score = compute_spam_score(data, geo_data)
    if spam_score >= 70:
        return False, "Your submission was flagged for review. If this is a genuine inquiry, please email us directly.", spam_score, geo_data

    # Accepted — record for rate limiting
    record_submission(ip)
    return True, "", spam_score, geo_data


def validate_submission(data: dict, ip: str) -> tuple:
    """Synchronous validation pipeline (no geo IP).
    Returns (is_valid, error_message, spam_score).
    Used as fallback; prefer validate_submission_full for lead endpoints."""

    if not check_rate_limit(ip):
        return False, "Too many submissions. Please try again later.", 100

    if validate_honeypot(data):
        return False, "__honeypot__", 100

    email_valid, email_err = validate_email(data.get("email", ""))
    if not email_valid:
        return False, email_err, 80

    phone = data.get("phone", "")
    phone_valid, phone_err, _ = validate_phone(phone)
    if not phone_valid:
        return False, phone_err, 70

    content_valid, content_err = validate_content_quality(
        data.get("name", ""),
        data.get("message", ""),
        data.get("company", ""),
    )
    if not content_valid:
        return False, content_err, 60

    spam_score = compute_spam_score(data)
    if spam_score >= 70:
        return False, "Your submission was flagged for review. If this is a genuine inquiry, please email us directly.", spam_score

    record_submission(ip)
    return True, "", spam_score


async def verify_recaptcha(token: str, ip: str = None) -> dict:
    """Verify a reCAPTCHA v3 token with Google.
    Returns {"success": True, "score": float, ...} on success.
    Raises HTTPException on failure.
    Skips verification if RECAPTCHA_SECRET_KEY is not configured."""
    if not RECAPTCHA_SECRET_KEY:
        return {"success": True, "score": 1.0, "skipped": True}

    if not token:
        raise HTTPException(status_code=422, detail="Security verification required. Please try again.")

    data = {"secret": RECAPTCHA_SECRET_KEY, "response": token}
    if ip:
        data["remoteip"] = ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        logger.warning("reCAPTCHA verification unavailable: %s", e)
        return {"success": True, "score": 0.5, "error": "verification_unavailable"}

    if not result.get("success"):
        logger.warning("reCAPTCHA verification failed: %s", result.get("error-codes"))
        raise HTTPException(status_code=422, detail="Security verification failed. Please refresh and try again.")

    score = float(result.get("score", 0))
    if score < RECAPTCHA_MIN_SCORE:
        logger.info("reCAPTCHA low score %.2f for IP %s", score, ip)
        raise HTTPException(status_code=422, detail="Your submission was flagged as suspicious. Please try again or contact us directly.")

    return result


async def check_recaptcha(request) -> dict:
    """One-line helper to verify reCAPTCHA from a FastAPI Request.
    Reads the token from X-Recaptcha-Token header.
    Returns the verification result dict.
    Gracefully skips if RECAPTCHA_SECRET_KEY is not set."""
    from utils import get_client_ip
    token = request.headers.get("x-recaptcha-token", "")
    ip = get_client_ip(request)
    return await verify_recaptcha(token, ip)
