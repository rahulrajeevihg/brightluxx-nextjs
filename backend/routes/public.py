from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Optional, List
import re

from database import products_col, inspirations_col, projects_col, leads_col
from models import Lead
from utils import serialize_doc, lead_limiter, get_client_ip
from anti_spam import validate_submission_full, check_recaptcha
from email_service import notify_new_lead
import uuid

router = APIRouter()

PRODUCT_SEARCH_SYNONYMS = {
    "video wall": ["led wall", "video wall", "dvled", "videobrick"],
    "led wall": ["led wall", "video wall", "dvled", "videobrick"],
    "digital totem": ["digital totem", "totem", "poster", "standee"],
    "transparent display": ["transparent display", "transparent led", "led film", "smart glass"],
    "meeting room": ["meeting room", "conference", "all-in-one", "iconference"],
    "boardroom": ["boardroom", "conference", "all-in-one", "iconference"],
    "control room": ["control room", "command centre", "command center", "noc"],
    "hotel": ["hotel", "hospitality"],
    "restaurant": ["restaurant", "menu", "digital signage"],
    "kiosk": ["kiosk", "interactive", "self service"],
    "poster": ["poster", "totem", "standee"],
}


def product_search_terms(search: str) -> list[str]:
    normalized = " ".join(search.lower().split())
    terms = [normalized, *PRODUCT_SEARCH_SYNONYMS.get(normalized, [])]
    pitch_match = re.fullmatch(r"p(\d+(?:\.\d+)?)", normalized)
    if pitch_match:
        terms.append(pitch_match.group(1))
    return list(dict.fromkeys(terms))


def product_search_query(search: str) -> dict:
    patterns = [re.escape(term) for term in product_search_terms(search) if term]
    if not patterns:
        return {}
    regex = "|".join(patterns)
    return {"$or": [{field: {"$regex": regex, "$options": "i"}} for field in (
        "name", "product_code", "description", "application", "category",
        "pixel_pitch", "brightness", "technology", "display_type", "product_family",
    )]}


def catalogue_product(doc: dict) -> dict:
    product = serialize_doc(doc)
    if not product.get("refresh_rate"):
        for spec in product.get("key_specs") or []:
            if str(spec.get("label", "")).strip().lower() == "refresh rate" and spec.get("value"):
                product["refresh_rate"] = spec["value"]
                break
    return product


@router.get("/api/products")
async def get_products(
    category: Optional[str] = None, 
    sub_category: Optional[str] = None,
    featured: Optional[bool] = None, 
    trending: Optional[bool] = None, 
    new_arrival: Optional[bool] = None, 
    search: Optional[str] = None,
    pitch_range: Optional[str] = None,
    limit: Optional[int] = None
):
    query = {}
    if category:
        query["category"] = category
    if sub_category:
        query["sub_category"] = sub_category
    if featured is not None:
        query["featured"] = featured
    if trending is not None:
        query["trending"] = trending
    if new_arrival is not None:
        query["new_arrival"] = new_arrival
    if search:
        query.update(product_search_query(search))
    
    cursor = products_col.find(query).sort("created_at", -1)
    products = [catalogue_product(doc) for doc in await cursor.to_list(length=200)]
    
    # Filter by pitch range if specified (done in Python for flexibility with various formats)
    if pitch_range:
        def extract_pitch_mm(pitch_str):
            """Extract numeric pitch value in mm from various formats like '1.5mm', 'P1.5', '0.9'"""
            if not pitch_str or pitch_str.startswith('N/A'):
                return None
            import re
            match = re.search(r'(\d+\.?\d*)', pitch_str)
            if match:
                return float(match.group(1))
            return None
        
        pitch_ranges = {
            'ultra-fine': (0, 1.0),      # < 1.0mm - Control rooms, boardrooms
            'fine': (1.0, 2.0),          # 1.0-2.0mm - Lobbies, retail
            'standard': (2.0, 4.0),      # 2.0-4.0mm - Showrooms, events
            'outdoor': (4.0, 100),       # > 4.0mm - Outdoor, billboards
        }
        
        if pitch_range in pitch_ranges:
            min_pitch, max_pitch = pitch_ranges[pitch_range]
            filtered = []
            for p in products:
                pitch_val = extract_pitch_mm(p.get('pixel_pitch', ''))
                if pitch_val is not None:
                    if pitch_range == 'ultra-fine' and pitch_val < max_pitch:
                        filtered.append(p)
                    elif pitch_range == 'outdoor' and pitch_val >= min_pitch:
                        filtered.append(p)
                    elif min_pitch <= pitch_val < max_pitch:
                        filtered.append(p)
            products = filtered

    if limit and limit > 0:
        products = products[:limit]

    return {"products": products}


@router.get("/api/products/categories")
async def get_product_categories():
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    categories = []
    async for doc in products_col.aggregate(pipeline):
        categories.append({"value": doc["_id"], "label": doc["_id"].replace("-", " ").title(), "count": doc["count"]})
    return {"categories": categories}


