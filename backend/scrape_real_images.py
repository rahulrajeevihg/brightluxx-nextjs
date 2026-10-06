"""
Download real images from brightluxx.com WordPress media library
and update MongoDB records with authentic product/project/inspiration photos.
"""
import asyncio
import os
import re
import requests
from io import BytesIO
from PIL import Image
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
UPLOAD_DIR = "/app/frontend/public/uploads"
WP_API = "https://brightluxx.com/wp-json/wp/v2/media"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# MAPPING: WP image IDs → product categories
# ──────────────────────────────────────────────

# Product category images (from WP media library product photos)
CATEGORY_IMAGE_MAP = {
    "cob-microled": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-3.jpg", "cob_microled_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-2.jpg", "cob_microled_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display_02.jpg", "cob_microled_3.webp"),
    ],
    "mip": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-1.jpg", "mip_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display.jpg", "mip_2.webp"),
    ],
    "transparent": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display.jpg", "transparent_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-1.jpg", "transparent_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-2.jpg", "transparent_3.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Transperent-led-screen.png", "transparent_4.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Curtain-LED-Display.jpg", "transparent_curtain_1.webp"),
    ],
    "flexible": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display.jpg", "flexible_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display-1.jpg", "flexible_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display-2.jpg", "flexible_3.webp"),
    ],
    "interactive": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display.jpg", "interactive_floor_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-1.jpg", "interactive_floor_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-2.jpg", "interactive_floor_3.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display.png", "interactive_floor_4.webp"),
    ],
    "all-in-one": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-3.jpg", "allinone_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Meeting-Room-4.jpg", "allinone_meeting.webp"),
    ],
    "dvled": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Home-Cinema-1.jpg", "dvled_cinema_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA.jpg", "dvled_cinema_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA1.jpg", "dvled_cinema_3.webp"),
    ],
    "outdoor": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-SMD-LED-Display.jpg", "outdoor_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-SMD-LED-Display-1.jpg", "outdoor_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-SMD-LED-Display-2.jpg", "outdoor_3.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-LED-SCREEN-uae.png", "outdoor_uae.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-DIP-LED-Display.jpg", "outdoor_dip_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-DIP-LED-Display-1.jpg", "outdoor_dip_2.webp"),
    ],
    "rental": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Die-Cast-Rental-LED-Display.jpg", "rental_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Die-Cast-Rental-LED-Display-1.jpg", "rental_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Die-Cast-Rental-LED-Display-2.jpg", "rental_3.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/INDOOR-RENTAL-LED-SCREEN.png", "rental_indoor.webp"),
    ],
    "indoor": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-led-screens.png", "indoor_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/Indoor-LED-Screens.jpg", "indoor_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/Indoor-LED-Screens-1.jpg", "indoor_3.webp"),
    ],
    "naked-eye-3d": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg", "naked3d_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE.jpg", "naked3d_2.webp"),
    ],
    "poster-totem": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Poster-LED-Display.jpg", "poster_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Poster-LED-Display-1.jpg", "poster_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Poster-LED-Display-2.jpg", "poster_3.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/Led-Poster-Displays.jpg", "poster_led_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/Led-Poster-Displays-1.jpg", "poster_led_2.webp"),
    ],
    "cinema-led": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA2.jpg", "cinema_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA3.jpg", "cinema_2.webp"),
    ],
    "sphere": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display.jpg", "sphere_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display-1.jpg", "sphere_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display-2.jpg", "sphere_3.webp"),
    ],
    "virtual-production": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-2.jpg", "vp_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/DIGITAL-BANNERS-1.jpg", "vp_stage.webp"),
    ],
    "shelf-edge": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display.jpg", "shelf_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display-1.jpg", "shelf_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display-2.jpg", "shelf_3.webp"),
    ],
    "ceiling-led": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-3.jpg", "ceiling_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/04/Indoor-LED-Screens-1.jpg", "ceiling_2.webp"),
    ],
    "road-signal": [
        ("https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display.jpg", "road_signal_1.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display-1.jpg", "road_signal_2.webp"),
        ("https://brightluxx.com/wp-content/uploads/2022/05/Road-Signal-LED-Display-2.jpg", "road_signal_3.webp"),
    ],
}

