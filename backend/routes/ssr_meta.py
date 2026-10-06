"""
Server-Side Meta Injection endpoint.
Returns page-specific title, description, canonical, H1, and OG data
for any given URL path. Used by the frontend server to inject correct
metadata into <head> before sending HTML to browsers/crawlers.

This fixes the core SPA SEO issue: every page getting the same generic
title/description in the initial HTML response.
"""
from fastapi import APIRouter, Query, Depends
from database import db
from auth import get_current_admin
import json
import re
import time

router = APIRouter()

PRODUCTION_URL = "https://brightluxx.com"
SITE_NAME = "Brightluxx"
DEFAULT_DESC = "Premium LED display solutions for architects, contractors, and specifiers in Dubai, UAE & GCC. MicroLED, outdoor, transparent, and creative LED displays."
DEFAULT_OG_IMAGE = "https://files.ihgbrands.com/uploads_hero_banner.webp"

# In-memory cache with TTL (reset on server restart)
_meta_cache = {}
_CACHE_TTL = 600  # 10 minutes

# Human-friendly path-to-title mapping for pages without DB entries
PATH_TITLES = {
    "/": "Premium LED Display Solutions in Dubai, UAE",
    "/products": "LED Display Products — Indoor, Outdoor, Creative & Transparent",
    "/solutions": "LED Display Solutions by Industry",
    "/technology": "LED Display Technology — COB, MiP, MicroLED & More",
    "/contact": "Contact Us — LED Display Enquiries Dubai, UAE",
    "/about": "About Brightluxx — LED Display Manufacturer Since 2005",
    "/blog": "Blog — LED Display Industry Insights & News",
    "/faq": "Frequently Asked Questions — LED Displays",
    "/case-studies": "Case Studies — LED Display Projects Across UAE",
    "/projects": "Project Portfolio — LED Display Installations",
    "/resources": "Resources — Spec Packs, Cheat Sheets & BIM References",
    "/knowledge": "Knowledge Hub — LED Display Technical Guides",
    "/calculator": "LED Screen Size Calculator",
    "/budget-estimator": "LED Display Budget Estimator",
    "/viewing-distance": "Viewing Distance & Pixel Pitch Calculator",
    "/power-estimator": "LED Display Power Consumption Estimator",
    "/project-planner": "LED Project Planner — Timeline & Specifications",
    "/technology-selector": "LED Technology Selector Quiz",
    "/spec-substitution": "LED Spec Substitution Service",
    "/value-engineering": "LED Value Engineering — Cost Optimization",
    "/installation-guide": "LED Display Installation Guide",
    "/cpd-programme": "CPD Programme — LED Technology Training",
    "/for-architects": "LED Displays for Architects — Specification Resources",
    "/for-contractors": "LED Displays for Contractors — Installation Guides",
    "/distribution": "Distribution & Franchise Partnerships",
    "/factory-tour": "Virtual Factory Tour — LED Manufacturing Facility",
    "/compare-brands": "Compare LED Display Brands — Brightluxx vs Competitors",
    "/led-screen-suppliers-dubai": "LED Screen Suppliers in Dubai — Brightluxx",
    "/abu-dhabi": "LED Display Supplier Abu Dhabi — Brightluxx",
    "/saudi-arabia": "LED Display Solutions Saudi Arabia — Brightluxx",
    "/qatar": "LED Screen Solutions Qatar — Brightluxx",
    "/kuwait": "LED Display Solutions Kuwait — Brightluxx",
    "/government-solutions": "Government LED Display Solutions — Brightluxx UAE",
    "/indoor-led": "Indoor LED Displays — Fine Pitch P0.4 to P4",
    "/outdoor-led": "Outdoor LED Displays — Weatherproof P2.5 to P10",
    "/luxury-home-cinema": "Luxury Home Cinema LED Displays",
    "/art-immersive": "Art & Immersive LED Installations — XR, NFT, Sculptural",
    "/signage-solutions": "Digital Signage Solutions — Channel Letters, Menus & More",
    "/product-families": "LED Display Product Families",
    "/lumimorph": "LumiMorph — Fine-Pitch Modular LED Displays",
    "/naturatex": "NaturaTex — Texture Screen Technology",
    "/signatouch": "SignaTouch — Interactive Digital Signage & Kiosks",
    "/glassmorph": "GlassMorph — Smart Glass & Transparent LED",
    "/pixelvue": "PixelVue — Standard & Specialty LED Displays",
    # Technology sub-pages
    "/technology/cob-led": "COB LED Technology — Chip-on-Board Explained",
    "/technology/cob": "COB LED Technology — Chip-on-Board Explained",
    "/technology/microled": "MicroLED & MiP Technology — Next-Gen Pixel Tech",
    "/technology/mip-led": "MiP LED Technology — Mini-in-Package Displays",
    "/technology/gob": "GOB Protection — Glue-on-Board Coating Technology",
    "/technology/hdr": "HDR & Color Technology for LED Displays",
    "/technology/driving-ic": "Driving ICs — PWM & Common Cathode Technology",
    "/technology/fine-pitch-led": "Fine Pitch LED Technology — Sub-P1.0 Displays",
    "/technology/media-facade": "Media Facade LED Technology",
    "/technology/all-in-one-dvled": "All-in-One dvLED Technology",
    "/technology/transparent-led": "Transparent LED Display Technology",
    "/technology/creative-led": "Creative LED Display Technology — Curved & Custom",
    "/technology/3d-anamorphic-led": "3D Anamorphic Naked-Eye LED Technology",
    # Solution sub-pages
    "/solutions/retail": "LED Displays for Retail & Hospitality",
    "/solutions/corporate": "LED Displays for Corporate Offices & Lobbies",
    "/solutions/entertainment": "LED Displays for Entertainment & Events",
    "/solutions/transportation": "LED Displays for Transportation — Airports, Metro",
    "/solutions/worship": "LED Displays for Houses of Worship",
    "/solutions/control-rooms": "LED Video Walls for Control Rooms & Command Centers",
    "/solutions/virtual-production": "LED Walls for Virtual Production & XR Stages",
    "/solutions/architecture": "Architectural LED Displays — Facades & Media Walls",
}

