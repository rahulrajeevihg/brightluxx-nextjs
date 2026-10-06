"""
Internal Linking API — Returns semantically rich internal link graph
for crawler pre-rendering. Defines parent/child, sibling, and cross-category
relationships to help search engines understand the site hierarchy.
"""
from fastapi import APIRouter
from database import db

router = APIRouter(tags=["Internal Links"])
seo_col = db["page_seo"]

# ── Site hierarchy and relationship map ─────────────────────────────
# Each page defines: parent, children, siblings, related, hub links

PRODUCT_FAMILIES = {
    "/lumimorph": {
        "name": "LumiMorph",
        "children": ["/lumimorph/elite", "/lumimorph/grande", "/lumimorph/mini"],
        "related_knowledge": ["/knowledge/cob-vs-mip-vs-smd", "/knowledge/pixel-pitch-guide"],
        "related_solutions": ["/art-immersive", "/luxury-home-cinema"],
        "use_cases": ["Luxury Residences", "Art Galleries", "Corporate Lobbies"],
    },
    "/naturatex": {
        "name": "NaturaTex",
        "children": ["/naturatex/holoveil"],
        "related_knowledge": ["/knowledge/cob-vs-mip-vs-smd", "/knowledge/brightness-nits-guide"],
        "related_solutions": ["/art-immersive", "/design-assist"],
        "use_cases": ["Architectural Interiors", "Retail Displays", "Museum Exhibits"],
    },
    "/signatouch": {
        "name": "SignaTouch",
        "children": ["/signatouch/touch-kiosk", "/signatouch/smart-signage", "/signatouch/self-service"],
        "related_knowledge": ["/knowledge/cms-multi-site", "/knowledge/refresh-rate-guide"],
        "related_solutions": ["/signage-solutions", "/digital-experience-architecture"],
        "use_cases": ["Retail Kiosks", "Wayfinding", "Self-Service Terminals"],
    },
    "/glassmorph": {
        "name": "GlassMorph",
        "children": ["/glassmorph/smart-film", "/glassmorph/led-film", "/glassmorph/media-glass", "/glassmorph/flying-display"],
        "related_knowledge": ["/knowledge/ip-rating-guide", "/knowledge/brightness-nits-guide"],
        "related_solutions": ["/for-architects", "/design-assist"],
        "use_cases": ["Smart Windows", "Transparent Displays", "Architectural Glass"],
    },
    "/pixelvue": {
        "name": "PixelVue",
        "children": [],
        "related_knowledge": ["/knowledge/pixel-pitch-guide", "/knowledge/refresh-rate-guide", "/knowledge/brightness-nits-guide"],
        "related_solutions": ["/indoor-led", "/outdoor-led", "/signage-solutions"],
        "use_cases": ["Digital Signage", "Video Walls", "Outdoor Advertising"],
    },
}

# Reverse map: child → parent family
CHILD_TO_PARENT = {}
for family_path, fam in PRODUCT_FAMILIES.items():
    for child in fam["children"]:
        CHILD_TO_PARENT[child] = family_path

ALL_FAMILIES = list(PRODUCT_FAMILIES.keys())

# Knowledge articles and their related product families
KNOWLEDGE_LINKS = {
    "/knowledge/cob-vs-mip-vs-smd": {
        "related_families": ["/lumimorph", "/naturatex", "/pixelvue"],
        "sibling_articles": ["/knowledge/pixel-pitch-guide", "/knowledge/brightness-nits-guide"],
    },
    "/knowledge/pixel-pitch-guide": {
        "related_families": ["/pixelvue", "/lumimorph"],
        "sibling_articles": ["/knowledge/brightness-nits-guide", "/knowledge/refresh-rate-guide"],
    },
    "/knowledge/brightness-nits-guide": {
        "related_families": ["/pixelvue", "/naturatex", "/glassmorph"],
        "sibling_articles": ["/knowledge/pixel-pitch-guide", "/knowledge/ip-rating-guide"],
    },
    "/knowledge/ip-rating-guide": {
        "related_families": ["/pixelvue", "/glassmorph"],
        "sibling_articles": ["/knowledge/brightness-nits-guide", "/knowledge/refresh-rate-guide"],
    },
    "/knowledge/refresh-rate-guide": {
        "related_families": ["/pixelvue", "/signatouch"],
        "sibling_articles": ["/knowledge/pixel-pitch-guide", "/knowledge/processing-calibration"],
    },
    "/knowledge/processing-calibration": {
        "related_families": ["/pixelvue", "/lumimorph"],
        "sibling_articles": ["/knowledge/refresh-rate-guide", "/knowledge/cms-multi-site"],
    },
    "/knowledge/cms-multi-site": {
        "related_families": ["/signatouch", "/pixelvue"],
        "sibling_articles": ["/knowledge/processing-calibration", "/knowledge/cob-vs-mip-vs-smd"],
    },
}

