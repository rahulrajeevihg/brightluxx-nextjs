"""Analytics tracking and reporting endpoints."""
from fastapi import APIRouter, Request, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel

from database import analytics_col, perf_col, leads_col, products_col, projects_col, inspirations_col
from auth import get_current_admin

router = APIRouter()


class TrackEvent(BaseModel):
    event: str  # page_view, product_view, cta_click, quote_request
    page: str = ""
    referrer: str = ""
    product_slug: str = ""
    category: str = ""
    session_id: str = ""
    screen_width: int = 0
    product_code: str = ""
    product_name: str = ""
    application: str = ""
    search_term: str = ""
    filters: str = ""
    finder_result: str = ""
    comparison_codes: List[str] = []
    form_type: str = ""


@router.post("/api/track")
async def track_event(data: TrackEvent, request: Request):
    """Lightweight event tracking endpoint. No auth required."""
    ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
    ua = request.headers.get("user-agent", "")

    doc = {
        "event": data.event,
        "page": data.page,
        "referrer": data.referrer,
        "product_slug": data.product_slug,
        "category": data.category,
        "session_id": data.session_id,
        "screen_width": data.screen_width,
        "product_code": data.product_code,
        "product_name": data.product_name,
        "application": data.application,
        "search_term": data.search_term,
        "filters": data.filters,
        "finder_result": data.finder_result,
        "comparison_codes": data.comparison_codes,
        "form_type": data.form_type,
        "ip_hash": str(hash(ip))[-8:],
        "ua_short": ua[:100],
        "ts": datetime.now(timezone.utc),
    }
    await analytics_col.insert_one(doc)
    return {"ok": True}


@router.get("/api/health")
async def health_check():
    """Health check endpoint for uptime monitoring."""
    try:
        await products_col.count_documents({})
        db_status = "healthy"
    except Exception:
        db_status = "degraded"

    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/admin/analytics")