# Project images - matched by project title keywords to WP image
PROJECT_IMAGE_MAP = {
    "LED World LLC (Ajman)": "https://brightluxx.com/wp-content/uploads/2022/05/LED-World-Ajman.jpg",
    "Sulthanate": "https://brightluxx.com/wp-content/uploads/2022/05/sulthan-gold.jpg",
    "LED World LLC (Khorfakan)": "https://brightluxx.com/wp-content/uploads/2022/05/LED-World-Ajman.jpg",
    "Oud Majed": "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg",
    "Shater Restaurant": "https://brightluxx.com/wp-content/uploads/2022/05/Shater-restaurantAl-Nahda-Sharjah.jpg",
    "Sulthan Gold": "https://brightluxx.com/wp-content/uploads/2022/05/sulthan-gold-deira.jpg",
    "Sulthan Gold and Diamond": "https://brightluxx.com/wp-content/uploads/2022/05/sulthan-gold.jpg",
    "Jawhara Jewellery": "https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE-1.jpg",
    "Planer First": "https://brightluxx.com/wp-content/uploads/2022/05/Planet-first.jpg",
    "Ahmed Al Maghribi": "https://brightluxx.com/wp-content/uploads/2022/05/Ahmed-al-maghribi.jpg",
    "Fine Mart": "https://brightluxx.com/wp-content/uploads/2022/05/finemart.jpg",
    "FNAC": "https://brightluxx.com/wp-content/uploads/2022/05/FNAC-Cosmomed.jpg",
    "Sharaf Exchange": "https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE-2.jpg",
    "Top Rock": "https://brightluxx.com/wp-content/uploads/2022/05/Jehangirs-Restaurant-Al-Mankhool-Dubai.jpg",
    "Kijora": "https://brightluxx.com/wp-content/uploads/2022/05/I2D-INTERIORS-KIJORA.jpg",
    "Al Mutakamela": "https://brightluxx.com/wp-content/uploads/2022/05/Al-Mutakamela-Vehicle-TestingAlQouz-2.jpg",
    "Division Nine": "https://brightluxx.com/wp-content/uploads/2022/05/P5-LED-Screen-at-MICROVISION-INTERIORS-LLC.jpg",
    "Infinity": "https://brightluxx.com/wp-content/uploads/2022/05/Infinity-Cafe.jpg",
    "FNAC Fujairah": "https://brightluxx.com/wp-content/uploads/2022/05/FNAC-Fujairah-Airport.jpg",
    "Dubai World Trade": "https://brightluxx.com/wp-content/uploads/2022/05/EXHIBITION-2.jpg",
    "Delma Mall": "https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE.jpg",
    "Indian Pavilion": "https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Screen-at-Indian-Pavillion-Expo-2020.jpg",
    "N W Z": "https://brightluxx.com/wp-content/uploads/2022/05/P10-LED-Screen-Outdoor-at-N-W-Z-WEST-ZONE-MALL-1.jpg",
    "MICROVISION": "https://brightluxx.com/wp-content/uploads/2022/05/P5-LED-Screen-at-MICROVISION-INTERIORS-LLC-1.jpg",
    "Nesto": "https://brightluxx.com/wp-content/uploads/2022/05/Nesto-Hypermarket.jpg",
    "Test Project": "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg",
}

