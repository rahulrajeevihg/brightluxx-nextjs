from datetime import datetime
from collections import defaultdict
from fastapi import Request
import re
import time


def serialize_doc(doc):
    if doc is None:
        return None
    if "_id" in doc:
        if "id" not in doc:
            doc["id"] = str(doc["_id"])
        del doc["_id"]
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max = max_attempts
        self.window = window_seconds
        self.attempts = defaultdict(list)

    def check(self, ip: str) -> bool:
        now = time.time()
        self.attempts[ip] = [t for t in self.attempts[ip] if now - t < self.window]
        if len(self.attempts[ip]) >= self.max:
            return False
        self.attempts[ip].append(now)
        return True

    def remaining(self, ip: str) -> int:
        now = time.time()
        self.attempts[ip] = [t for t in self.attempts[ip] if now - t < self.window]
        return max(0, self.max - len(self.attempts[ip]))

    def reset(self, ip: str):
        self.attempts.pop(ip, None)


login_limiter = RateLimiter(max_attempts=5, window_seconds=60)
lead_limiter = RateLimiter(max_attempts=10, window_seconds=60)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