# Path descriptions for pages without DB entries
PATH_DESCS = {
    "/products": "Browse 85+ premium LED display products — MicroLED, outdoor, transparent, interactive, and creative LED solutions for UAE & GCC projects.",
    "/solutions": "Industry-specific LED display solutions for retail, corporate, entertainment, transportation, worship, and control rooms across UAE.",
    "/technology": "Explore LED display technologies including COB, MiP, MicroLED, GOB protection, HDR, and driving IC innovations.",
    "/contact": "Get in touch with Brightluxx for LED display enquiries, site surveys, and project consultations in Dubai, UAE.",
    "/about": "Learn about Brightluxx — a leading LED display manufacturer and supplier in Dubai, UAE, serving the GCC since 2005.",
    "/blog": "Latest news, insights, and technical articles about LED display technology, installations, and industry trends.",
    "/indoor-led": "Premium indoor LED displays from P0.4 to P4 pixel pitch. COB MicroLED, MiP, fine-pitch, and all-in-one solutions for corporate and retail.",
    "/outdoor-led": "Weatherproof outdoor LED displays from P2.5 to P10. High brightness, coastal GOB, mesh facade, and road signal displays.",
}


def _title_from_path(path: str) -> str:
    """Generate a human-friendly title from a URL path when no DB entry exists."""
    if path in PATH_TITLES:
        return PATH_TITLES[path]
    # Dynamic fallback: convert path segments to title case
    segments = [s for s in path.strip("/").split("/") if s]
    if not segments:
        return "Premium LED Display Solutions in Dubai, UAE"
    readable = " — ".join(
        seg.replace("-", " ").replace("_", " ").title() for seg in segments
    )
    return readable


def _desc_from_path(path: str) -> str:
    """Generate a description from path."""
    if path in PATH_DESCS:
        return PATH_DESCS[path]
    title = _title_from_path(path)
    return f"{title}. Premium LED display solutions by Brightluxx in Dubai, UAE."


def clear_ssr_cache():
    """Exported helper so admin routes can purge the cache."""
    _meta_cache.clear()


def _org_schema():
    """Reusable Organization schema snippet."""
    return {
        "@type": "Organization",
        "name": SITE_NAME,
        "url": PRODUCTION_URL,
        "logo": DEFAULT_OG_IMAGE,
    }


