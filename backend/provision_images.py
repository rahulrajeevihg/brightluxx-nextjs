"""
Download REAL images from brightluxx.com WordPress media library.
Map each project, product, solution, and inspiration to unique real images.
"""
import asyncio, os, io, uuid, requests
from pathlib import Path
from PIL import Image as PILImage
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
db = client[os.getenv("DB_NAME")]
UPLOAD_DIR = Path("/app/frontend/public/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def dl(url, slug):
    """Download, optimize to WebP, return local path."""
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        img = PILImage.open(io.BytesIO(r.content))
        img = img.convert("RGBA") if img.mode in ("RGBA","P") else img.convert("RGB")
        if img.width > 1200:
            ratio = 1200 / img.width
            img = img.resize((1200, int(img.height * ratio)), PILImage.LANCZOS)
        out = UPLOAD_DIR / f"{slug}.webp"
        img.save(str(out), "WEBP", quality=82, method=4)
        print(f"  OK {slug} ({os.path.getsize(out)//1024}KB)")
        return f"/uploads/{slug}.webp"
    except Exception as e:
        print(f"  FAIL {slug}: {e}")
        return ""

# ── PROJECTS: real brightluxx.com project photos ──
PROJECT_IMAGES = {
    "Nesto Hypermarket": ("proj_nesto", "https://brightluxx.com/wp-content/uploads/2022/05/Nesto-Hypermarket.jpg"),
    "MICROVISION INTERIORS": ("proj_microvision", "https://brightluxx.com/wp-content/uploads/2022/05/P5-LED-Screen-at-MICROVISION-INTERIORS-LLC-1.jpg"),
    "N W Z West Zone Mall": ("proj_westzone", "https://brightluxx.com/wp-content/uploads/2022/05/P10-LED-Screen-Outdoor-at-N-W-Z-WEST-ZONE-MALL-1.jpg"),
    "Indian Pavilion": ("proj_expo2020", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Screen-at-Indian-Pavillion-Expo-2020.jpg"),
    "Dubai World Trade Centre": ("proj_dwtc", "https://brightluxx.com/wp-content/uploads/2022/05/Exhibition-3.jpg"),
    "MEB": ("proj_meb", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-P2.5-320x160mm-HD-LED-Video-Screen-Module-For-Meeting-room-Show.jpg"),
    "FNAC": ("proj_fnac_airport", "https://brightluxx.com/wp-content/uploads/2022/05/FNAC-Fujairah-Airport.jpg"),
    "Division Nine": ("proj_div9", "https://brightluxx.com/wp-content/uploads/2022/05/I2D-INTERIORS-KIJORA.jpg"),
    "Infinity": ("proj_infinity", "https://brightluxx.com/wp-content/uploads/2022/05/Infinity-Cafe.jpg"),
    "I2D Interiors": ("proj_i2d", "https://brightluxx.com/wp-content/uploads/2022/05/I2D-INTERIORS-KIJORA.jpg"),
    "Al Mutakamela": ("proj_mutakamela", "https://brightluxx.com/wp-content/uploads/2022/05/Al-Mutakamela-Vehicle-TestingAlQouz-2.jpg"),
    "Sharaf Exchange": ("proj_sharaf", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg"),
    "Top Rock": ("proj_jehangir", "https://brightluxx.com/wp-content/uploads/2022/05/Jehangirs-Restaurant-Al-Mankhool-Dubai.jpg"),
    "Fine Mart": ("proj_finemart", "https://brightluxx.com/wp-content/uploads/2022/05/finemart.jpg"),
    "Cosmomed": ("proj_cosmomed", "https://brightluxx.com/wp-content/uploads/2022/05/FNAC-Cosmomed.jpg"),
    "Planer First": ("proj_planer", "https://brightluxx.com/wp-content/uploads/2022/05/Planet-first.jpg"),
    "Ahmed Al Maghribi": ("proj_maghribi", "https://brightluxx.com/wp-content/uploads/2022/05/Ahmed-al-maghribi.jpg"),
    "Sulthan Gold": ("proj_sulthan1", "https://brightluxx.com/wp-content/uploads/2022/05/sulthan-gold.jpg"),
    "Jawhara": ("proj_jawhara", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-Shop-Signage-4.jpg"),
    "Oud Majed": ("proj_oud", "https://brightluxx.com/wp-content/uploads/2022/05/INDOOR-SHOP-SIGNAGE-3.jpg"),
    "Shater": ("proj_shater", "https://brightluxx.com/wp-content/uploads/2022/05/Shater-restaurantAl-Nahda-Sharjah.jpg"),
    "Sulthanate": ("proj_sulthanate", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-1-1.jpg"),
    "Bur Dubai": ("proj_sulthan2", "https://brightluxx.com/wp-content/uploads/2022/05/sulthan-gold-deira.jpg"),
    "LED World LLC (Khorfakan)": ("proj_ledworld_kf", "https://brightluxx.com/wp-content/uploads/2022/06/Untitled-4.jpg"),
    "LED World LLC (Ajman)": ("proj_ledworld_aj", "https://brightluxx.com/wp-content/uploads/2022/05/LED-World-Ajman.jpg"),
}

# ── PRODUCTS: real brightluxx.com module photos (unique per product) ──
PRODUCT_IMAGES = {
    "BL-ISF156": ("prod_isf156", "https://brightluxx.com/wp-content/uploads/2022/05/P1.5-Indoor-soft-flexible-LED-Display-module-for-round-custom-shapes-led-video-wall1-1.jpg"),
    "BL-IP3": ("prod_ip3", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-P3-1-32Scan-64x64dot-192X192mm-LED-Screen-Video-Module1.jpg"),
    "BL-IP307": ("prod_ip307", "https://brightluxx.com/wp-content/uploads/2022/05/P3.076-320x160mm-Indoor-HD-LED-Video-Screen-Module1.jpg"),
    "BL-CRC400": ("prod_crc400", "https://brightluxx.com/wp-content/uploads/2022/05/P4-Indoor-Circular-Round-LED-Display-Module-Screen1.jpg"),
    "BL-OR391": ("prod_or391", "https://brightluxx.com/wp-content/uploads/2022/05/P3.91-Outdoor-SMD-Full-Color-LED-Display-Module1.jpg"),
    "BL-OP4HD": ("prod_op4hd", "https://brightluxx.com/wp-content/uploads/2022/05/P4-Outdoor-HD-LED-Display-Screen-Module-256x128mm-for-advertising1.jpg"),
    "BL-OP5SMD": ("prod_op5smd", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-P5-320x160mm-SMD-LED-Screen-Module-High-Brightness-And-Resolution1.jpg"),
    "BL-OP667": ("prod_op667", "https://brightluxx.com/wp-content/uploads/2022/05/P6.67-mm-Outdoor-Nationstar-SMD-LED-display-screen-Module-320x160mm-IP671.jpg"),
    "BL-SF150": ("prod_sf150", "https://brightluxx.com/wp-content/uploads/2022/05/P1.5-Indoor-soft-flexible-LED-Display-module-for-round-custom-shapes-led-video-wall1.jpg"),
    "BL-SF400": ("prod_sf400", "https://brightluxx.com/wp-content/uploads/2022/05/P4-Indoor-soft-flexible-LED-Display-module-For-Creative-Led-Screen1.jpg"),
    "BL-IP18": ("prod_ip18", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-P2.5-320x160mm-HD-LED-Video-Screen-Module-For-Meeting-room-Show1.jpg"),
    "BL-RSL250": ("prod_rsl250", "https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display.jpg"),
    "BL-RSL400": ("prod_rsl400", "https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display-2.jpg"),
    "BL-FLR391": ("prod_flr391", "https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display.jpg"),
    "BL-CLR120": ("prod_clr120", "https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display.jpg"),
}

# ── PRODUCT CATEGORIES: for older products that need real category images ──
CATEGORY_IMAGES = {
    "indoor": ("cat_indoor", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-3.jpg"),
    "outdoor": ("cat_outdoor", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-SMD-LED-Display-1.jpg"),
    "flexible": ("cat_flexible", "https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display.jpg"),
    "transparent": ("cat_transparent", "https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-2.jpg"),
    "rental": ("cat_rental", "https://brightluxx.com/wp-content/uploads/2022/05/Die-Cast-Rental-LED-Display.jpg"),
    "sphere": ("cat_sphere", "https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display.jpg"),
    "road-signal": ("cat_roadsignal", "https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display-1.jpg"),
    "interactive": ("cat_floor", "https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-2.jpg"),
    "poster": ("cat_poster", "https://brightluxx.com/wp-content/uploads/2022/05/Poster-LED-Display.jpg"),
    "cob-microled": ("cat_cobmicro", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display_02.jpg"),
    "virtual-production": ("cat_vp", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display.jpg"),
    "all-in-one": ("cat_allinone", "https://brightluxx.com/wp-content/uploads/2022/05/Conference-Hall-4.jpg"),
    "dvled": ("cat_dvled", "https://brightluxx.com/wp-content/uploads/2022/05/Home-Cinema-1.jpg"),
    "mip": ("cat_mip", "https://brightluxx.com/wp-content/uploads/2022/05/pixel1-1.jpg"),
    "cinema": ("cat_cinema", "https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA1.jpg"),
    "fine-pitch": ("cat_finepitch", "https://brightluxx.com/wp-content/uploads/2022/05/Meeting-Room-4.jpg"),
    "naked-eye-3d": ("cat_3d", "https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display-2.jpg"),
    "sky-screen": ("cat_sky", "https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE-2.jpg"),
    "shelf-edge": ("cat_shelf", "https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display.jpg"),
    "conference": ("cat_conf", "https://brightluxx.com/wp-content/uploads/2022/05/CONFERENCE-HALL.jpg"),
}

# ── SOLUTIONS: unique images per solution ──
SOLUTION_IMAGES = {
    "retail": ("sol_retail", "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-Shop-Signage-4.jpg"),
    "corporate": ("sol_corporate", "https://brightluxx.com/wp-content/uploads/2022/05/Conference-Hall-4.jpg"),
    "outdoor": ("sol_outdoor", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg"),
    "events": ("sol_events", "https://brightluxx.com/wp-content/uploads/2022/05/Exhibition-3.jpg"),
    "creative": ("sol_creative", "https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display-2.jpg"),
    "traffic": ("sol_traffic", "https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display-1.jpg"),
    "immersive": ("sol_immersive", "https://brightluxx.com/wp-content/uploads/2022/05/Home-Cinema-1.jpg"),
    "transparent": ("sol_transparent", "https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-2.jpg"),
}

# ── INSPIRATIONS: real LED application photos from brightluxx ──
INSPIRATION_IMAGES = [
    ("insp_sports_lounge", "https://brightluxx.com/wp-content/uploads/2022/05/Sports-Lounge-1.jpg"),
    ("insp_road_adv", "https://brightluxx.com/wp-content/uploads/2022/05/road-advertising-1.jpg"),
    ("insp_pavement", "https://brightluxx.com/wp-content/uploads/2022/05/Pavement-Advertising-1.jpg"),
    ("insp_outdoor_sign1", "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-1-1.jpg"),
    ("insp_outdoor_sign2", "https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE-2.jpg"),
    ("insp_meeting", "https://brightluxx.com/wp-content/uploads/2022/05/Meeting-Room-4.jpg"),
    ("insp_indoor_sign", "https://brightluxx.com/wp-content/uploads/2022/05/INDOOR-SHOP-SIGNAGE-3.jpg"),
    ("insp_cinema", "https://brightluxx.com/wp-content/uploads/2022/05/Home-Cinema-1.jpg"),
    ("insp_exhibition", "https://brightluxx.com/wp-content/uploads/2022/05/Exhibition-3.jpg"),
    ("insp_education", "https://brightluxx.com/wp-content/uploads/2022/05/Education-1.jpg"),
    ("insp_conference", "https://brightluxx.com/wp-content/uploads/2022/05/Conference-Hall-4.jpg"),
    ("insp_outdoor_led1", "https://brightluxx.com/wp-content/uploads/2022/04/OUTDOOR-LED-SOLUTIONS.jpg"),
    ("insp_digital_banner", "https://brightluxx.com/wp-content/uploads/2022/04/DIGITAL-BANNERS.jpg"),
    ("insp_poster_display", "https://brightluxx.com/wp-content/uploads/2022/04/Led-Poster-Displays.jpg"),
    ("insp_indoor_screen", "https://brightluxx.com/wp-content/uploads/2022/04/Indoor-LED-Screens.jpg"),
    ("insp_pixel_wall", "https://brightluxx.com/wp-content/uploads/2022/05/pixel1-1.jpg"),
    ("insp_curtain", "https://brightluxx.com/wp-content/uploads/2022/05/Curtain-LED-Display.jpg"),
    ("insp_perimeter", "https://brightluxx.com/wp-content/uploads/2022/05/Perimeter-LED-Display.jpg"),
    ("insp_shelf", "https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display.jpg"),
    ("insp_floor_led", "https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-2.jpg"),
    ("insp_sphere", "https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display-2.jpg"),
    ("insp_range_pixel", "https://brightluxx.com/wp-content/uploads/2022/05/range-of-pixel-pitches-1.jpg"),
]


async def main():
    # Clean old AI/stock images
    for f in UPLOAD_DIR.glob("*.webp"):
        f.unlink()
    for f in UPLOAD_DIR.glob("*.png"):
        if "test" not in f.name:
            f.unlink()
    for f in UPLOAD_DIR.glob("*.jpg"):
        if "test" not in f.name:
            f.unlink()
    print("Cleaned old images\n")

    # 1. Download project images
    print("=== PROJECTS ===")
    proj_urls = {}
    for key, (slug, url) in PROJECT_IMAGES.items():
        local = dl(url, slug)
        if local:
            proj_urls[key] = local

    # 2. Download product-specific images
    print("\n=== PRODUCTS (specific) ===")
    prod_urls = {}
    for code, (slug, url) in PRODUCT_IMAGES.items():
        local = dl(url, slug)
        if local:
            prod_urls[code] = local

    # 3. Download category fallback images
    print("\n=== CATEGORIES (fallback) ===")
    cat_urls = {}
    for cat, (slug, url) in CATEGORY_IMAGES.items():
        local = dl(url, slug)
        if local:
            cat_urls[cat] = local

    # 4. Download solution images
    print("\n=== SOLUTIONS ===")
    sol_urls = {}
    for sol_id, (slug, url) in SOLUTION_IMAGES.items():
        local = dl(url, slug)
        if local:
            sol_urls[sol_id] = local

    # 5. Download inspiration images
    print("\n=== INSPIRATIONS ===")
    insp_urls = []
    for slug, url in INSPIRATION_IMAGES:
        local = dl(url, slug)
        if local:
            insp_urls.append(local)

    # ── UPDATE DATABASE ──
    print("\n=== Updating Projects ===")
    updated = 0
    async for p in db.projects.find():
        title = p.get("title", "")
        matched = None
        for key, url in proj_urls.items():
            if key.lower() in title.lower():
                matched = url
                break
        if matched:
            await db.projects.update_one({"_id": p["_id"]}, {"$set": {"image_url": matched}})
            updated += 1
    print(f"  Updated {updated} projects")

    print("\n=== Updating Products ===")
    updated = 0
    async for p in db.products.find():
        code = p.get("product_code", "")
        cat = p.get("category", "")
        if code in prod_urls:
            url = prod_urls[code]
        elif cat in cat_urls:
            url = cat_urls[cat]
        else:
            url = cat_urls.get("indoor", "")
        if url:
            await db.products.update_one({"_id": p["_id"]}, {"$set": {"image_url": url}})
            updated += 1
    print(f"  Updated {updated} products")

    print("\n=== Updating Inspirations ===")
    updated = 0
    idx = 0
    async for i in db.inspirations.find():
        if idx < len(insp_urls):
            await db.inspirations.update_one({"_id": i["_id"]}, {"$set": {"image_url": insp_urls[idx]}})
            idx += 1
            updated += 1
    print(f"  Updated {updated} inspirations")

    # Store solution images for frontend use
    import json
    with open("/app/frontend/src/data/solution_images.json", "w") as f:
        json.dump(sol_urls, f, indent=2)
    print(f"\n  Solution images saved to solution_images.json")

    # Summary
    webp_files = list(UPLOAD_DIR.glob("*.webp"))
    total_size = sum(f.stat().st_size for f in webp_files)
    print(f"\n=== SUMMARY ===")
    print(f"  Total WebP files: {len(webp_files)}")
    print(f"  Total size: {total_size//1024} KB")
    print(f"  All unique filenames: {len(set(f.name for f in webp_files))}")

asyncio.run(main())
