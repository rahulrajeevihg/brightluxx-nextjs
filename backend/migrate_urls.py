"""
Replace all files.ihgbrands.com URLs with recovered/Emergent URLs
in both the frontend codebase and MongoDB database.
"""
import json
import os
import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

REPLACEMENTS = json.load(open("/tmp/url_replacements.json"))
FRONTEND_DIR = "/app/frontend/src"
BACKEND_DIR = "/app/backend"


def replace_in_file(filepath: str, dry_run=False) -> int:
    """Replace ihgbrands URLs in a single file. Returns count of replacements."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    original = content
    count = 0
    for old_url, new_url in REPLACEMENTS.items():
        if old_url in content:
            content = content.replace(old_url, new_url)
            count += content.count(new_url) - original.count(new_url)
            count = max(count, 1)

    if content != original and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return count if content != original else 0


def replace_in_codebase():
    """Replace in all JS/JSX/JSON files."""
    total = 0
    files_changed = 0

    for root, dirs, files in os.walk(FRONTEND_DIR):
        # Skip node_modules and build
        dirs[:] = [d for d in dirs if d not in ("node_modules", "build", ".git")]
        for f in files:
            if f.endswith((".js", ".jsx", ".ts", ".tsx", ".json", ".css")):
                filepath = os.path.join(root, f)
                count = replace_in_file(filepath)
                if count:
                    total += count
                    files_changed += 1
                    print(f"  {filepath}: {count} replacements")

    # Also check backend files
    for root, dirs, files in os.walk(BACKEND_DIR):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "tests")]
        for f in files:
            if f.endswith((".py", ".json")):
                filepath = os.path.join(root, f)
                count = replace_in_file(filepath)
                if count:
                    total += count
                    files_changed += 1
                    print(f"  {filepath}: {count} replacements")

    return files_changed, total


async def replace_in_database():
    """Replace URLs in all MongoDB collections."""
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    total_docs = 0
    total_replacements = 0

    for col_name in await db.list_collection_names():
        col = db[col_name]
        docs_updated = 0

        async for doc in col.find({}):
            doc_str = json.dumps(doc, default=str)
            new_str = doc_str

            for old_url, new_url in REPLACEMENTS.items():
                if old_url in new_str:
                    new_str = new_str.replace(old_url, new_url)

            if new_str != doc_str:
                # Parse back and update
                try:
                    new_doc = json.loads(new_str)
                    # Remove _id from update
                    doc_id = doc["_id"]
                    new_doc.pop("_id", None)
                    await col.replace_one({"_id": doc_id}, new_doc)
                    docs_updated += 1
                    total_replacements += 1
                except Exception as e:
                    print(f"  Error updating doc in {col_name}: {e}")

        if docs_updated:
            print(f"  {col_name}: {docs_updated} documents updated")
            total_docs += docs_updated

    client.close()
    return total_docs, total_replacements


async def main():
    print("=== Step 1: Replacing in codebase ===")
    files_changed, code_replacements = replace_in_codebase()
    print(f"Files changed: {files_changed}, Total replacements: {code_replacements}")

    print("\n=== Step 2: Replacing in database ===")
    docs_updated, db_replacements = await replace_in_database()
    print(f"Documents updated: {docs_updated}, Total replacements: {db_replacements}")

    print("\n=== Summary ===")
    print(f"Code: {files_changed} files, {code_replacements} replacements")
    print(f"Database: {docs_updated} documents updated")
    print(f"Total URLs migrated: {len(REPLACEMENTS)}")

    # Verify no ihgbrands URLs remain
    print("\n=== Verification ===")
    remaining_code = 0
    for root, dirs, files in os.walk(FRONTEND_DIR):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "build", ".git")]
        for f in files:
            if f.endswith((".js", ".jsx")):
                with open(os.path.join(root, f), "r", errors="ignore") as fh:
                    content = fh.read()
                    matches = re.findall(r"files\.ihgbrands\.com", content)
                    if matches:
                        remaining_code += len(matches)
                        print(f"  REMAINING in {os.path.join(root, f)}: {len(matches)}")

    if remaining_code == 0:
        print("  Code: CLEAN - No ihgbrands URLs remaining!")
    else:
        print(f"  Code: {remaining_code} ihgbrands references remaining")


if __name__ == "__main__":
    asyncio.run(main())
