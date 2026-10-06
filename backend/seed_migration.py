"""
Database seed migration — ensures all content collections have complete, up-to-date data.
Loads from seed_data_full.json (exported from preview with all enrichments).
Uses UPSERT logic: updates existing docs by unique key, inserts missing ones.
Safe to run on every startup — never deletes data, only adds/updates.
"""
import json
import os
from datetime import datetime, timezone

SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_data_full.json")
LEGACY_SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_data.json")

# Unique key field for each collection (used for upsert matching)
COLLECTION_KEYS = {
    "page_seo": "path",
    "products": "slug",
    "blogs": "slug",
    "case_studies": "slug",
    "pixelvue_products": "slug",
    "product_families": "slug",
    "solutions": "slug",
    "inspirations": "slug",
    "applications_content": "slug",
    "technologies_content": "slug",
    "resources": "id",
    "taxonomy": "id",
    "homepage_content": "type",
    "site_settings": "key",
    "reviews": "id",
    "projects": "slug",
}


async def run_seed(db):
    """Seed/sync content collections using upsert from seed_data_full.json."""
    # Prefer comprehensive seed file, fall back to legacy
    seed_file = SEED_FILE if os.path.exists(SEED_FILE) else LEGACY_SEED_FILE
    if not os.path.exists(seed_file):
        print("Seed: no seed file found, skipping")
        return

    with open(seed_file, "r") as f:
        seed = json.load(f)

    stats = {"inserted": 0, "updated": 0, "skipped": 0, "collections": 0}

    for coll_name, docs in seed.items():
        if not docs:
            continue

        key_field = COLLECTION_KEYS.get(coll_name)
        if not key_field:
            # Unknown collection — insert only if empty (safe fallback)
            count = await db[coll_name].count_documents({})
            if count == 0:
                await db[coll_name].insert_many(docs)
                stats["inserted"] += len(docs)
            continue

        col = db[coll_name]
        col_inserted = 0
        col_updated = 0

        for doc in docs:
            # Remove _id to avoid ObjectId conflicts between environments
            doc.pop("_id", None)

            key_value = doc.get(key_field)
            if not key_value:
                # No key — insert if no duplicate exists
                await col.insert_one(doc)
                col_inserted += 1
                continue

            # Upsert: update if exists, insert if not
            existing = await col.find_one({key_field: key_value})
            if existing:
                # Update existing doc — preserve _id, merge new fields
                update_fields = {}
                for k, v in doc.items():
                    if k == key_field:
                        continue
                    # Only update if the seed has meaningful data
                    # Don't overwrite with empty/None if existing has data
                    if v is not None and v != "" and v != []:
                        update_fields[k] = v
                    elif not existing.get(k):
                        update_fields[k] = v

                if update_fields:
                    await col.update_one(
                        {key_field: key_value},
                        {"$set": update_fields}
                    )
                    col_updated += 1
                else:
                    stats["skipped"] += 1
            else:
                # Insert new doc
                await col.insert_one(doc)
                col_inserted += 1

        if col_inserted > 0 or col_updated > 0:
            stats["collections"] += 1
            stats["inserted"] += col_inserted
            stats["updated"] += col_updated
            print(f"  Seed: {coll_name} — {col_inserted} inserted, {col_updated} updated")

    total = stats["inserted"] + stats["updated"]
    if total > 0:
        print(f"Seed: Synced {total} docs across {stats['collections']} collections ({stats['inserted']} new, {stats['updated']} updated)")
    else:
        print("Seed: All content up to date, no changes needed")

