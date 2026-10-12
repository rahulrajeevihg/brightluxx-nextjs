import asyncio, os, re, json
from collections import Counter
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "brightluxx")

PATTERNS = {
    "P1_objstore": re.compile(r"integrations\.emergentagent\.com/objstore"),
    "P2_static_prod": re.compile(r"static\.prod-images\.emergentagent\.com"),
    "P3_customer_assets": re.compile(r"customer-assets[-\w]*\.emergentagent\.net"),
    "P4_api_media": re.compile(r"/api/media/"),
    "P5_api_cdn": re.compile(r"/api/cdn/"),
    "P5_recovered": re.compile(r"/recovered/"),
    "any_emergent": re.compile(r"emergentagent\.(com|net)"),
    "ihg_cdn": re.compile(r"files\.ihgbrands\.com"),
}

def walk(v, cb, path=""):
    if isinstance(v, str):
        cb(v, path)
    elif isinstance(v, dict):
        for k, vv in v.items():
            walk(vv, cb, f"{path}.{k}")
    elif isinstance(v, list):
        for i, vv in enumerate(v):
            walk(vv, cb, f"{path}[]")

async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    names = await db.list_collection_names()
    pattern_counts = Counter()
    field_hits = Counter()  # (collection, pattern) -> count
    ihg_samples = set()
    for cn in sorted(names):
        cursor = db[cn].find({})
        async for doc in cursor:
            def cb(s, path, _cn=cn):
                for pname, pat in PATTERNS.items():
                    if pat.search(s):
                        pattern_counts[pname] += 1
                        field_hits[(_cn, path, pname)] += 1
                        if pname == "ihg_cdn" and len(ihg_samples) < 60:
                            ihg_samples.add(s if len(s) < 200 else s[:200])
            walk(doc, cb)
    print("=== PATTERN TOTALS (string-value occurrences across all collections) ===")
    for p, c in pattern_counts.most_common():
        print(f"  {p}: {c}")
    print("\n=== FIELD-LEVEL HITS for migration-relevant patterns (P1-P5, any_emergent) ===")
    rel = {"P1_objstore","P2_static_prod","P3_customer_assets","P4_api_media","P5_api_cdn","P5_recovered","any_emergent"}
    for (cn, path, pname), c in sorted(field_hits.items()):
        if pname in rel:
            print(f"  [{cn}] field='{path}' {pname} x{c}")
    print(f"\n=== SAMPLE files.ihgbrands.com URLs in DB (for HEAD verification), {len(ihg_samples)} unique ===")
    for s in list(ihg_samples)[:30]:
        print("  ", s)
    # write samples to file
    with open("/app/migration/ihg_url_samples.txt","w") as f:
        for s in sorted(ihg_samples):
            f.write(s+"\n")
    client.close()

asyncio.run(main())
