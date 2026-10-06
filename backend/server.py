from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from datetime import datetime, timezone
import os
import uuid
import time
import asyncio

from database import admins_col, perf_col, analytics_col
from auth import pwd_context
from routes.public import router as public_router
from routes.admin import router as admin_router
from routes.admin_crud import router as admin_crud_router
from routes.upload import router as upload_router
from routes.analytics import router as analytics_router
from routes.specpacks import router as specpacks_router
from routes.spec_substitution import router as spec_sub_router
from routes.sitemap import router as sitemap_router
from routes.downloads import router as downloads_router
from routes.cpd import router as cpd_router
from routes.design_assist import router as design_assist_router
from routes.chat import router as chat_router
from routes.quick_inquiry import router as quick_inquiry_router
from routes.site_visit import router as site_visit_router
from routes.project_planner import router as project_planner_router
from routes.partners import router as partners_router
from routes.site_settings import router as site_settings_router
from routes.resources import router as resources_router
from routes.taxonomy import router as taxonomy_router
from routes.image_management import router as image_management_router
from routes.homepage import router as homepage_router
from routes.blog import router as blog_router
from routes.case_studies import router as case_studies_router
from routes.pixelvue import router as pixelvue_router
from routes.solutions_api import router as solutions_api_router
from routes.technologies_api import router as technologies_api_router
from routes.applications_api import router as applications_api_router
from routes.site_content import router as site_content_router
from routes.product_families import router as product_families_router
from routes.signage_inquiry import router as signage_inquiry_router
from routes.sync import router as sync_router
from routes.seo_manager import router as seo_manager_router
from routes.prerender import router as prerender_router
from routes.internal_links import router as internal_links_router
from routes.redirects import router as redirects_router
from routes.ssr_meta import router as ssr_meta_router
from routes.content_gen import router as content_gen_router
from routes.reviews import router as reviews_router
from routes.rebuild import router as rebuild_router
from routes.img_proxy import router as img_proxy_router

app = FastAPI()