ALL_KNOWLEDGE = list(KNOWLEDGE_LINKS.keys())

# SEO landing pages → product families they should link to
SEO_LANDING_LINKS = {
    "/indoor-led": {
        "families": ["/lumimorph", "/naturatex", "/signatouch", "/pixelvue"],
        "sibling_landings": ["/outdoor-led", "/led-screen-suppliers-dubai"],
    },
    "/outdoor-led": {
        "families": ["/pixelvue", "/glassmorph"],
        "sibling_landings": ["/indoor-led", "/led-screen-suppliers-dubai"],
    },
    "/led-screen-suppliers-dubai": {
        "families": ALL_FAMILIES,
        "sibling_landings": ["/abu-dhabi", "/saudi-arabia", "/qatar", "/kuwait"],
    },
    "/abu-dhabi": {
        "families": ALL_FAMILIES,
        "sibling_landings": ["/led-screen-suppliers-dubai", "/saudi-arabia"],
    },
    "/saudi-arabia": {
        "families": ALL_FAMILIES,
        "sibling_landings": ["/led-screen-suppliers-dubai", "/qatar", "/kuwait"],
    },
    "/qatar": {
        "families": ALL_FAMILIES,
        "sibling_landings": ["/led-screen-suppliers-dubai", "/saudi-arabia", "/kuwait"],
    },
    "/kuwait": {
        "families": ALL_FAMILIES,
        "sibling_landings": ["/led-screen-suppliers-dubai", "/qatar", "/saudi-arabia"],
    },
}


# ── Page name cache (loaded on first request) ──────────────────────
_name_cache = {}


async def _get_name(path: str) -> str:
    """Get the display name for a path."""
    if not _name_cache:
        docs = await seo_col.find({}, {"_id": 0, "path": 1, "name": 1}).to_list(200)
        for d in docs:
            _name_cache[d["path"]] = d.get("name", d["path"].strip("/").replace("-", " ").title())
    return _name_cache.get(path, path.strip("/").replace("-", " ").title())


def _link(path: str, name: str, rel: str) -> dict:
    """Build a link entry."""
    return {"path": path, "name": name, "rel": rel}


