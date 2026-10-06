"""Dynamic sitemap.xml generation — fully DB-driven.
Combines SEO pages, products, blogs, case studies, and static routes
with real lastmod dates and deduplication.
Filters out redirected/noindex URLs."""
from fastapi import APIRouter
from fastapi.responses import Response
from datetime import datetime, timezone
from database import db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_URL = "https://brightluxx.com"

# Paths that 301-redirect (WP legacy + prerender-server.js) — must NOT appear in sitemap
REDIRECT_PATHS = {
    "/our-works/", "/our-works", "/digital-solutions/", "/digital-solutions",
    "/products/led-display", "/products/led-display/",
    "/products/indoor-led-display", "/products/indoor-led-display/",
    "/products/outdoor-led-display", "/products/outdoor-led-display/",
    "/products/spherical-led-display", "/products/spherical-led-display/",
    "/products/cube-led-display-p3", "/products/cube-led-display-p3/",
    "/products/transparent-led-display", "/products/transparent-led-display/",
    "/products/rental-led-display", "/products/flexible-led-display",
    "/download-catalog/", "/download-catalog",
    "/about-us/", "/about-us", "/contact-us/", "/contact-us",
    "/services/", "/services", "/portfolio/", "/portfolio",
    "/gallery/", "/gallery",
    # prerender-server.js WP_REDIRECTS
    "/led-screen-dubai", "/led-display-abu-dhabi",
    "/led-screen-saudi-arabia", "/led-screen-qatar", "/led-screen-kuwait",
    "/resource-library", "/digital-experience",
}