# GZip compression for responses > 500 bytes
from api_cache import APICacheMiddleware
app.add_middleware(APICacheMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

cors_origins_str = os.environ.get("CORS_ORIGINS")
if not cors_origins_str:
    raise RuntimeError("CORS_ORIGINS must be configured with explicit allowed origins")
cors_origins = [origin.strip().rstrip("/") for origin in cors_origins_str.split(",") if origin.strip()]
if not cors_origins:
    raise RuntimeError("CORS_ORIGINS must contain at least one allowed origin")

# The managed production runtime may provide a wildcard origin. Browsers cannot
# combine wildcard CORS with credentialed cookies, so keep wildcard access
# non-credentialed while retaining credential support for explicit origin lists.
cors_allows_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allows_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

# Skip perf logging for high-frequency/static endpoints
_SKIP_PERF = {"/api/track", "/api/health", "/health"}


@app.get("/health")
async def health_check():
    """Kubernetes liveness/readiness probe."""
    return {"status": "ok"}

# Cacheable public endpoints (read-only, public data)
_CACHEABLE = {
    "/api/products", "/api/blogs", "/api/case-studies", "/api/resources",
    "/api/homepage-content", "/api/solutions", "/api/technologies",
    "/api/applications", "/api/product-families", "/api/site-settings",
    "/api/inspirations", "/api/projects", "/api/pixelvue/products",
    "/api/seo/page-meta", "/api/img", "/api/media",
}


@app.middleware("http")
async def perf_and_security(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = (time.monotonic() - start) * 1000

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    path = request.url.path

    # Cache-Control for public GET endpoints
    if request.method == "GET" and response.status_code == 200:
        # Admin endpoints must never be publicly cached — this covers both
        # /api/admin/* and CMS admin sub-paths like /api/product-families/admin/all.
        if path.startswith("/api/admin/") or "/admin/" in path:
            response.headers["Cache-Control"] = "no-store"
        elif any(path == p or path.startswith(p + "/") for p in _CACHEABLE):
            response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"

    # Non-blocking perf tracking
    if path.startswith("/api/") and not any(path.startswith(s) for s in _SKIP_PERF):
        asyncio.create_task(_log_perf(request.method, path, elapsed_ms, response.status_code))

    return response


async def _log_perf(method: str, path: str, elapsed_ms: float, status_code: int):
    """Fire-and-forget perf logging."""
    try:
        await perf_col.insert_one({
            "endpoint": f"{method} {path}",
            "response_time_ms": round(elapsed_ms, 1),
            "status_code": status_code,
            "ts": datetime.now(timezone.utc),
        })
    except Exception:
        pass


app.include_router(public_router)
app.include_router(admin_router)
app.include_router(admin_crud_router)
app.include_router(upload_router)
app.include_router(analytics_router)
app.include_router(specpacks_router)
app.include_router(spec_sub_router)
app.include_router(sitemap_router)
app.include_router(downloads_router)
app.include_router(cpd_router)
app.include_router(design_assist_router)
app.include_router(chat_router)
app.include_router(quick_inquiry_router)
app.include_router(site_visit_router)
app.include_router(project_planner_router)
app.include_router(partners_router)
app.include_router(site_settings_router)
app.include_router(resources_router)
app.include_router(taxonomy_router)
app.include_router(homepage_router)
app.include_router(blog_router)
app.include_router(case_studies_router)
app.include_router(pixelvue_router)
app.include_router(solutions_api_router)
app.include_router(technologies_api_router)
app.include_router(applications_api_router)
app.include_router(site_content_router)
app.include_router(product_families_router)
app.include_router(image_management_router)
app.include_router(signage_inquiry_router)
app.include_router(sync_router)
app.include_router(seo_manager_router)
app.include_router(prerender_router)
app.include_router(internal_links_router)
app.include_router(redirects_router)
app.include_router(ssr_meta_router)
app.include_router(content_gen_router)
app.include_router(reviews_router)
app.include_router(rebuild_router)
app.include_router(img_proxy_router)


@app.on_event("startup")
async def startup():
    # Create indexes for analytics collections
    try:
        await analytics_col.create_index([("ts", -1)])
        await analytics_col.create_index([("event", 1), ("ts", -1)])
        await perf_col.create_index([("ts", -1)])
        await perf_col.create_index([("endpoint", 1), ("ts", -1)])
        # Review indexes
        from database import db as idx_db
        await idx_db["reviews"].create_index([("product_slug", 1), ("status", 1)])
        await idx_db["reviews"].create_index([("id", 1)], unique=True)
        # Content collection indexes for fast public queries
        await idx_db["products"].create_index([("slug", 1)])
        await idx_db["products"].create_index([("category", 1), ("created_at", -1)])
        await idx_db["products"].create_index([("featured", 1)])
        await idx_db["projects"].create_index([("slug", 1)])
        await idx_db["projects"].create_index([("featured", 1), ("created_at", -1)])
        await idx_db["page_seo"].create_index([("path", 1)])
        await idx_db["blogs"].create_index([("slug", 1)])
        await idx_db["case_studies"].create_index([("slug", 1)])
        await idx_db["inspirations"].create_index([("category", 1)])
    except Exception:
        pass

    # Seed admin user — credentials come from the environment, never hardcoded.
    seed_email = os.environ.get("ADMIN_SEED_EMAIL", "admin@brightluxx.com")
    seed_password = os.environ.get("ADMIN_SEED_PASSWORD")
    existing = await admins_col.find_one({"email": seed_email})
    if not existing:
        if seed_password:
            await admins_col.insert_one({
                "id": str(uuid.uuid4()),
                "email": seed_email,
                "password": pwd_context.hash(seed_password),
                "name": "Admin",
                "role": "super_admin",
                "created_at": datetime.now(timezone.utc)
            })
            print(f"Admin user seeded: {seed_email}")
        else:
            print("ADMIN_SEED_PASSWORD not set — skipping admin seed.")

    # Seed content collections from seed_data.json
    try:
        from seed_migration import run_seed
        from database import db as seed_db
        await run_seed(seed_db)
    except Exception as e:
        print(f"Seed migration warning: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
