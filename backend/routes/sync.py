"""
Admin data sync endpoint — allows force-syncing content from seed_data.json.
Used to update deployed environments with latest preview data.
"""
import json
import os
from fastapi import APIRouter, Depends
from database import db
from auth import get_current_admin

router = APIRouter()

SEED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed_data.json")

CONTENT_COLLECTIONS = [
    "homepage_content",
    "products",
    "product_families",
    "blogs",
    "case_studies",
    "inspirations",
    "projects",
    "resources",
    "solutions",
    "site_settings",
    "applications_content",
    "technologies_content",
    "taxonomy",
    "pixelvue_products",
]


@router.post("/api/admin/sync-from-seed")
async def sync_from_seed(admin=Depends(get_current_admin)):
    """Force-sync all content collections from seed_data.json."""
    if not os.path.exists(SEED_FILE):
        return {"success": False, "error": "seed_data.json not found"}

    with open(SEED_FILE, "r") as f:
        seed = json.load(f)

    results = {}
    for coll_name in CONTENT_COLLECTIONS:
        docs = seed.get(coll_name, [])
        if not docs:
            results[coll_name] = "skipped (no seed data)"
            continue

        await db[coll_name].delete_many({})
        await db[coll_name].insert_many(docs)
        results[coll_name] = f"replaced with {len(docs)} docs"

    return {"success": True, "synced": results}
