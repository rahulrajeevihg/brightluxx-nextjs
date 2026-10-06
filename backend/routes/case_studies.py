"""
Case Studies API routes for managing project case studies.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
import uuid
import os
import re

from database import db
from auth import get_current_admin
from routes.ssr_meta import clear_ssr_cache
router = APIRouter()

case_studies_col = db["case_studies"]


def slugify(text: str) -> str:
    """Generate URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


class CaseStudyCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    category: str
    location: str
    year: str
    client: str
    consultant: str
    contractor: str
    hero_image: Optional[str] = None
    thumbnail: Optional[str] = None
    technology: str
    tech_id: str
    pixel_pitch: str
    display_size: str
    challenge: str
    solution: str
    results: List[str] = []
    specs: List[List[str]] = []
    tags: List[str] = []
    is_published: bool = True
    featured: bool = False


class CaseStudyUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    year: Optional[str] = None
    client: Optional[str] = None
    consultant: Optional[str] = None
    contractor: Optional[str] = None
    hero_image: Optional[str] = None
    thumbnail: Optional[str] = None
    technology: Optional[str] = None
    tech_id: Optional[str] = None
    pixel_pitch: Optional[str] = None
    display_size: Optional[str] = None
    challenge: Optional[str] = None
    solution: Optional[str] = None
    results: Optional[List[str]] = None
    specs: Optional[List[List[str]]] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None


# Categories for case studies
CASE_STUDY_CATEGORIES = [
    {"id": "all", "label": "All Projects"},
    {"id": "retail", "label": "Retail"},
    {"id": "hospitality", "label": "Hospitality"},
    {"id": "corporate", "label": "Corporate"},
    {"id": "f&b", "label": "F&B / Restaurant"},
    {"id": "healthcare", "label": "Healthcare"},
    {"id": "jewellery", "label": "Jewellery & Luxury"},
    {"id": "residential", "label": "Residential"},
    {"id": "fashion", "label": "Fashion"},
    {"id": "salon", "label": "Salon & Spa"},
    {"id": "supermarket", "label": "Supermarket"},
    {"id": "fragrance", "label": "Fragrance"},
    {"id": "bespoke", "label": "Bespoke Lighting"},
    {"id": "transport", "label": "Transport"},
    {"id": "entertainment", "label": "Entertainment"},
]


# Public endpoints
@router.get("/api/case-studies")
async def get_published_case_studies(category: Optional[str] = None):
    """Get all published case studies for the public page."""
    query = {"is_published": True}
    if category and category.lower() != "all":
        query["category"] = category
    
    cursor = case_studies_col.find(query, {"_id": 0}).sort("created_at", -1)
    case_studies = await cursor.to_list(length=100)
    
    return {
        "case_studies": case_studies,
        "categories": CASE_STUDY_CATEGORIES
    }


@router.get("/api/case-studies/{slug}")
async def get_case_study_by_slug(slug: str):
    """Get a single case study by slug for the detail page."""
    case_study = await case_studies_col.find_one({"slug": slug, "is_published": True}, {"_id": 0})
    if not case_study:
        raise HTTPException(status_code=404, detail="Case study not found")
    return {"case_study": case_study}


# Admin endpoints
@router.get("/api/admin/case-studies")
async def admin_get_case_studies(admin=Depends(get_current_admin)):
    """Get all case studies for admin (including unpublished)."""
    cursor = case_studies_col.find({}, {"_id": 0}).sort("created_at", -1)
    case_studies = await cursor.to_list(length=500)
    
    counts = {
        "total": await case_studies_col.count_documents({}),
        "published": await case_studies_col.count_documents({"is_published": True}),
        "drafts": await case_studies_col.count_documents({"is_published": False}),
        "featured": await case_studies_col.count_documents({"featured": True}),
    }
    
    # Count by category
    for cat in CASE_STUDY_CATEGORIES:
        if cat["id"] != "all":
            counts[cat["id"]] = await case_studies_col.count_documents({"category": cat["id"]})
    
    return {
        "case_studies": case_studies,
        "counts": counts,
        "categories": CASE_STUDY_CATEGORIES
    }