async def get_analytics(
    days: int = 30,
    admin=Depends(get_current_admin),
):
    """Aggregated analytics data for the admin dashboard."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Page views over time (daily)
    daily_pipeline = [
        {"$match": {"event": "page_view", "ts": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}},
            "views": {"$sum": 1},
            "unique_sessions": {"$addToSet": "$session_id"},
        }},
        {"$project": {"_id": 0, "date": "$_id", "views": 1, "unique_visitors": {"$size": "$unique_sessions"}}},
        {"$sort": {"date": 1}},
    ]
    daily_views = await analytics_col.aggregate(daily_pipeline).to_list(length=60)

    # Top pages
    top_pages_pipeline = [
        {"$match": {"event": "page_view", "ts": {"$gte": since}}},
        {"$group": {"_id": "$page", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "page": "$_id", "views": 1}},
    ]
    top_pages = await analytics_col.aggregate(top_pages_pipeline).to_list(length=10)

    # Top products viewed
    top_products_pipeline = [
        {"$match": {"event": "product_view", "ts": {"$gte": since}, "product_slug": {"$ne": ""}}},
        {"$group": {"_id": "$product_slug", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "slug": "$_id", "views": 1}},
    ]
    top_products = await analytics_col.aggregate(top_products_pipeline).to_list(length=10)

    # Category engagement
    category_pipeline = [
        {"$match": {"event": "product_view", "ts": {"$gte": since}, "category": {"$ne": ""}}},
        {"$group": {"_id": "$category", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$project": {"_id": 0, "category": "$_id", "views": 1}},
    ]
    categories = await analytics_col.aggregate(category_pipeline).to_list(length=20)

    # CTA clicks
    cta_pipeline = [
        {"$match": {"event": "cta_click", "ts": {"$gte": since}}},
        {"$group": {"_id": "$page", "clicks": {"$sum": 1}}},
        {"$sort": {"clicks": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "cta": "$_id", "clicks": 1}},
    ]
    cta_clicks = await analytics_col.aggregate(cta_pipeline).to_list(length=10)

    # Totals
    total_views = await analytics_col.count_documents({"event": "page_view", "ts": {"$gte": since}})
    unique_visitors_pipeline = [
        {"$match": {"event": "page_view", "ts": {"$gte": since}}},
        {"$group": {"_id": "$session_id"}},
        {"$count": "total"}
    ]
    uv_result = await analytics_col.aggregate(unique_visitors_pipeline).to_list(length=1)
    unique_visitors = uv_result[0]["total"] if uv_result else 0

    # Device breakdown
    device_pipeline = [
        {"$match": {"event": "page_view", "ts": {"$gte": since}, "screen_width": {"$gt": 0}}},
        {"$group": {
            "_id": {"$cond": [{"$lte": ["$screen_width", 768]}, "mobile", {"$cond": [{"$lte": ["$screen_width", 1024]}, "tablet", "desktop"]}]},
            "count": {"$sum": 1},
        }},
        {"$project": {"_id": 0, "device": "$_id", "count": 1}},
    ]
    devices = await analytics_col.aggregate(device_pipeline).to_list(length=3)

    # Lead funnel
    total_leads = await leads_col.count_documents({"created_at": {"$gte": since}})
    quote_leads = await leads_col.count_documents({"source": "product_detail", "created_at": {"$gte": since}})
    contact_leads = await leads_col.count_documents({"source": "contact_form", "created_at": {"$gte": since}})

    # Referrer breakdown
    referrer_pipeline = [
        {"$match": {"event": "page_view", "ts": {"$gte": since}, "referrer": {"$ne": ""}}},
        {"$group": {"_id": "$referrer", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "referrer": "$_id", "count": 1}},
    ]
    referrers = await analytics_col.aggregate(referrer_pipeline).to_list(length=10)

    return {
        "period_days": days,
        "total_page_views": total_views,
        "unique_visitors": unique_visitors,
        "daily_views": daily_views,
        "top_pages": top_pages,
        "top_products": top_products,
        "categories": categories,
        "cta_clicks": cta_clicks,
        "devices": devices,
        "referrers": referrers,
        "lead_funnel": {
            "total_leads": total_leads,
            "quote_requests": quote_leads,
            "contact_form": contact_leads,
        },
    }


@router.get("/api/admin/performance")
async def get_performance(
    days: int = 7,
    admin=Depends(get_current_admin),
):
    """API performance metrics for the admin dashboard."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    # Response time by endpoint
    endpoint_pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {
            "_id": "$endpoint",
            "avg_ms": {"$avg": "$response_time_ms"},
            "max_ms": {"$max": "$response_time_ms"},
            "min_ms": {"$min": "$response_time_ms"},
            "count": {"$sum": 1},
            "errors": {"$sum": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 20},
        {"$project": {"_id": 0, "endpoint": "$_id", "avg_ms": {"$round": ["$avg_ms", 1]}, "max_ms": 1, "min_ms": 1, "count": 1, "errors": 1}},
    ]
    endpoints = await perf_col.aggregate(endpoint_pipeline).to_list(length=20)

    # Hourly response times (last 24h)
    hourly_since = now - timedelta(hours=24)
    hourly_pipeline = [
        {"$match": {"ts": {"$gte": hourly_since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$ts"}},
            "avg_ms": {"$avg": "$response_time_ms"},
            "requests": {"$sum": 1},
            "errors": {"$sum": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "hour": "$_id", "avg_ms": {"$round": ["$avg_ms", 1]}, "requests": 1, "errors": 1}},
    ]
    hourly = await perf_col.aggregate(hourly_pipeline).to_list(length=48)

    # Status code distribution
    status_pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {
            "_id": {"$concat": [{"$toString": {"$multiply": [{"$floor": {"$divide": ["$status_code", 100]}}, 100]}}, "s"]},
            "count": {"$sum": 1},
        }},
        {"$project": {"_id": 0, "status_group": "$_id", "count": 1}},
        {"$sort": {"status_group": 1}},
    ]
    status_codes = await perf_col.aggregate(status_pipeline).to_list(length=10)

    # Overall stats
    total_requests = await perf_col.count_documents({"ts": {"$gte": since}})
    error_count = await perf_col.count_documents({"ts": {"$gte": since}, "status_code": {"$gte": 400}})
    avg_pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {"_id": None, "avg": {"$avg": "$response_time_ms"}, "p95": {"$percentile": {"input": "$response_time_ms", "p": [0.95], "method": "approximate"}}}},
    ]
    avg_result = await perf_col.aggregate(avg_pipeline).to_list(length=1)
    avg_response = round(avg_result[0]["avg"], 1) if avg_result else 0
    p95_response = round(avg_result[0]["p95"][0], 1) if avg_result and avg_result[0].get("p95") else 0

    # Slowest endpoints
    slow_pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {
            "_id": "$endpoint",
            "avg_ms": {"$avg": "$response_time_ms"},
            "count": {"$sum": 1},
        }},
        {"$match": {"count": {"$gte": 3}}},
        {"$sort": {"avg_ms": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "endpoint": "$_id", "avg_ms": {"$round": ["$avg_ms", 1]}, "count": 1}},
    ]
    slowest = await perf_col.aggregate(slow_pipeline).to_list(length=5)

    return {
        "period_days": days,
        "total_requests": total_requests,
        "error_count": error_count,
        "error_rate": round(error_count / max(total_requests, 1) * 100, 2),
        "avg_response_ms": avg_response,
        "p95_response_ms": p95_response,
        "endpoints": endpoints,
        "hourly": hourly,
        "status_codes": status_codes,
        "slowest_endpoints": slowest,
    }