def _global_business_schemas():
    """Sitewide Organization + LocalBusiness JSON-LD (footer NAP appears on every page)."""
    address = {"@type": "PostalAddress", "streetAddress": "Jebel Ali Industrial Area 1",
               "addressLocality": "Dubai", "addressCountry": "AE"}
    return [
        json.dumps({
            "@context": "https://schema.org", "@type": "Organization",
            "@id": f"{PRODUCTION_URL}/#organization",
            "name": "Brightluxx", "legalName": "Brightluxx LED Displays",
            "url": PRODUCTION_URL, "logo": f"{PRODUCTION_URL}/android-chrome-512x512.png",
            "telephone": "+971559954274", "address": address,
            "contactPoint": {"@type": "ContactPoint", "telephone": "+971559954274",
                             "contactType": "sales", "areaServed": ["AE", "SA", "QA", "KW", "BH", "OM"],
                             "availableLanguage": ["en", "ar"]},
        }),
        json.dumps({
            "@context": "https://schema.org", "@type": "LocalBusiness",
            "@id": f"{PRODUCTION_URL}/#localbusiness",
            "name": "Brightluxx LED Displays", "image": f"{PRODUCTION_URL}/android-chrome-512x512.png",
            "url": PRODUCTION_URL, "telephone": "+971559954274",
            "priceRange": "AED 2,500 - AED 12,000 per m²", "address": address,
            "geo": {"@type": "GeoCoordinates", "latitude": 24.9857, "longitude": 55.0272},
            "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
                                          "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                          "opens": "09:00", "closes": "18:00"},
            "areaServed": ["Dubai", "Abu Dhabi", "United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Bahrain", "Oman"],
        }),
    ]


def _breadcrumb_schema(items):
    """Build BreadcrumbList schema.  items = [(name, url), ...]"""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url,
            }
            for i, (name, url) in enumerate(items)
        ],
    }