@router.post("/api/admin/case-studies")
async def create_case_study(data: CaseStudyCreate, admin=Depends(get_current_admin)):
    """Create a new case study."""
    case_id = str(uuid.uuid4())[:12]
    
    # Generate slug if not provided
    slug = data.slug or slugify(data.title)
    
    # Ensure unique slug
    existing = await case_studies_col.find_one({"slug": slug})
    if existing:
        slug = f"{slug}-{case_id[:4]}"
    
    now = datetime.now(timezone.utc)
    
    case_study = {
        "id": case_id,
        "title": data.title,
        "slug": slug,
        "category": data.category,
        "location": data.location,
        "year": data.year,
        "client": data.client,
        "consultant": data.consultant,
        "contractor": data.contractor,
        "hero_image": data.hero_image,
        "thumbnail": data.thumbnail,
        "technology": data.technology,
        "tech_id": data.tech_id,
        "pixel_pitch": data.pixel_pitch,
        "display_size": data.display_size,
        "challenge": data.challenge,
        "solution": data.solution,
        "results": data.results,
        "specs": data.specs,
        "tags": data.tags,
        "is_published": data.is_published,
        "featured": data.featured,
        "created_at": now,
        "updated_at": now,
    }
    
    await case_studies_col.insert_one(case_study)
    clear_ssr_cache()
    return {"success": True, "case_study": {k: v for k, v in case_study.items() if k != "_id"}}


