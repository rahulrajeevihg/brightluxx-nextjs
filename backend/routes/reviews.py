"""Product review collection and moderation endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_admin
from anti_spam import validate_submission_full
from utils import get_client_ip
import uuid
import re

router = APIRouter(tags=["Reviews"])

reviews_col = db["reviews"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Public-safe fields only (no email, spam_score, moderated_by)
PUBLIC_FIELDS = {"id": 1, "product_slug": 1, "product_name": 1, "name": 1,
                 "rating": 1, "title": 1, "comment": 1, "created_at": 1, "_id": 0}


# --- Public endpoints ---

@router.get("/api/products/{slug}/reviews")
async def get_product_reviews(slug: str, page: int = 1, limit: int = Query(default=20, le=100)):
    """Get approved reviews for a product (no PII)."""
    query = {"product_slug": slug, "status": "approved"}
    total = await reviews_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = reviews_col.find(query, PUBLIC_FIELDS).sort("created_at", -1).skip(skip).limit(limit)
    reviews = await cursor.to_list(length=limit)

    # Compute aggregate
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    agg = await reviews_col.aggregate(pipeline).to_list(1)
    stats = {"average_rating": round(agg[0]["avg"], 1), "total_reviews": agg[0]["count"]} if agg else {"average_rating": 0, "total_reviews": 0}

    return {"reviews": reviews, "stats": stats, "total": total, "page": page}


@router.post("/api/products/{slug}/reviews")
async def submit_review(slug: str, request: Request):
    """Submit a product review (goes to moderation)."""
    body = await request.json()

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    rating = body.get("rating")
    comment = (body.get("comment") or "").strip()
    title = (body.get("title") or "").strip()

    # Validation
    if not name or len(name) < 2:
        raise HTTPException(400, "Name is required (min 2 characters)")
    if not email or not EMAIL_RE.match(email):
        raise HTTPException(400, "Valid email is required")
    if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be 1-5")
    if not comment or len(comment) < 10:
        raise HTTPException(400, "Review must be at least 10 characters")

    # Check product exists FIRST (before anti-spam, so 404 is always returned for bad slugs)
    product = await db["products"].find_one({"slug": slug}, {"name": 1})
    if not product:
        raise HTTPException(404, "Product not found")

    # Check duplicate (same email + product within 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    existing = await reviews_col.find_one({
        "product_slug": slug,
        "email": email,
        "created_at": {"$gte": thirty_days_ago},
    })
    if existing:
        raise HTTPException(409, "You have already reviewed this product recently")

    # Anti-spam check (lightweight — reviews don't require phone)
    client_ip = get_client_ip(request)
    spam_data = {
        "name": name, "email": email, "message": comment,
        "phone": "",
        "website": body.get("_honeypot", ""),
        "_website": body.get("_website", ""),
    }
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(spam_data, client_ip)
    if not is_valid:
        # Silent success for spammers (honeypot/rate-limit)
        return {"status": "submitted", "message": "Thank you for your review!"}

    review = {
        "id": str(uuid.uuid4()),
        "product_slug": slug,
        "product_name": product.get("name", slug),
        "name": name,
        "email": email,
        "rating": int(rating),
        "title": title[:200] if title else "",
        "comment": comment[:2000],
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "spam_score": spam_score,
    }

    await reviews_col.insert_one(review)
    return {"status": "submitted", "message": "Thank you! Your review will appear after moderation."}


# --- Admin endpoints ---

@router.get("/api/admin/reviews")
async def admin_get_reviews(
    status: str = None,
    product_slug: str = None,
    page: int = 1,
    limit: int = 50,
    admin=Depends(get_current_admin),
):
    """Get all reviews for admin moderation."""
    query = {}
    if status:
        query["status"] = status
    if product_slug:
        query["product_slug"] = product_slug

    total = await reviews_col.count_documents(query)
    skip = (page - 1) * limit
    cursor = reviews_col.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    reviews = await cursor.to_list(length=limit)

    # Stats
    pending = await reviews_col.count_documents({"status": "pending"})
    approved = await reviews_col.count_documents({"status": "approved"})
    rejected = await reviews_col.count_documents({"status": "rejected"})

    return {
        "reviews": reviews,
        "total": total,
        "page": page,
        "stats": {"pending": pending, "approved": approved, "rejected": rejected},
    }


@router.put("/api/admin/reviews/{review_id}")
async def admin_update_review(review_id: str, request: Request, admin=Depends(get_current_admin)):
    """Approve, reject, or update a review."""
    body = await request.json()
    update = {}

    if "status" in body and body["status"] in ("approved", "rejected", "pending"):
        update["status"] = body["status"]
    if "comment" in body:
        update["comment"] = body["comment"][:2000]

    if not update:
        raise HTTPException(400, "No valid fields to update")

    update["updated_at"] = datetime.now(timezone.utc)
    update["moderated_by"] = admin.get("email", "admin")

    result = await reviews_col.update_one({"id": review_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "Review not found")

    # Clear SSR cache when review status changes (affects aggregate rating in Product schema)
    if "status" in update:
        from routes.ssr_meta import clear_ssr_cache
        clear_ssr_cache()

    return {"updated": True}


@router.delete("/api/admin/reviews/{review_id}")
async def admin_delete_review(review_id: str, admin=Depends(get_current_admin)):
    """Delete a review."""
    result = await reviews_col.delete_one({"id": review_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Review not found")
    from routes.ssr_meta import clear_ssr_cache
    clear_ssr_cache()
    return {"deleted": True}
