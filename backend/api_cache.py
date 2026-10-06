"""In-memory TTL cache middleware for hot public GET endpoints.
Cuts production response times from ~1-2s (DB latency) to ~ms after first hit.
Any non-GET /api request clears the cache so admin edits appear promptly.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

CACHEABLE_PREFIXES = (
    "/api/homepage-content",
    "/api/products",
    "/api/projects",
    "/api/site-settings",
    "/api/seo/page-meta",
    "/api/inspirations",
    "/api/product-families",
    "/api/blogs",
    "/api/case-studies",
    "/api/solutions",
    "/api/technologies",
    "/api/applications",
    "/api/pixelvue",
    "/api/taxonomy",
    "/api/resources",
    "/api/ssr/meta",
)

TTL = 300  # server-side cache seconds
BROWSER_CC = "public, max-age=60, stale-while-revalidate=300"
MAX_ENTRIES = 500

_store = {}


class APICacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path

        if request.method != "GET":
            response = await call_next(request)
            if path.startswith("/api"):
                _store.clear()
            return response

        if not path.startswith(CACHEABLE_PREFIXES) or "/admin" in path:
            return await call_next(request)

        key = f"{path}?{request.url.query}"
        now = time.time()
        hit = _store.get(key)
        if hit and hit[0] > now:
            return Response(
                content=hit[1],
                status_code=200,
                media_type=hit[2],
                headers={"Cache-Control": BROWSER_CC, "X-API-Cache": "HIT"},
            )

        response = await call_next(request)
        if response.status_code != 200:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        media = response.headers.get("content-type", "application/json")
        if len(_store) >= MAX_ENTRIES:
            _store.clear()
        _store[key] = (now + TTL, body, media)
        return Response(
            content=body,
            status_code=200,
            media_type=media,
            headers={"Cache-Control": BROWSER_CC, "X-API-Cache": "MISS"},
        )