@router.post("/api/admin/case-studies/upload-image")
async def upload_case_study_image(
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Upload an image for a case study."""
    from cdn_upload import upload_image_to_cdn
    
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
        )
    
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    unique_name = f"case_study_{uuid.uuid4().hex[:8]}{ext}"
    
    content = await file.read()
    
    try:
        image_url = upload_image_to_cdn(unique_name, content, "case-studies")
        
        return {
            "success": True,
            "image_url": image_url,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/api/admin/case-studies/{case_id}")
async def update_case_study(case_id: str, data: CaseStudyUpdate, admin=Depends(get_current_admin)):
    """Update a case study."""
    existing = await case_studies_col.find_one({"id": case_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Case study not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # If slug changed, ensure uniqueness
    if data.slug and data.slug != existing.get("slug"):
        slug_exists = await case_studies_col.find_one({"slug": data.slug, "id": {"$ne": case_id}})
        if slug_exists:
            raise HTTPException(status_code=400, detail="Slug already exists")
    
    await case_studies_col.update_one({"id": case_id}, {"$set": update_data})
    clear_ssr_cache()
    updated = await case_studies_col.find_one({"id": case_id}, {"_id": 0})
    return {"success": True, "case_study": updated}


@router.delete("/api/admin/case-studies/{case_id}")
async def delete_case_study(case_id: str, admin=Depends(get_current_admin)):
    """Delete a case study."""
    result = await case_studies_col.delete_one({"id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case study not found")
    clear_ssr_cache()
    return {"success": True, "message": "Case study deleted"}


@router.post("/api/admin/case-studies/seed")
async def seed_case_studies(admin=Depends(get_current_admin)):
    """Seed the database with existing case studies data."""
    existing_count = await case_studies_col.count_documents({})
    if existing_count > 0:
        return {"success": False, "message": f"Case studies already exist ({existing_count} found)."}
    
    now = datetime.now(timezone.utc)
    
    # Existing case studies data
    case_studies_data = [
        {
            "id": "jumeirah-al-naseem-lobby",
            "title": "Jumeirah Al Naseem — Immersive Lobby Experience",
            "slug": "jumeirah-al-naseem-lobby",
            "category": "hospitality",
            "location": "Dubai, UAE",
            "year": "2025",
            "client": "Jumeirah Group",
            "consultant": "Gensler Middle East",
            "contractor": "Depa Interiors",
            "hero_image": "https://images.unsplash.com/photo-1768346564825-6f90c0b89e2e?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1768346564825-6f90c0b89e2e?w=600&q=80",
            "technology": "MicroLED",
            "tech_id": "microled",
            "pixel_pitch": "P0.7",
            "display_size": "12m x 3.5m (42 sqm)",
            "challenge": "The hotel required a signature digital art wall in the main lobby that could display curated fine art and immersive ocean content. The display needed to be invisible when off — no visible bezels, no pixel structure visible from 2m viewing distance. The environment demanded near-silent operation and minimal heat output.",
            "solution": "We specified a seamless MicroLED wall at P0.7 pixel pitch with a custom concave curve to wrap the reception area. The display was front-serviceable with quick-release modules for maintenance without disrupting guests. A custom content management system was integrated with the hotel's BMS for automated scheduling.",
            "results": [
                "Guest engagement scores increased 34% in post-stay surveys",
                "Featured in Hospitality Design magazine and 3 regional publications",
                "Display achieved DCI-P3 97% colour accuracy verified by independent calibration",
                "Zero unplanned downtime in first 12 months of operation"
            ],
            "specs": [
                ["Technology", "MicroLED (Self-Emissive)"],
                ["Pixel Pitch", "P0.7"],
                ["Total Resolution", "17,142 x 5,000 (85+ megapixels)"],
                ["Brightness", "1,200 nits (calibrated)"],
                ["Contrast", "> 1,000,000:1"],
                ["Display Size", "12m x 3.5m (42 sqm)"],
                ["Refresh Rate", "3,840 Hz"],
                ["Power Consumption", "168 W/sqm average"],
                ["Service Access", "Front-service, magnetic modules"],
                ["Content System", "Integrated CMS with BMS scheduling"]
            ],
            "tags": ["luxury", "5-star", "lobby", "art wall", "microled", "curved"],
            "is_published": True,
            "featured": True
        },
        {
            "id": "dubai-mall-flagship-retail",
            "title": "Dubai Mall — Flagship Retail Digital Storefront",
            "slug": "dubai-mall-flagship-retail",
            "category": "retail",
            "location": "Dubai, UAE",
            "year": "2025",
            "client": "Confidential Luxury Brand",
            "consultant": "Callison RTKL",
            "contractor": "ISG Interior Services",
            "hero_image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80",
            "technology": "COB LED",
            "tech_id": "cob-led",
            "pixel_pitch": "P0.9",
            "display_size": "8m x 4m (32 sqm)",
            "challenge": "A luxury fashion house needed a statement digital wall behind the cash wrap area. The display had to render fabric textures and product photography with absolute colour fidelity. Ambient light from the glass facade reached 2,000 lux at peak hours, requiring high brightness without compromising energy budgets.",
            "solution": "COB LED at P0.9 was specified to deliver exceptional contrast and colour accuracy within budget. An anti-glare nano-coating reduced reflections by 65%. The display was integrated with the brand's global digital asset management platform for real-time content updates from HQ.",
            "results": [
                "Footfall conversion rate increased 22% vs previous static display period",
                "Brand reported 15% uplift in average transaction value in first quarter",
                "Colour accuracy certified at sRGB 120% by independent auditor",
                "Monthly energy cost 40% below client's original budget projection"
            ],
            "specs": [
                ["Technology", "COB LED (Chip-on-Board)"],
                ["Pixel Pitch", "P0.9"],
                ["Total Resolution", "8,888 x 4,444 (39+ megapixels)"],
                ["Brightness", "800 nits (auto-dimming)"],
                ["Contrast", "20,000:1"],
                ["Display Size", "8m x 4m (32 sqm)"],
                ["Surface Treatment", "Anti-glare nano-coating"],
                ["Refresh Rate", "3,840 Hz"],
                ["Power Consumption", "130 W/sqm average"],
                ["Content Integration", "DAM platform API integration"]
            ],
            "tags": ["luxury", "fashion", "retail", "cob", "high-brightness", "anti-glare"],
            "is_published": True,
            "featured": True
        },
        {
            "id": "adnoc-hq-command-center",
            "title": "ADNOC HQ — Unified Command Center",
            "slug": "adnoc-hq-command-center",
            "category": "corporate",
            "location": "Abu Dhabi, UAE",
            "year": "2024",
            "client": "ADNOC Group",
            "consultant": "HOK Architects",
            "contractor": "Al Jaber Engineering",
            "hero_image": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&q=80",
            "technology": "Fine Pitch LED",
            "tech_id": "fine-pitch-led",
            "pixel_pitch": "P1.2",
            "display_size": "18m x 3m (54 sqm)",
            "challenge": "The corporate command center required a massive video wall capable of displaying real-time operational data from 40+ sources simultaneously. The display needed 24/7 operation reliability, front serviceability for zero-downtime maintenance, and integration with 6 different data visualization platforms.",
            "solution": "A Fine Pitch LED wall at P1.2 was specified for the optimal balance of resolution, reliability, and cost at 3m+ viewing distance. Redundant power supplies and signal processing ensured zero single points of failure. Custom input matrix allowed any source to be displayed at any position and size on the wall.",
            "results": [
                "Operational response time improved 28% with unified data visualization",
                "Zero unplanned downtime in 18 months of 24/7 operation",
                "Total cost of ownership 45% lower than comparable LCD video wall solution",
                "Maintenance time reduced from 4 hours to 15 minutes with front-service design"
            ],
            "specs": [
                ["Technology", "Fine Pitch LED (SMD 4-in-1)"],
                ["Pixel Pitch", "P1.2"],
                ["Total Resolution", "15,000 x 2,500 (37+ megapixels)"],
                ["Brightness", "600 nits (always-on calibrated)"],
                ["Contrast", "8,000:1"],
                ["Display Size", "18m x 3m (54 sqm)"],
                ["Operation", "24/7 continuous"],
                ["Redundancy", "Dual power, dual signal processing"],
                ["Power Consumption", "110 W/sqm average"],
                ["Input Sources", "40+ via custom matrix switcher"]
            ],
            "tags": ["command center", "corporate", "24/7", "mission-critical", "fine-pitch"],
            "is_published": True,
            "featured": False
        },
        {
            "id": "riyadh-metro-passenger-info",
            "title": "Riyadh Metro — Passenger Information Displays",
            "slug": "riyadh-metro-passenger-info",
            "category": "transport",
            "location": "Riyadh, KSA",
            "year": "2025",
            "client": "Royal Commission for Riyadh City",
            "consultant": "Bechtel / FAST Consortium",
            "contractor": "Samsung C&T",
            "hero_image": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600&q=80",
            "technology": "Fine Pitch LED",
            "tech_id": "fine-pitch-led",
            "pixel_pitch": "P1.5",
            "display_size": "186 displays, 4-12 sqm each",
            "challenge": "The metro system required 186 high-brightness LED displays across 22 stations for passenger information, wayfinding, and advertising. Displays needed to withstand temperature fluctuations, high dust environments, and 20-hour daily operation while maintaining IP54 rating for semi-outdoor platform areas.",
            "solution": "Fine Pitch LED at P1.5 was deployed in custom IP54-rated enclosures with active cooling and dust filtration. Each display was connected to a centralized CMS for real-time schedule updates, emergency messaging, and revenue-generating advertising content. The deployment was phased across 22 stations over 14 months.",
            "results": [
                "All 186 displays operational within 14-month deployment window",
                "Passenger satisfaction scores for wayfinding improved 41%",
                "Advertising revenue covering 60% of display operating costs",
                "99.7% uptime achieved across all displays in first operational year"
            ],
            "specs": [
                ["Technology", "Fine Pitch LED (Outdoor-Rated)"],
                ["Pixel Pitch", "P1.5"],
                ["Brightness", "1,500 — 3,000 nits (auto-adjusting)"],
                ["IP Rating", "IP54 (semi-outdoor rated)"],
                ["Displays Deployed", "186 units across 22 stations"],
                ["Size Range", "4 — 12 sqm per display"],
                ["Operation", "20 hours/day"],
                ["Cooling", "Active cooling with dust filtration"],
                ["CMS", "Centralized with emergency override"],
                ["Network", "Redundant fibre + 4G failover"]
            ],
            "tags": ["metro", "transport", "mass-deployment", "ip54", "outdoor", "wayfinding"],
            "is_published": True,
            "featured": False
        },
        {
            "id": "expo-city-dubai-event-hall",
            "title": "Expo City Dubai — Multi-Purpose Event Hall",
            "slug": "expo-city-dubai-event-hall",
            "category": "entertainment",
            "location": "Dubai, UAE",
            "year": "2025",
            "client": "Expo City Dubai Authority",
            "consultant": "Populous Architects",
            "contractor": "Laing O'Rourke",
            "hero_image": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600&q=80",
            "technology": "Creative LED",
            "tech_id": "creative-led",
            "pixel_pitch": "P2.6",
            "display_size": "360-degree cylindrical, 280 sqm total",
            "challenge": "A 5,000-seat multi-purpose venue needed a 360-degree cylindrical LED display for concerts, conferences, and immersive brand experiences. The display had to support rapid content changeover between event types, withstand rigging loads, and deliver consistent image quality across the full 360-degree viewing angle.",
            "solution": "Custom Creative LED modules at P2.6 were engineered into a cylindrical structure suspended from the venue's rigging grid. The display was divided into 12 independently addressable zones for maximum content flexibility. A Brompton processing system was specified for seamless 360-degree content mapping.",
            "results": [
                "Venue booking rate increased 35% year-over-year after installation",
                "Event setup time reduced from 8 hours to 2 hours with preset configurations",
                "Featured as a landmark installation in InfoComm Middle East keynote",
                "Client recovered investment within 18 months through premium event pricing"
            ],
            "specs": [
                ["Technology", "Creative LED (Custom Curved Modules)"],
                ["Pixel Pitch", "P2.6"],
                ["Configuration", "360-degree cylindrical"],
                ["Total Area", "280 sqm"],
                ["Brightness", "2,000 nits"],
                ["Contrast", "6,000:1"],
                ["Zones", "12 independently addressable segments"],
                ["Processing", "Brompton Tessera SX40"],
                ["Rigging", "Custom steel frame, 12-point fly system"],
                ["Power", "Redundant 3-phase, 84 kW total"]
            ],
            "tags": ["entertainment", "creative", "360-degree", "cylindrical", "events", "immersive"],
            "is_published": True,
            "featured": False
        },
        {
            "id": "cleveland-clinic-abu-dhabi",
            "title": "Cleveland Clinic Abu Dhabi — Patient Wayfinding System",
            "slug": "cleveland-clinic-abu-dhabi",
            "category": "healthcare",
            "location": "Abu Dhabi, UAE",
            "year": "2024",
            "client": "Mubadala Health",
            "consultant": "HDR Architecture",
            "contractor": "Consolidated Contractors Company",
            "hero_image": "https://images.unsplash.com/photo-1626204717650-96d57481eeb3?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1626204717650-96d57481eeb3?w=600&q=80",
            "technology": "All-in-One dvLED",
            "tech_id": "all-in-one-dvled",
            "pixel_pitch": "P1.2",
            "display_size": "24 displays, 130\" — 165\" each",
            "challenge": "The hospital needed a network of digital wayfinding displays that could integrate with the hospital information system (HIS) for real-time patient flow management. Displays had to be antimicrobial-rated, low-EMI for medical equipment compatibility, and simple enough for facilities staff to maintain without AV specialists.",
            "solution": "All-in-One dvLED displays at P1.2 were deployed as a plug-and-play solution. The pre-assembled units eliminated complex installation, while built-in Android SoC processors ran the wayfinding application without external media players. Custom antimicrobial surface treatment was applied to all display faces.",
            "results": [
                "Patient wayfinding complaints reduced by 52% within 3 months",
                "Staff time spent on directions reduced by estimated 340 hours/month",
                "Facilities team manages all displays without dedicated AV support",
                "EMI testing confirmed zero interference with medical imaging equipment"
            ],
            "specs": [
                ["Technology", "All-in-One dvLED"],
                ["Pixel Pitch", "P1.2"],
                ["Display Sizes", "130\" and 165\" (pre-assembled)"],
                ["Units Deployed", "24 across 8 floors"],
                ["Resolution", "4K UHD per display"],
                ["Brightness", "400 nits (healthcare-optimized)"],
                ["Surface", "Antimicrobial nano-coating"],
                ["Processing", "Built-in Android SoC"],
                ["EMI Rating", "Class B (medical-grade)"],
                ["Integration", "HIS API for real-time patient flow"]
            ],
            "tags": ["healthcare", "wayfinding", "hospital", "all-in-one", "antimicrobial", "plug-and-play"],
            "is_published": True,
            "featured": False
        },
        {
            "id": "the-view-at-the-palm-transparent",
            "title": "The View at The Palm — Transparent Observation Deck",
            "slug": "the-view-at-the-palm-transparent",
            "category": "entertainment",
            "location": "Dubai, UAE",
            "year": "2025",
            "client": "Nakheel",
            "consultant": "Atkins",
            "contractor": "Arabtec Construction",
            "hero_image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&q=80",
            "technology": "Transparent LED",
            "tech_id": "transparent-led",
            "pixel_pitch": "P3.9",
            "display_size": "26m x 8m (208 sqm)",
            "challenge": "The observation deck at the Palm Tower needed digital signage on floor-to-ceiling glass facades without obstructing the panoramic view. The display had to maintain 85%+ transparency during the day while being bright enough for content visibility in direct sunlight. Wind loads at 240m height added structural engineering complexity.",
            "solution": "Transparent LED mesh at P3.9 was bonded directly to the structural glazing using a custom mounting system engineered for Category 3 wind loads. Auto-brightness sensors adjust output from 500 nits (evening) to 5,000 nits (direct sunlight) to ensure consistent visibility without overwhelming the view.",
            "results": [
                "Visitor satisfaction scores for the observation experience rated 4.7/5",
                "Transparency measured at 87% — exceeding the 85% minimum requirement",
                "Additional revenue stream from branded content partnerships",
                "Installation won \"Best Digital Experience\" at Middle East Leisure Awards"
            ],
            "specs": [
                ["Technology", "Transparent LED Mesh"],
                ["Pixel Pitch", "P3.9"],
                ["Transparency", "87%"],
                ["Total Area", "26m x 8m (208 sqm)"],
                ["Brightness", "500 — 5,000 nits (auto-adjusting)"],
                ["Wind Load Rating", "Category 3 (240m height)"],
                ["Mounting", "Structural glazing bond"],
                ["Weight", "12 kg/sqm (mesh only)"],
                ["Power", "85 W/sqm average"],
                ["Control", "Centralized with daylight sensor integration"]
            ],
            "tags": ["transparent", "observation", "glass-facade", "high-rise", "tourism", "iconic"],
            "is_published": True,
            "featured": False
        },
        {
            "id": "kapsarc-3d-anamorphic",
            "title": "KAPSARC — 3D Anamorphic Corner Display",
            "slug": "kapsarc-3d-anamorphic",
            "category": "corporate",
            "location": "Riyadh, KSA",
            "year": "2025",
            "client": "King Abdullah Petroleum Studies and Research Center",
            "consultant": "Zaha Hadid Architects",
            "contractor": "Saudi Binladin Group",
            "hero_image": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=1200&q=80",
            "thumbnail": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=600&q=80",
            "technology": "3D Anamorphic LED",
            "tech_id": "3d-anamorphic-led",
            "pixel_pitch": "P2.5",
            "display_size": "Corner: 12m x 6m per face (144 sqm total)",
            "challenge": "KAPSARC wanted a landmark digital installation at the main entrance that would communicate their energy research mission through glasses-free 3D content. The L-shaped corner display needed precise calibration for the 3D illusion to work from the designated 30m viewing zone, with content that could be updated for visiting delegations.",
            "solution": "3D Anamorphic LED at P2.5 was installed in a precision-engineered L-shaped corner configuration. Custom 3D content was produced showing energy molecules, data visualizations, and the KAPSARC crystal structure in dramatic forced-perspective. A dedicated rendering workstation generates real-time 3D content.",
            "results": [
                "Installation became the #1 photographed feature on campus",
                "Social media impressions exceeded 2M in the first month",
                "Visiting delegations consistently cite the display as a highlight",
                "Content team produces new 3D sequences monthly with in-house tools"
            ],
            "specs": [
                ["Technology", "3D Anamorphic LED"],
                ["Pixel Pitch", "P2.5"],
                ["Configuration", "L-shaped corner, 90-degree"],
                ["Face Size", "12m x 6m per face"],
                ["Total Area", "144 sqm"],
                ["Brightness", "6,000 nits"],
                ["Optimal Viewing", "25 — 40m distance, 30-degree cone"],
                ["3D Content", "Real-time rendering workstation"],
                ["Refresh Rate", "3,840 Hz (flicker-free for cameras)"],
                ["Structural", "Steel subframe with seismic rating"]
            ],
            "tags": ["3d", "anamorphic", "landmark", "corporate", "corner-display", "glasses-free"],
            "is_published": True,
            "featured": False
        }
    ]
    
    for cs in case_studies_data:
        cs["created_at"] = now
        cs["updated_at"] = now
    
    await case_studies_col.insert_many(case_studies_data)
    
    return {"success": True, "message": f"Seeded {len(case_studies_data)} case studies"}