async def build_links_for_page(path: str) -> list:
    """Build the internal link graph for a specific page."""
    links = []

    # ── Hub links (every page gets these) ──
    hub_links = [
        ("/", "Home", "home"),
        ("/products", "All Products", "hub"),
        ("/product-families", "Product Families", "hub"),
        ("/solutions", "Solutions", "hub"),
        ("/contact", "Contact Us", "action"),
    ]
    for hp, hn, hr in hub_links:
        if hp != path:
            links.append(_link(hp, hn, hr))

    # ── Product Family landing pages ──
    if path in PRODUCT_FAMILIES:
        fam = PRODUCT_FAMILIES[path]
        # Children (vertical down)
        for child in fam["children"]:
            name = await _get_name(child)
            links.append(_link(child, name, "child"))
        # Sibling families (horizontal)
        for sib in ALL_FAMILIES:
            if sib != path:
                name = await _get_name(sib)
                links.append(_link(sib, name, "sibling-family"))
        # Related knowledge
        for k in fam["related_knowledge"]:
            name = await _get_name(k)
            links.append(_link(k, name, "related-guide"))
        # Related solutions/pages
        for s in fam["related_solutions"]:
            name = await _get_name(s)
            links.append(_link(s, name, "related-solution"))
        # Content hubs
        links.append(_link("/knowledge", "Knowledge Hub", "resource"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/projects", "Projects", "social-proof"))

    # ── Product sub-pages (children of a family) ──
    elif path in CHILD_TO_PARENT:
        parent = CHILD_TO_PARENT[path]
        parent_name = await _get_name(parent)
        links.append(_link(parent, parent_name, "parent"))
        # Siblings
        fam = PRODUCT_FAMILIES[parent]
        for sib in fam["children"]:
            if sib != path:
                name = await _get_name(sib)
                links.append(_link(sib, name, "sibling"))
        # Related knowledge from parent
        for k in fam["related_knowledge"]:
            name = await _get_name(k)
            links.append(_link(k, name, "related-guide"))
        # Other families
        for f in ALL_FAMILIES:
            if f != parent:
                name = await _get_name(f)
                links.append(_link(f, name, "related-family"))
        links.append(_link("/budget-estimator", "Budget Estimator", "tool"))

    # ── Knowledge articles ──
    elif path in KNOWLEDGE_LINKS:
        kl = KNOWLEDGE_LINKS[path]
        links.append(_link("/knowledge", "Knowledge Hub", "parent"))
        for fam in kl["related_families"]:
            name = await _get_name(fam)
            links.append(_link(fam, name, "related-product"))
        for sib in kl["sibling_articles"]:
            name = await _get_name(sib)
            links.append(_link(sib, name, "sibling-article"))
        links.append(_link("/for-architects", "For Architects", "audience"))
        links.append(_link("/tech-guide", "Tech Guide", "resource"))

    # ── Knowledge hub ──
    elif path == "/knowledge":
        for k in ALL_KNOWLEDGE:
            name = await _get_name(k)
            links.append(_link(k, name, "child-article"))
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "related-product"))
        links.append(_link("/for-architects", "For Architects", "audience"))
        links.append(_link("/tech-guide", "Tech Guide", "resource"))

    # ── SEO landing pages ──
    elif path in SEO_LANDING_LINKS:
        sl = SEO_LANDING_LINKS[path]
        for fam in sl["families"]:
            name = await _get_name(fam)
            links.append(_link(fam, name, "related-product"))
        for sib in sl["sibling_landings"]:
            name = await _get_name(sib)
            links.append(_link(sib, name, "sibling-location"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/factory-tour", "Factory Tour", "trust"))
        links.append(_link("/about", "About Brightluxx", "trust"))

    # ── Homepage ──
    elif path == "/":
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "product-family"))
        links.append(_link("/art-immersive", "Art & Immersive", "lifestyle"))
        links.append(_link("/luxury-home-cinema", "Luxury Home Cinema", "lifestyle"))
        links.append(_link("/knowledge", "Knowledge Hub", "resource"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/projects", "Projects", "social-proof"))
        links.append(_link("/blog", "Blog", "content"))
        links.append(_link("/about", "About Brightluxx", "trust"))
        links.append(_link("/factory-tour", "Factory Tour", "trust"))
        links.append(_link("/for-architects", "For Architects", "audience"))
        links.append(_link("/budget-estimator", "Budget Estimator", "tool"))
        for sl in SEO_LANDING_LINKS:
            name = await _get_name(sl)
            links.append(_link(sl, name, "geo-landing"))

    # ── Lifestyle pages ──
    elif path in ["/art-immersive", "/luxury-home-cinema"]:
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "related-product"))
        other = "/luxury-home-cinema" if path == "/art-immersive" else "/art-immersive"
        name = await _get_name(other)
        links.append(_link(other, name, "sibling"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/projects", "Projects", "social-proof"))
        links.append(_link("/inspirations", "Inspirations", "content"))
        links.append(_link("/design-assist", "Design Assist", "service"))

    # ── Solutions page ──
    elif path == "/solutions":
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "product-family"))
        links.append(_link("/applications", "Applications", "related"))
        links.append(_link("/signage-solutions", "Signage Solutions", "related"))
        links.append(_link("/digital-experience-architecture", "Digital Experience", "related"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/for-architects", "For Architects", "audience"))

    # ── About page ──
    elif path == "/about":
        links.append(_link("/factory-tour", "Factory Tour", "related"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        links.append(_link("/projects", "Projects", "social-proof"))
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "product-family"))
        links.append(_link("/cpd-programme", "CPD Programme", "service"))

    # ── Contact page ──
    elif path == "/contact":
        links.append(_link("/about", "About Brightluxx", "trust"))
        links.append(_link("/factory-tour", "Factory Tour", "trust"))
        links.append(_link("/design-assist", "Design Assist", "service"))
        links.append(_link("/budget-estimator", "Budget Estimator", "tool"))
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "product-family"))

    # ── Tool/service pages ──
    elif path in ["/budget-estimator", "/design-assist", "/cpd-programme", "/tech-guide", "/for-architects"]:
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "related-product"))
        links.append(_link("/knowledge", "Knowledge Hub", "resource"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))
        # Cross-link tools
        tools = ["/budget-estimator", "/design-assist", "/cpd-programme", "/tech-guide", "/for-architects"]
        for t in tools:
            if t != path:
                name = await _get_name(t)
                links.append(_link(t, name, "related-tool"))

    # ── Content hub pages (blog, case-studies, projects, inspirations) ──
    elif path in ["/blog", "/case-studies", "/projects", "/inspirations", "/applications"]:
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "related-product"))
        content_hubs = ["/blog", "/case-studies", "/projects", "/inspirations", "/applications"]
        for ch in content_hubs:
            if ch != path:
                name = await _get_name(ch)
                links.append(_link(ch, name, "sibling-content"))
        links.append(_link("/knowledge", "Knowledge Hub", "resource"))

    # ── Other pages (FAQ, factory-tour, signage-solutions, etc.) ──
    else:
        for f in ALL_FAMILIES:
            name = await _get_name(f)
            links.append(_link(f, name, "related-product"))
        links.append(_link("/knowledge", "Knowledge Hub", "resource"))
        links.append(_link("/case-studies", "Case Studies", "social-proof"))

    # Deduplicate by path
    seen = set()
    unique = []
    for link in links:
        if link["path"] not in seen:
            seen.add(link["path"])
            unique.append(link)
    return unique


@router.get("/api/prerender/internal-links")
async def get_internal_links(path: str = "/"):
    """Return the internal link graph for a given page."""
    links = await build_links_for_page(path)
    return links
