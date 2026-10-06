from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

products_col = db["products"]
inspirations_col = db["inspirations"]
projects_col = db["projects"]
leads_col = db["leads"]
admins_col = db["admins"]
analytics_col = db["analytics_events"]
perf_col = db["performance_metrics"]


def id_query(id_value):
    """Build an _id filter that matches whether the stored _id is a string or an ObjectId.

    The CMS content collections (product_families, solutions, technologies_content,
    applications_content, pixelvue_products) were seeded with string _id values, while
    documents created via the admin API get real ObjectId _ids. Matching both keeps
    toggle/update/delete working for every record regardless of how it was created.
    """
    ids = [id_value]
    try:
        oid = ObjectId(str(id_value))
        if oid not in ids:
            ids.append(oid)
    except Exception:
        pass
    return {"_id": {"$in": ids}}