# Static routes with priority and change frequency (fallback for pages not in DB)
STATIC_ROUTES = {
    "/": (1.0, "daily"),
    "/products": (0.9, "daily"),
    "/solutions": (0.9, "weekly"),
    "/contact": (0.9, "monthly"),
    "/about": (0.8, "monthly"),
    "/blog": (0.8, "daily"),
    "/faq": (0.7, "monthly"),
    "/case-studies": (0.9, "weekly"),
    "/projects": (0.8, "weekly"),
    "/resources": (0.8, "weekly"),
    "/knowledge": (0.9, "weekly"),
    "/product-families": (0.9, "weekly"),
    # Product families
    "/pixelvue": (0.9, "weekly"),
    "/lumimorph": (0.9, "weekly"),
    "/naturatex": (0.9, "weekly"),
    "/signatouch": (0.9, "weekly"),
    "/glassmorph": (0.9, "weekly"),
    # Product family sub-pages
    "/lumimorph/elite": (0.8, "monthly"),
    "/lumimorph/grande": (0.8, "monthly"),
    "/lumimorph/mini": (0.8, "monthly"),
    "/naturatex/holoveil": (0.8, "monthly"),
    "/signatouch/touch-kiosk": (0.8, "monthly"),
    "/signatouch/smart-signage": (0.8, "monthly"),
    "/signatouch/self-service": (0.8, "monthly"),
    "/glassmorph/smart-film": (0.8, "monthly"),
    "/glassmorph/led-film": (0.8, "monthly"),
    "/glassmorph/media-glass": (0.8, "monthly"),
    "/glassmorph/flying-display": (0.8, "monthly"),
    "/glassmorph/switchable-glass": (0.8, "monthly"),
    "/glassmorph/hanging-led": (0.8, "monthly"),
    # Technology pages
    "/technology": (0.8, "weekly"),
    "/technology/cob-led": (0.7, "monthly"),
    "/technology/cob": (0.7, "monthly"),
    "/technology/microled": (0.7, "monthly"),
    "/technology/mip-led": (0.7, "monthly"),
    "/technology/gob": (0.7, "monthly"),
    "/technology/hdr": (0.7, "monthly"),
    "/technology/driving-ic": (0.7, "monthly"),
    "/technology/fine-pitch-led": (0.7, "monthly"),
    "/technology/all-in-one-dvled": (0.7, "monthly"),
    "/technology/transparent-led": (0.7, "monthly"),
    "/technology/creative-led": (0.7, "monthly"),
    "/technology/3d-anamorphic-led": (0.7, "monthly"),
    "/technology/media-facade": (0.7, "monthly"),
    # Solutions
    "/solutions/retail": (0.8, "monthly"),
    "/solutions/corporate": (0.8, "monthly"),
    "/solutions/entertainment": (0.8, "monthly"),
    "/solutions/transportation": (0.8, "monthly"),
    "/solutions/worship": (0.8, "monthly"),
    "/solutions/control-rooms": (0.8, "monthly"),
    "/solutions/virtual-production": (0.8, "monthly"),
    "/solutions/architecture": (0.8, "monthly"),
    # SEO landing pages
    "/led-screen-suppliers-dubai": (0.95, "weekly"),
    "/government-solutions": (0.9, "weekly"),
    "/abu-dhabi": (0.9, "weekly"),
    "/saudi-arabia": (0.9, "weekly"),
    "/qatar": (0.85, "monthly"),
    "/kuwait": (0.85, "monthly"),
    "/compare-brands": (0.85, "weekly"),
    "/indoor-led": (0.85, "weekly"),
    "/outdoor-led": (0.85, "weekly"),
    "/luxury-home-cinema": (0.8, "weekly"),
    "/art-immersive": (0.8, "weekly"),
    "/signage-solutions": (0.8, "weekly"),
    # Tools
    "/calculator": (0.7, "monthly"),
    "/budget-estimator": (0.8, "monthly"),
    "/viewing-distance": (0.7, "monthly"),
    "/power-estimator": (0.7, "monthly"),
    "/project-planner": (0.8, "monthly"),
    "/technology-selector": (0.8, "monthly"),
    "/tools/roi-calculator": (0.75, "monthly"),
    # Architect / Contractor
    "/for-architects": (0.8, "monthly"),
    "/for-contractors": (0.7, "monthly"),
    "/cpd-programme": (0.7, "monthly"),
    "/spec-substitution": (0.7, "monthly"),
    "/value-engineering": (0.7, "monthly"),
    "/installation-guide": (0.6, "monthly"),
    "/design-assist": (0.7, "monthly"),
    # Other
    "/factory-tour": (0.5, "monthly"),
    "/distribution": (0.5, "monthly"),
    "/compare-products": (0.5, "monthly"),
    "/lp/specifier-toolkit": (0.6, "monthly"),
    # Knowledge hub articles
    "/knowledge/cob-vs-mip-vs-smd": (0.8, "monthly"),
    "/knowledge/pixel-pitch-guide": (0.8, "monthly"),
    "/knowledge/brightness-nits-guide": (0.8, "monthly"),
    "/knowledge/ip-rating-guide": (0.8, "monthly"),
    "/knowledge/refresh-rate-guide": (0.8, "monthly"),
    "/knowledge/processing-calibration": (0.8, "monthly"),
    "/knowledge/cms-multi-site": (0.8, "monthly"),
    # Application pages
    "/applications": (0.8, "weekly"),
    "/applications/retail": (0.7, "monthly"),
    "/applications/hospitality": (0.7, "monthly"),
    "/applications/corporate": (0.7, "monthly"),
    "/applications/healthcare": (0.7, "monthly"),
    "/applications/education": (0.7, "monthly"),
    "/applications/outdoor": (0.7, "monthly"),
    "/applications/transport": (0.7, "monthly"),
    "/applications/worship": (0.7, "monthly"),
    # Digital experience
    "/digital-experience-architecture": (0.7, "monthly"),
    "/digital-experience/media-facades": (0.6, "monthly"),
    "/digital-experience/immersive-led-rooms": (0.6, "monthly"),
    "/digital-experience/retail-experiential-screens": (0.6, "monthly"),
    # Contractor pages
    "/contractors/dvled-vs-lcd": (0.6, "monthly"),
    "/contractors/led-cost-per-sqm": (0.6, "monthly"),
    "/contractors/led-installation-guide": (0.6, "monthly"),
    # Latest tech
    "/latest-tech": (0.7, "weekly"),
    "/latest-tech/glasses-free-3d": (0.6, "monthly"),
    "/latest-tech/microled": (0.6, "monthly"),
    "/latest-tech/transparent-led": (0.6, "monthly"),
    "/latest-tech/ai-powered": (0.6, "monthly"),
    # Misc
    "/tech-guide": (0.6, "monthly"),
    "/sla-guide": (0.6, "monthly"),
    "/supplier-registration": (0.5, "monthly"),
    "/technical-support": (0.5, "monthly"),
    "/inspirations": (0.7, "weekly"),
    # Arabic landing pages — static, prerendered, canonical Arabic content
    "/ar-ae/": (0.9, "monthly"),
    "/ar-ae/dubai": (0.85, "monthly"),
    "/ar-ae/uae": (0.85, "monthly"),
}