# Inspiration category to WP images
INSPIRATION_IMAGE_MAP = {
    "Immersive Retail": ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-Shop-Signage-4.jpg", "insp_retail.webp"),
    "Stadium Spectacle": ("https://brightluxx.com/wp-content/uploads/2022/05/SPORTS-LOUNGE.jpg", "insp_stadium.webp"),
    "Architectural Media": ("https://brightluxx.com/wp-content/uploads/2022/05/Curtain-LED-Display-2.jpg", "insp_facade.webp"),
    "Interactive Floor": ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-2.jpg", "insp_floor.webp"),
    "Holographic Storefront": ("https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-2.jpg", "insp_holographic.webp"),
    "Immersive Room": ("https://brightluxx.com/wp-content/uploads/2022/05/Curve-Flexible-LED-Display-2.jpg", "insp_immersive.webp"),
    "Corporate Command": ("https://brightluxx.com/wp-content/uploads/2022/05/Conference-Hall-4.jpg", "insp_command.webp"),
    "Luxury Hotel": ("https://brightluxx.com/wp-content/uploads/2022/05/Meeting-Room-4.jpg", "insp_hotel.webp"),
    "Concert Stage": ("https://brightluxx.com/wp-content/uploads/2022/04/DIGITAL-BANNERS-1.jpg", "insp_concert.webp"),
    "Home Cinema": ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA1.jpg", "insp_cinema.webp"),
    "Museum Interactive": ("https://brightluxx.com/wp-content/uploads/2022/05/Floor-LED-Display-1.jpg", "insp_museum.webp"),
    "Digital Highway": ("https://brightluxx.com/wp-content/uploads/2022/05/road-advertising-1.jpg", "insp_highway.webp"),
    "Transparent Storefront": ("https://brightluxx.com/wp-content/uploads/2022/05/Transparent-Glass-LED-Display-1.jpg", "insp_transparent.webp"),
    "All-in-One Boardroom": ("https://brightluxx.com/wp-content/uploads/2022/05/CONFERENCE-HALL-3.jpg", "insp_boardroom.webp"),
    "Smart City": ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-SMD-LED-Display-2.jpg", "insp_smartcity.webp"),
    "Expo Pavilion": ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Screen-at-Indian-Pavillion-Expo-2020.jpg", "insp_expo.webp"),
    "Naked-Eye 3D": ("https://brightluxx.com/wp-content/uploads/2022/05/OUTDOOR-SHOP-SIGNAGE-2.jpg", "insp_3d.webp"),
    "LED Sphere": ("https://brightluxx.com/wp-content/uploads/2022/05/Spherical-LED-Display-2.jpg", "insp_sphere.webp"),
    "Virtual Production": ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-2.jpg", "insp_vp.webp"),
    "Shelf Edge": ("https://brightluxx.com/wp-content/uploads/2022/05/Shelf-LED-Display-2.jpg", "insp_shelf.webp"),
    "Cinema LED": ("https://brightluxx.com/wp-content/uploads/2022/05/HOME-CINEMA3.jpg", "insp_cinema_led.webp"),
    "Sky Ceiling": ("https://brightluxx.com/wp-content/uploads/2022/04/Indoor-LED-Screens-1.jpg", "insp_ceiling.webp"),
}

# Banner/hero images
HERO_IMAGES = [
    ("https://brightluxx.com/wp-content/uploads/2022/05/Home-Banner.jpg", "hero_banner.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/04/BRIGHTLUXX-banners8.jpg", "hero_banner_2.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/04/BRIGHTLUXX-banners7.jpg", "hero_banner_3.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/04/BRIGHTLUXX-banners6.jpg", "hero_banner_4.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/04/about-us-banner.jpg", "about_banner.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/04/about-us-footer-banner.jpg", "about_footer_banner.webp"),
]

# Logo
LOGO_IMAGES = [
    ("https://brightluxx.com/wp-content/uploads/2022/03/Brightluxx-logo-white.png", "brightluxx_logo_white.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/03/brightlux-logo-png.png", "brightluxx_logo.webp"),
]

# Solution images
SOLUTION_IMAGES = [
    ("https://brightluxx.com/wp-content/uploads/2022/05/Sports-Lounge-1.jpg", "sol_sports.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/road-advertising-1.jpg", "sol_road.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Pavement-Advertising-1.jpg", "sol_pavement.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-1-1.jpg", "sol_outdoor_shop.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-Shop-Signage-4.jpg", "sol_indoor_shop.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Meeting-Room-4.jpg", "sol_meeting.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Home-Cinema-1.jpg", "sol_cinema.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Exhibition-3.jpg", "sol_exhibition.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Education-1.jpg", "sol_education.webp"),
    ("https://brightluxx.com/wp-content/uploads/2022/05/Conference-Hall-4.jpg", "sol_conference.webp"),
]


