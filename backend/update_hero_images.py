"""
Update PixelVue products with generated hero images
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Map of slug to hero image URL
HERO_IMAGES = {
    "ultra-flip": "https://files.ihgbrands.com/emergent-images/c1b7502756769bf9daf11872065d28e36ef306db7dfcc7c8ab3d7d87be572dcd.png",
    "digi-standee": "https://files.ihgbrands.com/emergent-images/ef7f013daafe0ad3c478b20c96066e99a89c9f51c9b8cc82f2ed0d33c7c7b6c3.png",
    "ooh-poster": "https://files.ihgbrands.com/emergent-images/cc89ef2cdbfd77939eaf1644f7062af27b054cc7b6a7cbb54d84f6538342e528.png",
    "eagle-wing": "https://files.ihgbrands.com/emergent-images/3e4bcf108b3e615ffe78596cdd3d8f1aef3120bb5ef65333277fe9bb14695c9a.png",
    "unity": "https://files.ihgbrands.com/emergent-images/6f71666ebd9b962a2b6efb0899b4806e7fc29d1d2fcf0fa1305b2513c9ce21a9.png",
    "videobrick": "https://files.ihgbrands.com/emergent-images/7c8b60f5c974d7c20b6f9f22ae7ec451e77096d815c54c6d979ffa1d2d96c365.png",
    "iconference": "https://files.ihgbrands.com/emergent-images/008a75cc8d4d9f7004cc7abdd79b93c82d982598b9a3ab5b08733c4301ebeb35.png",
    "ezeesign": "https://files.ihgbrands.com/emergent-images/407481e89ac18e4c469af4935ca321239eec36681913566a4bc0fc9d6d25a811.png",
    "ishelf": "https://files.ihgbrands.com/emergent-images/41c41370fc3701d164eb42d1fbdcd2d3d542974997c4b2ed30b4ac9aafe9d111.png",
    "tablevision": "https://files.ihgbrands.com/emergent-images/b879b6aa2042303fa35ccfcb220ceea68fb26424d1147a494ba5071c7928c69f.png",
    "iflex-pro": "https://files.ihgbrands.com/emergent-images/15eb0ec68ed652e854d1fa957e4c28add69c08b9b75e7b7e6fe09aa913cd514e.png",
    "itransformers": "https://files.ihgbrands.com/emergent-images/b57f1a1f0ffc676308c65a8c2d728e868e39fef6152e3465f0b419e12357ddac.png",
    "tetris": "https://files.ihgbrands.com/emergent-images/53b872a7d8ea18497dbc2f2c9d54cee141552f123e279656a8d41954db5e8ed4.png",
    "ellipse-counter": "https://files.ihgbrands.com/emergent-images/a35abb67a5d9c082ff685f5017821147eef564b23d2d413fd7c676ea0ba2cab8.png",
    "creative-shapes": "https://files.ihgbrands.com/emergent-images/efe560b6d8812dcb6fefc2d7c6ea2a24d6110fa2a2e5b24f228b60101988f54b.png",
    "interactive": "https://files.ihgbrands.com/emergent-images/62f734fff1161edd3284954ae61cd4a7a071f605a184024395028ae79c818b45.png",
    "crystalflex": "https://files.ihgbrands.com/emergent-images/747956d8d56634809f709d5be2f071f4d0bcf011730c42110ed0b8bfde2a98d6.png",
    "rolling-floor": "https://files.ihgbrands.com/emergent-images/e2058d730739aff4566608d8343395800689b5b44499802b1f0046fec09629e1.png",
    "magicstage": "https://files.ihgbrands.com/emergent-images/608566c3095f0ec4e4d1d172d9995d78caa1187c0988bd3210445cf0cee3eec3.png",
    "magic-blanket": "https://files.ihgbrands.com/emergent-images/2166b9b91bdf5943d131765d85069cf911c38751df8b077b878c536ef758b570.png",
    "magicsky": "https://files.ihgbrands.com/emergent-images/306ccf6c1a950ca1e50c7b561d35dd61373f7992ac1d6ad30318d3fafacf65af.png",
    "magic-garments": "https://files.ihgbrands.com/emergent-images/929ad368c68dbedb518a3de198726ce2e36e0c98a1d64c7e8ea5e2f748357186.png"
}

async def update_hero_images():
    print("Updating hero images for PixelVue products...")
    
    for slug, image_url in HERO_IMAGES.items():
        result = await db.pixelvue_products.update_one(
            {"slug": slug},
            {"$set": {"hero_image": image_url}}
        )
        if result.modified_count > 0:
            print(f"  ✓ Updated {slug}")
        else:
            print(f"  - {slug} (not found or already set)")
    
    # Verify
    products = await db.pixelvue_products.find({}).to_list(100)
    with_images = [p for p in products if p.get("hero_image")]
    print(f"\nTotal products with hero images: {len(with_images)}/{len(products)}")

if __name__ == "__main__":
    asyncio.run(update_hero_images())
