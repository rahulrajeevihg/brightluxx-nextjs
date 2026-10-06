"""Update product images for products missing image_url."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# Map product names to Unsplash/Pexels image URLs
IMAGE_MAP = {
    "NovaStar MCTRL4K Controller": "https://images.unsplash.com/photo-1672689956124-18666b4cdae4?w=600&q=80",
    "Colorlight Z6 Media Server": "https://images.unsplash.com/photo-1672689956124-18666b4cdae4?w=600&q=80",
    "LED Power Supply Unit 200W": "https://images.unsplash.com/photo-1672689956124-18666b4cdae4?w=600&q=80",
    "Mounting Bracket Kit — Wall Mount": "https://images.pexels.com/photos/35871024/pexels-photo-35871024.jpeg?auto=compress&w=600",
    "Round LED Display P2.5": "https://images.unsplash.com/photo-1653398615155-aecb61350afc?w=600&q=80",
    "Cube LED Display P3": "https://images.unsplash.com/photo-1653398615155-aecb61350afc?w=600&q=80",
    "Cone LED Display P4": "https://images.unsplash.com/photo-1653398615155-aecb61350afc?w=600&q=80",
    "Digital Signage Pro 55\" 4K": "https://images.unsplash.com/photo-1764795849694-34b3316b3de4?w=600&q=80",
    "Digital Signage Outdoor 75\" IP65": "https://images.unsplash.com/photo-1690964099658-b619682704ce?w=600&q=80",
    "Digital Kiosk Interactive 43\"": "https://images.unsplash.com/photo-1764795849694-34b3316b3de4?w=600&q=80",
    "Commercial Smart TV 85\" 4K": "https://images.unsplash.com/photo-1740968984962-29087e16ceff?w=600&q=80",
    "Outdoor Smart TV 65\" IP55": "https://images.unsplash.com/photo-1762417582231-d4861d804c17?w=600&q=80",
    "Plug & Play Video Wall 2x2 P1.5": "https://images.unsplash.com/photo-1646215993365-125e6428e1dc?w=600&q=80",
    "Portable LED Stand P2.5": "https://images.unsplash.com/photo-1745237850595-2991cd361fa1?w=600&q=80",
    "Meeting Room LED All-in-One 136\"": "https://images.unsplash.com/photo-1709000724284-c38463263d59?w=600&q=80",
}

async def update_images():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["products"]

    updated = 0
    for name, url in IMAGE_MAP.items():
        result = await col.update_one(
            {"name": name, "$or": [{"image_url": {"$exists": False}}, {"image_url": ""}, {"image_url": None}]},
            {"$set": {"image_url": url}}
        )
        if result.modified_count > 0:
            updated += 1
            print(f"  Updated: {name}")
        else:
            print(f"  Skipped (already has image): {name}")

    print(f"\nTotal updated: {updated}")
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())
