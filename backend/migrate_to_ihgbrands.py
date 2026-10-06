"""
Migrate all media URLs to files.ihgbrands.com CDN.
Replaces:
  1. /recovered/xxx → https://files.ihgbrands.com/xxx
  2. static.prod-images.emergentagent.com/jobs/.../hash.png → https://files.ihgbrands.com/emergent-images/hash.png
"""
import json
import os
import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

CDN_BASE = "https://files.ihgbrands.com"
FRONTEND_DIR = "/app/frontend/src"
BACKEND_DIR = "/app/backend"


def build_replacements():
    """Build the complete replacement map."""
    replacements = {}

    # 1. /recovered/xxx → CDN/xxx
    recovered_dir = "/app/frontend/public/recovered"
    for filename in os.listdir(recovered_dir):
        old_path = f"/recovered/{filename}"
        new_url = f"{CDN_BASE}/{filename}"
        replacements[old_path] = new_url

    # 2. Emergent static URLs → CDN/emergent-images/hash.ext
    with open("/tmp/emergent_urls.txt") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            filename = os.path.basename(url)
            new_url = f"{CDN_BASE}/emergent-images/{filename}"
            replacements[url] = new_url

    return replacements


def replace_in_file(filepath, replacements):
    """Replace URLs in a single file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def replace_in_codebase(replacements):
    """Replace in all source files."""
    total = 0
    for base_dir in [FRONTEND_DIR, BACKEND_DIR]:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "build", ".git", "__pycache__")]
            for f in files:
                if f.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".py")):
                    filepath = os.path.join(root, f)
                    if replace_in_file(filepath, replacements):
                        total += 1
                        print(f"  Updated: {filepath}")
    return total


async def replace_in_database(replacements):
    """Replace URLs in MongoDB."""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    total = 0

    for col_name in await db.list_collection_names():
        col = db[col_name]
        async for doc in col.find({}):
            doc_str = json.dumps(doc, default=str)
            new_str = doc_str
            for old, new in replacements.items():
                new_str = new_str.replace(old, new)

            if new_str != doc_str:
                try:
                    new_doc = json.loads(new_str)
                    doc_id = doc["_id"]
                    new_doc.pop("_id", None)
                    await col.replace_one({"_id": doc_id}, new_doc)
                    total += 1
                except Exception as e:
                    print(f"  Error: {col_name}: {e}")

    client.close()
    return total


async def main():
    print("Building replacement map...")
    replacements = build_replacements()
    print(f"Total replacements: {len(replacements)}")

    print("\n=== Updating code ===")
    files_changed = replace_in_codebase(replacements)
    print(f"Files updated: {files_changed}")

    print("\n=== Updating database ===")
    docs_updated = await replace_in_database(replacements)
    print(f"Documents updated: {docs_updated}")

    print("\n=== Verification ===")
    # Check for any remaining /recovered/ or emergent URLs
    for root, dirs, files in os.walk(FRONTEND_DIR):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "build", ".git")]
        for f in files:
            if f.endswith((".js", ".jsx")):
                with open(os.path.join(root, f), "r", errors="ignore") as fh:
                    content = fh.read()
                    if "/recovered/" in content:
                        print(f"  REMAINING /recovered/ in {os.path.join(root, f)}")
                    if "static.prod-images.emergentagent.com" in content:
                        count = content.count("static.prod-images.emergentagent.com")
                        print(f"  REMAINING emergent static in {os.path.join(root, f)}: {count}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