def download_and_convert(url, filename, max_width=1200):
    """Download image from URL and save as optimized WebP."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        print(f"  [SKIP] {filename} already exists")
        return True

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        img.save(filepath, "WEBP", quality=82)
        print(f"  [OK] {filename} ({img.width}x{img.height})")
        return True
    except Exception as e:
        print(f"  [FAIL] {filename}: {e}")
        return False


async def update_products(db):
    """Update product images by category."""
    print("\n=== UPDATING PRODUCTS ===")
    products_col = db["products"]

    for category, images in CATEGORY_IMAGE_MAP.items():
        # Download images for this category
        downloaded = []
        for url, filename in images:
            if download_and_convert(url, filename):
                downloaded.append(f"/uploads/{filename}")

        if not downloaded:
            print(f"  [WARN] No images downloaded for {category}")
            continue

        # Update all products in this category
        cursor = products_col.find({"category": category})
        products = await cursor.to_list(length=100)
        for i, product in enumerate(products):
            img_url = downloaded[i % len(downloaded)]
            gallery = downloaded[:3] if len(downloaded) > 1 else downloaded
            await products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"image_url": img_url, "gallery": gallery}}
            )
            print(f"  Updated [{category}] {product['name']} => {img_url}")


async def update_projects(db):
    """Update project images by matching project title keywords."""
    print("\n=== UPDATING PROJECTS ===")
    projects_col = db["projects"]

    cursor = projects_col.find({})
    projects = await cursor.to_list(length=100)

    for project in projects:
        title = project.get("title", "")
        matched_url = None

        # Try to match project title to our mapping
        for keyword, url in PROJECT_IMAGE_MAP.items():
            if keyword.lower() in title.lower():
                matched_url = url
                break

        if not matched_url:
            # Default fallback for unmatched projects
            matched_url = "https://brightluxx.com/wp-content/uploads/2022/05/Outdoor-Shop-Signage-3.jpg"

        # Create safe filename from project title
        safe_name = re.sub(r'[^a-z0-9]', '_', title.lower().strip())[:40]
        filename = f"proj_{safe_name}.webp"

        if download_and_convert(matched_url, filename):
            await projects_col.update_one(
                {"_id": project["_id"]},
                {"$set": {"image_url": f"/uploads/{filename}"}}
            )
            print(f"  Updated project: {title} => /uploads/{filename}")


async def update_inspirations(db):
    """Update inspiration images."""
    print("\n=== UPDATING INSPIRATIONS ===")
    inspirations_col = db["inspirations"]

    cursor = inspirations_col.find({})
    inspirations = await cursor.to_list(length=100)

    for insp in inspirations:
        title = insp.get("title", "")
        matched = None

        for keyword, (url, filename) in INSPIRATION_IMAGE_MAP.items():
            if keyword.lower() in title.lower():
                matched = (url, filename)
                break

        if not matched:
            matched = ("https://brightluxx.com/wp-content/uploads/2022/05/Indoor-LED-Display-3.jpg", f"insp_default.webp")

        url, filename = matched
        if download_and_convert(url, filename):
            await inspirations_col.update_one(
                {"_id": insp["_id"]},
                {"$set": {"image_url": f"/uploads/{filename}"}}
            )
            print(f"  Updated inspiration: {title} => /uploads/{filename}")


def download_extras():
    """Download hero banners, logos, and solution images."""
    print("\n=== DOWNLOADING BANNERS & LOGOS ===")
    for url, filename in HERO_IMAGES + LOGO_IMAGES:
        download_and_convert(url, filename, max_width=1920)

    print("\n=== DOWNLOADING SOLUTION IMAGES ===")
    for url, filename in SOLUTION_IMAGES:
        download_and_convert(url, filename, max_width=1200)


async def main():
    print("=" * 60)
    print("  BRIGHTLUXX REAL IMAGE DOWNLOADER")
    print("=" * 60)

    # Download extra images (banners, logos, solutions)
    download_extras()

    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Update each collection
    await update_products(db)
    await update_projects(db)
    await update_inspirations(db)

    # Count results
    products_col = db["products"]
    projects_col = db["projects"]
    inspirations_col = db["inspirations"]

    p_count = await products_col.count_documents({})
    pr_count = await projects_col.count_documents({})
    i_count = await inspirations_col.count_documents({})

    print("\n" + "=" * 60)
    print(f"  COMPLETE: {p_count} products, {pr_count} projects, {i_count} inspirations updated")
    print("=" * 60)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