def _article_schema(*, title, description, url, image=None, date_published=None,
                     date_modified=None, section=None):
    """Build an Article schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110] if title else "",
        "description": description or "",
        "url": url,
        "image": image or DEFAULT_OG_IMAGE,
        "author": _org_schema(),
        "publisher": _org_schema(),
    }
    if date_published:
        schema["datePublished"] = str(date_published)[:10]
    if date_modified:
        schema["dateModified"] = str(date_modified)[:10]
    if section:
        schema["articleSection"] = section
    return schema


def _webpage_schema(*, title, description, url):
    """Build a generic WebPage schema."""
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description or "",
        "url": url,
        "publisher": _org_schema(),
    }


async def _build_schemas(path: str, meta: dict) -> list:
    """Build JSON-LD schemas for any page type. Returns list of JSON strings."""
    schemas = []
    title = meta.get("h1") or meta.get("title", "")
    desc = meta.get("description", "")
    url = f"{PRODUCTION_URL}{path}"

    # --- Product pages ---
    if path.startswith("/products/"):
        slug = path.split("/products/")[1].rstrip("/")
        product = await db["products"].find_one({"slug": slug})
        if product:
            product_schema = {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": product.get("name", ""),
                "description": product.get("description", "") or product.get("tagline", ""),
                "sku": product.get("product_code", ""),
                "brand": {"@type": "Brand", "name": product.get("brand", "Brightluxx")},
                "manufacturer": _org_schema(),
                "url": url,
                "category": product.get("category", "LED Display"),
                "image": product.get("image_url", "") or DEFAULT_OG_IMAGE,
            }
            # Offers
            price_range = product.get("price_range")
            if price_range and isinstance(price_range, dict):
                product_schema["offers"] = {
                    "@type": "AggregateOffer",
                    "priceCurrency": price_range.get("currency", "USD"),
                    "lowPrice": price_range.get("low", 0),
                    "highPrice": price_range.get("high", 0),
                    "offerCount": 1,
                    "availability": f"https://schema.org/{product.get('availability', 'InStock')}",
                    "seller": _org_schema(),
                    "url": url,
                }
            # Properties
            props = []
            for field, label in [("pixel_pitch", "Pixel Pitch"), ("brightness", "Brightness"),
                                 ("resolution", "Resolution"), ("warranty", "Warranty")]:
                if product.get(field):
                    props.append({"@type": "PropertyValue", "name": label, "value": product[field]})
            key_specs = product.get("key_specs", {})
            if isinstance(key_specs, dict):
                for k, v in key_specs.items():
                    if k not in ("pixel_pitch", "brightness", "resolution"):
                        props.append({"@type": "PropertyValue", "name": k.replace("_", " ").title(), "value": str(v)})
            if props:
                product_schema["additionalProperty"] = props
            # AggregateRating from reviews
            review_stats = await db["reviews"].aggregate([
                {"$match": {"product_slug": slug, "status": "approved"}},
                {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
            ]).to_list(1)
            if review_stats and review_stats[0]["count"] > 0:
                product_schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": round(review_stats[0]["avg"], 1),
                    "reviewCount": review_stats[0]["count"],
                    "bestRating": 5,
                    "worstRating": 1,
                }
            schemas.append(json.dumps(product_schema))
            # FAQ
            if product.get("faq"):
                schemas.append(json.dumps({
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [
                        {"@type": "Question", "name": item["q"],
                         "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                        for item in product["faq"]
                    ]
                }))
            # Breadcrumb
            schemas.append(json.dumps(_breadcrumb_schema([
                ("Home", PRODUCTION_URL),
                ("Products", f"{PRODUCTION_URL}/products"),
                (product.get("name", slug), url),
            ])))

    # --- Blog pages ---
    elif path.startswith("/blog/") and path != "/blog":
        blog_slug = path.split("/blog/")[1].rstrip("/")
        blog = await db["blogs"].find_one({"slug": blog_slug})
        if blog:
            schemas.append(json.dumps(_article_schema(
                title=blog.get("title", title),
                description=blog.get("excerpt", desc),
                url=url,
                image=blog.get("cover_image") or blog.get("image_url"),
                date_published=blog.get("created_at"),
                date_modified=blog.get("updated_at"),
                section="LED Display Technology",
            )))
            if blog.get("faq"):
                schemas.append(json.dumps({
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [
                        {"@type": "Question", "name": item["q"],
                         "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                        for item in blog["faq"]
                    ]
                }))
            schemas.append(json.dumps(_breadcrumb_schema([
                ("Home", PRODUCTION_URL),
                ("Blog", f"{PRODUCTION_URL}/blog"),
                (blog.get("title", blog_slug), url),
            ])))

    # --- Case study pages ---
    elif path.startswith("/case-studies/") and path != "/case-studies":
        cs_slug = path.split("/case-studies/")[1].rstrip("/")
        cs = await db["case_studies"].find_one({"slug": cs_slug})
        if cs:
            schemas.append(json.dumps(_article_schema(
                title=cs.get("title", title),
                description=cs.get("challenge", desc),
                url=url,
                image=cs.get("hero_image") or cs.get("thumbnail"),
                date_published=cs.get("created_at"),
                date_modified=cs.get("updated_at"),
                section="Case Study",
            )))
            schemas.append(json.dumps(_breadcrumb_schema([
                ("Home", PRODUCTION_URL),
                ("Case Studies", f"{PRODUCTION_URL}/case-studies"),
                (cs.get("title", cs_slug), url),
            ])))

    # --- Application pages ---
    elif path.startswith("/applications/") and path != "/applications":
        schemas.append(json.dumps(_webpage_schema(title=title, description=desc, url=url)))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("Applications", f"{PRODUCTION_URL}/applications"),
            (title, url),
        ])))

    # --- Digital experience pages ---
    elif path.startswith("/digital-experience"):
        schemas.append(json.dumps(_webpage_schema(title=title, description=desc, url=url)))
        crumbs = [("Home", PRODUCTION_URL)]
        if "/" in path.lstrip("/").split("/", 1)[-1]:
            crumbs.append(("Digital Experience", f"{PRODUCTION_URL}/digital-experience-architecture"))
        crumbs.append((title, url))
        schemas.append(json.dumps(_breadcrumb_schema(crumbs)))

    # --- Contractor pages ---
    elif path.startswith("/contractors/"):
        schemas.append(json.dumps(_article_schema(
            title=title, description=desc, url=url, section="Contractor Resources",
        )))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("For Contractors", f"{PRODUCTION_URL}/for-contractors"),
            (title, url),
        ])))

    # --- Latest tech pages ---
    elif path.startswith("/latest-tech/"):
        schemas.append(json.dumps(_article_schema(
            title=title, description=desc, url=url, section="Latest Technology",
        )))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("Latest Tech", f"{PRODUCTION_URL}/latest-tech"),
            (title, url),
        ])))

    # --- Knowledge hub articles ---
    elif path.startswith("/knowledge/") and path != "/knowledge":
        schemas.append(json.dumps(_article_schema(
            title=title, description=desc, url=url, section="Knowledge Hub",
        )))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("Knowledge Hub", f"{PRODUCTION_URL}/knowledge"),
            (title, url),
        ])))

    # --- Technology sub-pages ---
    elif path.startswith("/technology/") and path != "/technology":
        schemas.append(json.dumps(_article_schema(
            title=title, description=desc, url=url, section="LED Technology",
        )))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("Technology", f"{PRODUCTION_URL}/technology"),
            (title, url),
        ])))

    # --- Solutions sub-pages ---
    elif path.startswith("/solutions/") and path != "/solutions":
        sol = await db["solutions"].find_one({"slug": path.split("/")[-1]})
        schemas.append(json.dumps({
            "@context": "https://schema.org", "@type": "Service",
            "name": (sol or {}).get("title") or title,
            "description": (sol or {}).get("description") or desc,
            "url": url, "provider": _org_schema(),
            "areaServed": ["United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Bahrain", "Oman"],
        }))
        if sol and isinstance(sol.get("faqs"), list) and sol["faqs"]:
            schemas.append(json.dumps({
                "@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": f.get("q", ""),
                                "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}}
                               for f in sol["faqs"]],
            }))
        schemas.append(json.dumps(_breadcrumb_schema([
            ("Home", PRODUCTION_URL),
            ("Solutions", f"{PRODUCTION_URL}/solutions"),
            (title, url),
        ])))

    # --- Fallback: any other page gets a WebPage schema + BreadcrumbList ---
    else:
        schemas.append(json.dumps(_webpage_schema(title=title, description=desc, url=url)))
        if path != "/":
            crumbs = [("Home", PRODUCTION_URL), (title, url)]
            schemas.append(json.dumps(_breadcrumb_schema(crumbs)))

    schemas.extend(_global_business_schemas())
    return schemas


@router.get("/api/ssr/meta")
async def get_ssr_meta(path: str = Query(...)):
    """Return page-specific meta for server-side injection into HTML <head>."""
    # Normalize path
    path = path.rstrip("/") or "/"

    # Check cache with TTL
    cached = _meta_cache.get(path)
    if cached and (time.time() - cached["_ts"]) < _CACHE_TTL:
        return cached["data"]

    # Try SEO database first
    seo_col = db["page_seo"]
    seo_entry = await seo_col.find_one({"path": path})

    if seo_entry and (seo_entry.get("meta_title") or seo_entry.get("meta_description")):
        raw_title = seo_entry.get("meta_title", "") or _title_from_path(path)
        title_with_suffix = raw_title if "brightluxx" in raw_title.lower() else f"{raw_title} | {SITE_NAME}"
        raw_og_title = seo_entry.get("og_title", "") or seo_entry.get("meta_title", "")
        og_with_suffix = raw_og_title if "brightluxx" in raw_og_title.lower() else f"{raw_og_title} | {SITE_NAME}"
        result = {
            "title": title_with_suffix,
            "description": seo_entry.get("meta_description", "") or _desc_from_path(path),
            "canonical": seo_entry.get("canonical_url", "") or f"{PRODUCTION_URL}{path}",
            "h1": raw_title,
            "keywords": ", ".join(seo_entry.get("keywords", [])) if seo_entry.get("keywords") else "",
            "og_title": og_with_suffix,
            "og_description": seo_entry.get("og_description", "") or seo_entry.get("meta_description", "") or _desc_from_path(path),
            "og_image": seo_entry.get("og_image", "") or DEFAULT_OG_IMAGE,
            "og_image_alt": seo_entry.get("image_alt", "") or raw_title,
            "noindex": seo_entry.get("noindex", False),
        }
    else:
        # Fallback: generate from path
        title = _title_from_path(path)
        desc = _desc_from_path(path)
        title_with_suffix = title if "brightluxx" in title.lower() else f"{title} | {SITE_NAME}"
        result = {
            "title": title_with_suffix,
            "description": desc,
            "canonical": f"{PRODUCTION_URL}{path}",
            "h1": title,
            "keywords": "",
            "og_title": title_with_suffix,
            "og_description": desc,
            "og_image": DEFAULT_OG_IMAGE,
            "og_image_alt": title,
            "noindex": False,
        }

    # CRITICAL: canonical must ALWAYS be self-referencing unless explicitly overridden
    # Never fall back to homepage
    if not result["canonical"] or (result["canonical"] == f"{PRODUCTION_URL}/" and path != "/"):
        result["canonical"] = f"{PRODUCTION_URL}{path}"

    # --- Schema injection by page type ---
    schemas = await _build_schemas(path, result)
    if schemas:
        result["schemas"] = schemas

    # Cache result with timestamp (cap at 500 entries)
    if len(_meta_cache) > 500:
        _meta_cache.clear()
    _meta_cache[path] = {"data": result, "_ts": time.time()}
    return result


@router.post("/api/ssr/meta/clear-cache")
async def clear_ssr_cache_endpoint(admin=Depends(get_current_admin)):
    """Clear the SSR meta cache (admin only)."""
    _meta_cache.clear()
    return {"cleared": True}