def _format_date(dt) -> str:
    """Format a datetime or ISO string to YYYY-MM-DD for sitemap."""
    if not dt:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if isinstance(dt, str):
        try:
            return dt[:10]
        except Exception:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@router.get("/api/sitemap.xml")
async def sitemap():
    """Generate comprehensive, DB-driven sitemap with real lastmod dates."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seen = set()
    entries = []

    def add(path, priority, freq, lastmod=None):
        if path in seen or path in REDIRECT_PATHS:
            return
        seen.add(path)
        entries.append(
            f"  <url>\n"
            f"    <loc>{BASE_URL}{path}</loc>\n"
            f"    <lastmod>{lastmod or today}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    # 1. SEO DB pages (205 entries with real update dates)
    try:
        async for page in db["page_seo"].find(
            {"noindex": {"$ne": True}},
            {"path": 1, "updated_at": 1}
        ):
            path = page.get("path", "")
            if not path:
                continue
            pr, fr = STATIC_ROUTES.get(path, (0.6, "monthly"))
            add(path, pr, fr, _format_date(page.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: page_seo query failed: {e}")

    # 2. Static routes not yet covered by SEO DB
    for path, (pr, fr) in STATIC_ROUTES.items():
        add(path, pr, fr, today)

    # 3. Dynamic product pages
    try:
        async for p in db["products"].find({}, {"slug": 1, "updated_at": 1, "schema_updated": 1}):
            slug = p.get("slug", "")
            if slug:
                lm = _format_date(p.get("schema_updated") or p.get("updated_at"))
                add(f"/products/{slug}", 0.7, "weekly", lm)
    except Exception as e:
        logger.error(f"Sitemap: products query failed: {e}")

    # 4. PixelVue products (no status field — include all)
    try:
        async for p in db["pixelvue_products"].find({}, {"slug": 1, "updated_at": 1}):
            if p.get("slug"):
                add(f"/pixelvue/{p['slug']}", 0.7, "weekly", _format_date(p.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: pixelvue_products query failed: {e}")

    # 5. Blog posts
    try:
        async for b in db["blogs"].find({}, {"slug": 1, "updated_at": 1, "created_at": 1}):
            if b.get("slug"):
                add(f"/blog/{b['slug']}", 0.6, "weekly", _format_date(b.get("updated_at") or b.get("created_at")))
    except Exception as e:
        logger.error(f"Sitemap: blogs query failed: {e}")

    # 6. Case studies (no status field — all records are published)
    try:
        async for cs in db["case_studies"].find({}, {"slug": 1, "updated_at": 1}):
            if cs.get("slug"):
                add(f"/case-studies/{cs['slug']}", 0.6, "monthly", _format_date(cs.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: case_studies query failed: {e}")

    # 7. Solutions content
    try:
        async for s in db["solutions_content"].find({}, {"slug": 1, "updated_at": 1}):
            if s.get("slug"):
                add(f"/solutions/{s['slug']}", 0.7, "weekly", _format_date(s.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: solutions_content query failed: {e}")

    # 8. Application pages (no status field — include all)
    try:
        async for a in db["applications_content"].find({}, {"slug": 1, "updated_at": 1}):
            if a.get("slug"):
                add(f"/applications/{a['slug']}", 0.7, "monthly", _format_date(a.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: applications_content query failed: {e}")

    # 9. Technology pages (no status field — include all)
    try:
        async for t in db["technologies_content"].find({}, {"slug": 1, "updated_at": 1}):
            if t.get("slug"):
                add(f"/technology/{t['slug']}", 0.7, "monthly", _format_date(t.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: technologies_content query failed: {e}")

    # 10. Inspiration/project pages (no status field — include all)
    try:
        async for i in db["inspirations"].find({}, {"slug": 1, "updated_at": 1}):
            if i.get("slug"):
                add(f"/inspirations/{i['slug']}", 0.5, "monthly", _format_date(i.get("updated_at")))
    except Exception as e:
        logger.error(f"Sitemap: inspirations query failed: {e}")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries) + "\n"
        '</urlset>'
    )

    return Response(content=xml, media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@router.get("/api/image-sitemap.xml")
async def image_sitemap():
    """Image sitemap for Google Image Search indexing.
    Lists all product, blog, and case study images with metadata."""
    entries = []

    def img_entry(page_url, image_url, title="", caption=""):
        esc_title = title.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
        esc_caption = caption.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")[:200]
        parts = [
            "  <url>",
            f"    <loc>{BASE_URL}{page_url}</loc>",
            "    <image:image>",
            f"      <image:loc>{image_url}</image:loc>",
        ]
        if esc_title:
            parts.append(f"      <image:title>{esc_title}</image:title>")
        if esc_caption:
            parts.append(f"      <image:caption>{esc_caption}</image:caption>")
        parts.append("    </image:image>")
        parts.append("  </url>")
        return "\n".join(parts)

    # Products
    try:
        async for p in db["products"].find(
            {"image_url": {"$exists": True, "$ne": ""}},
            {"slug": 1, "name": 1, "image_url": 1, "tagline": 1, "category": 1}
        ):
            if p.get("slug") and p.get("image_url"):
                title = f"{p.get('name', '')} - Brightluxx LED Display"
                caption = p.get("tagline", "") or f"{p.get('name', '')} {p.get('category', '')} LED display"
                entries.append(img_entry(
                    f"/products/{p['slug']}",
                    p["image_url"],
                    title,
                    caption,
                ))
    except Exception as e:
        logger.error(f"Image sitemap products: {e}")

    # Case studies
    try:
        async for cs in db["case_studies"].find(
            {"images": {"$exists": True}},
            {"slug": 1, "title": 1, "images": 1, "location": 1}
        ):
            if cs.get("slug"):
                for img in (cs.get("images") or [])[:5]:
                    url = img if isinstance(img, str) else img.get("url", "")
                    if url:
                        entries.append(img_entry(
                            f"/case-studies/{cs['slug']}",
                            url,
                            f"{cs.get('title', '')} - LED Project",
                            cs.get("location", ""),
                        ))
    except Exception as e:
        logger.error(f"Image sitemap case studies: {e}")

    # Blogs
    try:
        async for b in db["blogs"].find(
            {"image_url": {"$exists": True, "$ne": ""}},
            {"slug": 1, "title": 1, "image_url": 1}
        ):
            if b.get("slug") and b.get("image_url"):
                entries.append(img_entry(
                    f"/blog/{b['slug']}",
                    b["image_url"],
                    b.get("title", ""),
                ))
    except Exception as e:
        logger.error(f"Image sitemap blogs: {e}")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "\n".join(entries) + "\n"
        "</urlset>"
    )

    return Response(content=xml, media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"})