@router.post("/api/products/compare")
async def compare_products(product_codes: List[str]):
    if len(product_codes) < 2 or len(product_codes) > 4:
        raise HTTPException(status_code=400, detail="Select 2-4 products to compare")
    cursor = products_col.find({"product_code": {"$in": product_codes}})
    products = [serialize_doc(doc) async for doc in cursor]
    return {"products": products}


@router.post("/api/calculator/screen-size")
async def calculate_screen_size(data: dict):
    width = data.get("venue_width", 10)
    height = data.get("venue_height", 3)
    viewing_distance = data.get("viewing_distance", 5)
    content_type = data.get("content_type", "video")
    indoor = data.get("indoor", True)
    recommended_pitch = round(viewing_distance / 1.5, 2)
    if content_type == "text":
        recommended_pitch = min(recommended_pitch, 1.5)
    elif content_type == "mixed":
        recommended_pitch = min(recommended_pitch, 2.5)
    available_pitches = [0.4, 0.6, 0.9, 1.2, 1.5, 1.9, 2.5, 2.9, 3.9, 4.7, 6.8, 7.8]
    closest_pitch = min(available_pitches, key=lambda x: abs(x - recommended_pitch))
    screen_width = min(width * 0.85, width - 0.5)
    screen_height = min(height * 0.7, height - 0.5)
    screen_area = round(screen_width * screen_height, 1)
    pixels_per_m = round(1000 / closest_pitch)
    res_w = int(screen_width * pixels_per_m)
    res_h = int(screen_height * pixels_per_m)
    brightness = "600-1,200 nits" if indoor else "5,000-10,000 nits"
    pitch_query = {"pixel_pitch": {"$regex": str(closest_pitch)}}
    matching = [serialize_doc(doc) for doc in await products_col.find(pitch_query).to_list(length=5)]
    return {
        "recommended_pitch": closest_pitch,
        "screen_width": round(screen_width, 1),
        "screen_height": round(screen_height, 1),
        "screen_area": screen_area,
        "resolution": f"{res_w} x {res_h}",
        "brightness": brightness,
        "matching_products": matching,
        "tips": [
            f"At {viewing_distance}m viewing distance, {closest_pitch}mm pitch provides optimal clarity.",
            f"Screen area: {screen_area} sqm ({round(screen_width, 1)}m x {round(screen_height, 1)}m).",
            f"Recommended brightness: {brightness} for {'indoor' if indoor else 'outdoor'} use."
        ]
    }


@router.get("/api/products/{slug}")
async def get_product(slug: str):
    product = await products_col.find_one({"slug": slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return catalogue_product(product)


@router.get("/api/inspirations")
async def get_inspirations(category: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    cursor = inspirations_col.find(query).sort("created_at", -1)
    inspirations = [serialize_doc(doc) for doc in await cursor.to_list(length=100)]
    return {"inspirations": inspirations}


@router.get("/api/projects")
async def get_projects(sector: Optional[str] = None, featured: Optional[bool] = None, limit: Optional[int] = None):
    query = {}
    if sector:
        query["sector"] = sector
    if featured is not None:
        query["featured"] = featured
    cursor = projects_col.find(query).sort("created_at", -1)
    projects = [serialize_doc(doc) for doc in await cursor.to_list(length=min(limit, 100) if limit and limit > 0 else 100)]
    return {"projects": projects}


@router.get("/api/projects/{slug}")
async def get_project(slug: str):
    project = await projects_col.find_one({"slug": slug})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serialize_doc(project)


@router.post("/api/leads")
async def create_lead(lead: Lead, request: Request):
    client_ip = get_client_ip(request)
    lead_dict = lead.dict()

    # Anti-spam + geo IP validation
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(lead_dict, client_ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Thank you! We'll contact you within 2 hours.", "leadId": "ok"}
        raise HTTPException(status_code=422, detail=error_msg)

    # reCAPTCHA v3 verification
    recaptcha_result = await check_recaptcha(request)

    lead_dict["id"] = str(uuid.uuid4())
    lead_dict["status"] = "new"
    lead_dict["notes"] = ""
    lead_dict["spam_score"] = spam_score
    lead_dict["ip"] = client_ip
    lead_dict["geo"] = {"country": geo_data.get("country", ""), "country_name": geo_data.get("country_name", ""), "city": geo_data.get("city", ""), "region": geo_data.get("region", ""), "isp": geo_data.get("isp", "")}
    result = await leads_col.insert_one(lead_dict)
    print(f"New lead from {lead.name} ({lead.email}) - {lead.application} [spam_score={spam_score}]")

    # Send email notification (fire-and-forget)
    try:
        await notify_new_lead({**lead_dict, "source": "contact_form"})
    except Exception:
        pass

    return {
        "success": True,
        "message": "Thank you! We'll contact you within 2 hours.",
        "leadId": str(result.inserted_id)
    }


@router.get("/api/search")
async def search(q: str):
    results = {"products": [], "inspirations": [], "projects": []}
    prod_cursor = products_col.find(product_search_query(q)).limit(5)
    results["products"] = [serialize_doc(doc) for doc in await prod_cursor.to_list(length=5)]
    return results
