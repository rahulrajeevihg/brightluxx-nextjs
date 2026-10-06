"""
Seed Home Cinema products into the database.
Premium LED display products for luxury home theater and cinema room installations.
"""
import asyncio
from datetime import datetime, timezone
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "brightluxx")

PRODUCTS = [
    # --- Cinema Screens (cinema-screen) ---
    {
        "name": "CinemaLED Pro 1.2",
        "slug": "cinemaled-pro-12",
        "product_code": "BL-HC-CP12",
        "category": "home-cinema",
        "sub_category": "cinema-screen",
        "family": "CinemaLED",
        "tagline": "Reference-grade MicroLED for dedicated home theaters.",
        "description": "The CinemaLED Pro 1.2 is our flagship home cinema display, delivering true 4K resolution at 1.2mm pixel pitch with DCI-P3 color gamut coverage. Designed for dedicated screening rooms and luxury home theaters, it features ISF certification, THX-class contrast ratios, and an ultra-quiet fanless thermal design. HDR10+ and Dolby Vision ensure reference-grade playback for the most discerning cinephiles. Available in 100\", 120\", 150\" and custom diagonal sizes.",
        "pixel_pitch": "1.2mm",
        "brightness": "800 nits (peak 1500 nits HDR)",
        "application": "Dedicated Home Theaters, Screening Rooms, Private Cinemas",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.2mm"},
            {"label": "Resolution", "value": "4K UHD (3840x2160)"},
            {"label": "Color Gamut", "value": "DCI-P3 (99.8%)"},
            {"label": "Contrast", "value": "100000:1"},
            {"label": "HDR", "value": "HDR10+, Dolby Vision"},
            {"label": "Refresh Rate", "value": "7680Hz"},
            {"label": "Sizes", "value": "100\", 120\", 150\", Custom"},
            {"label": "Noise", "value": "Fanless (0dB)"},
        ],
        "features": ["DCI-P3 99.8%", "Dolby Vision", "ISF Certified", "Fanless Design", "THX-Class Contrast", "Front Serviceable"],
        "image_url": "https://files.ihgbrands.com/emergent-images/2031d053c67d612c7dc323331b83b59af6f8320b60abdd2d32421775987d0177.png",
        "featured": True,
        "trending": True,
    },
    {
        "name": "CinemaLED Ultra 0.9",
        "slug": "cinemaled-ultra-09",
        "product_code": "BL-HC-CU09",
        "category": "home-cinema",
        "sub_category": "cinema-screen",
        "family": "CinemaLED",
        "tagline": "8K MicroLED for the ultimate home cinema experience.",
        "description": "The pinnacle of home cinema technology. CinemaLED Ultra delivers true 8K resolution at 0.9mm pixel pitch using COB MicroLED, offering an unprecedented 33 million pixels for screens 150\" and above. Pixel-level dimming enables infinite contrast in perfectly dark viewing rooms. Integrated Dolby Atmos-synchronized ambient lighting creates a fully immersive cinema atmosphere. Each unit is individually calibrated at the factory for D65 white point accuracy.",
        "pixel_pitch": "0.9mm",
        "brightness": "1000 nits (peak 2000 nits HDR)",
        "application": "Ultra-Luxury Home Cinemas, Superyacht Theaters, VIP Screening Rooms",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "0.9mm"},
            {"label": "Resolution", "value": "8K (7680x4320)"},
            {"label": "Technology", "value": "COB MicroLED"},
            {"label": "Color Gamut", "value": "BT.2020 (95%)"},
            {"label": "Contrast", "value": "Infinite (pixel dimming)"},
            {"label": "HDR", "value": "HDR10+, Dolby Vision IQ"},
            {"label": "Calibration", "value": "Factory D65"},
            {"label": "Sizes", "value": "150\", 180\", 220\", Custom"},
        ],
        "features": ["8K Resolution", "COB MicroLED", "Pixel-Level Dimming", "Dolby Vision IQ", "Ambient Sync Lighting", "Factory Calibrated"],
        "image_url": "https://files.ihgbrands.com/emergent-images/64444ed7ca157e07ab9eeea06f1bb969e8744dbda982442ba235f506fd348b48.png",
        "featured": True,
        "new_arrival": True,
    },

    # --- Living Room / Multi-Purpose (living-room) ---
    {
        "name": "AmbientScreen 1.5",
        "slug": "ambientscreen-15",
        "product_code": "BL-HC-AS15",
        "category": "home-cinema",
        "sub_category": "living-room",
        "family": "AmbientScreen",
        "tagline": "LED wall that doubles as art when you're not watching.",
        "description": "AmbientScreen transforms any living room wall into a stunning LED display that switches between cinema mode and ambient art mode. In cinema mode, enjoy 4K HDR content with 2000:1 contrast. In ambient mode, display curated artwork, family photos, or dynamic screensavers that blend with your interior design. Ultra-slim 32mm depth mounts flush to the wall. Built-in AI upscaling enhances any content to near-4K quality.",
        "pixel_pitch": "1.5mm",
        "brightness": "600 nits (adjustable 50-600)",
        "application": "Living Rooms, Family Rooms, Master Bedrooms, Penthouses",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.5mm"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Depth", "value": "32mm (flush mount)"},
            {"label": "Brightness", "value": "50-600 nits (auto)"},
            {"label": "Modes", "value": "Cinema / Ambient Art"},
            {"label": "AI Upscaling", "value": "Yes"},
            {"label": "Sizes", "value": "85\", 100\", 120\", 136\""},
        ],
        "features": ["Ambient Art Mode", "Flush Mount 32mm", "AI Upscaling", "Auto Brightness", "Curated Art Gallery", "Smart Home Integration"],
        "image_url": "https://files.ihgbrands.com/emergent-images/ea77d4dd0e99bf17d39a28af7bcce5ed3db13b59241d32385de3a59cf9952a29.png",
    },
    {
        "name": "AmbientScreen Curved 1.8",
        "slug": "ambientscreen-curved-18",
        "product_code": "BL-HC-ASC18",
        "category": "home-cinema",
        "sub_category": "living-room",
        "family": "AmbientScreen",
        "tagline": "Curved LED for wraparound immersion in any room.",
        "description": "Experience cinema-grade immersion with a gently curved LED display that wraps around your field of vision. The concave curvature matches the natural curvature of the human eye, reducing eye strain during long viewing sessions and creating a more immersive experience than flat screens. Ideal for open-plan living areas and game rooms. Available in 2000R, 3000R, and 4000R curvatures.",
        "pixel_pitch": "1.8mm",
        "brightness": "800 nits",
        "application": "Media Rooms, Game Rooms, Open-Plan Living, Entertainment Lounges",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.8mm"},
            {"label": "Curvature", "value": "2000R / 3000R / 4000R"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Viewing Angle", "value": "178°"},
            {"label": "Refresh", "value": "3840Hz"},
            {"label": "Sizes", "value": "120\", 150\", 180\""},
        ],
        "features": ["Curved Design", "Multiple Curvatures", "Wide Viewing Angle", "Gaming Mode 120fps", "Low Latency <8ms"],
        "image_url": "https://files.ihgbrands.com/emergent-images/f7ad6c93eff45321279f7b8912a259cd14afd89d426a4ecb8c8a049055ac5a98.png",
    },

    # --- Outdoor Cinema (outdoor-cinema) ---
    {
        "name": "PoolView P3.9",
        "slug": "poolview-p39",
        "product_code": "BL-HC-PV39",
        "category": "home-cinema",
        "sub_category": "outdoor-cinema",
        "family": "PoolView",
        "tagline": "Weather-proof outdoor cinema for poolside and gardens.",
        "description": "PoolView brings cinema-quality viewing to outdoor living spaces. IP65-rated panels withstand Dubai's extreme heat, humidity, sandstorms, and direct sun. Anti-glare coating and 5000 nits peak brightness ensure vibrant image quality even in bright daylight. Retractable or fixed mounting options. Perfect for villa gardens, rooftop terraces, and resort pool areas across the GCC.",
        "pixel_pitch": "3.9mm",
        "brightness": "5000 nits (outdoor daylight)",
        "application": "Pool Areas, Villa Gardens, Rooftop Terraces, Resort Cinemas",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "3.9mm"},
            {"label": "Brightness", "value": "5000 nits"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Operating Temp", "value": "-20°C to 60°C"},
            {"label": "Anti-Glare", "value": "Yes"},
            {"label": "Sizes", "value": "100\", 120\", 150\", 200\""},
        ],
        "features": ["IP65 Weatherproof", "5000 Nits Daylight", "Anti-Glare Coating", "Sand/Dust Resistant", "Retractable Mount Option", "Auto Brightness Sensor"],
        "image_url": "https://files.ihgbrands.com/emergent-images/127b54193b9ab0ec636c8645560811771af1f58dde5daceea69f261828cf7c0a.png",
    },
    {
        "name": "PoolView Retractable P2.9",
        "slug": "poolview-retractable-p29",
        "product_code": "BL-HC-PVR29",
        "category": "home-cinema",
        "sub_category": "outdoor-cinema",
        "family": "PoolView",
        "tagline": "Motorized retractable LED screen for seamless outdoor living.",
        "description": "The PoolView Retractable rises from a concealed housing when you want to watch, and disappears completely when you don't. Motorized lift system with whisper-quiet operation (under 35dB). Fine 2.9mm pixel pitch delivers sharp 4K content outdoors. IP65 rated with automatic rain detection — the screen retracts automatically if it starts raining. Designed for luxury villas, superyachts, and premium hospitality venues.",
        "pixel_pitch": "2.9mm",
        "brightness": "4500 nits",
        "application": "Luxury Villas, Superyachts, Resort Terraces, Premium Hospitality",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "2.9mm"},
            {"label": "Brightness", "value": "4500 nits"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Mechanism", "value": "Motorized Retractable"},
            {"label": "Noise", "value": "<35dB"},
            {"label": "Rain Sensor", "value": "Auto-retract"},
            {"label": "Sizes", "value": "85\", 100\", 120\""},
        ],
        "features": ["Motorized Retractable", "Auto Rain Sensor", "Concealed Housing", "Whisper Quiet", "IP65", "Remote Control + App"],
        "image_url": "https://files.ihgbrands.com/emergent-images/0f94ba2fb077d6c4bdf8613e9ec3fa9295c46a647cb8f37a7afc192b6e8a1f2c.png",
        "new_arrival": True,
    },

    # --- Private Theater Systems (theater-system) ---
    {
        "name": "TheaterPro Complete System",
        "slug": "theaterpro-complete",
        "product_code": "BL-HC-TPC",
        "category": "home-cinema",
        "sub_category": "theater-system",
        "family": "TheaterPro",
        "tagline": "Turnkey home cinema: screen, processor, calibration included.",
        "description": "TheaterPro is a complete home cinema solution — not just a screen. Includes the CinemaLED Pro display, a dedicated 4K HDR video processor, color calibration service, acoustic-transparent mounting system (for behind-screen speakers), and installation by certified Brightluxx engineers. Designed for custom integrators and luxury home builders who want a single-vendor cinema solution. ISF Level III calibration included.",
        "pixel_pitch": "1.5mm",
        "brightness": "800 nits",
        "application": "Custom Home Theaters, Developer Show Homes, Private Screening Rooms",
        "key_specs": [
            {"label": "Screen", "value": "CinemaLED Pro 1.5"},
            {"label": "Processor", "value": "4K HDR Dedicated"},
            {"label": "Calibration", "value": "ISF Level III"},
            {"label": "Audio Mount", "value": "Acoustic Transparent"},
            {"label": "Installation", "value": "Included"},
            {"label": "Warranty", "value": "5 Years On-Site"},
            {"label": "Sizes", "value": "100\", 120\", 150\", Custom"},
        ],
        "features": ["Turnkey Solution", "ISF Level III Calibration", "Acoustic Transparent", "Dedicated Processor", "5-Year On-Site Warranty", "Certified Installation"],
        "image_url": "https://files.ihgbrands.com/emergent-images/db7d33a7c4fd4942b9c17775de14a895_brightluxx-xr-stage-p26.png",
        "featured": True,
    },
    {
        "name": "TheaterPro Mini System",
        "slug": "theaterpro-mini",
        "product_code": "BL-HC-TPM",
        "category": "home-cinema",
        "sub_category": "theater-system",
        "family": "TheaterPro",
        "tagline": "Compact cinema system for bedrooms and small media rooms.",
        "description": "TheaterPro Mini brings cinematic quality to smaller spaces — bedrooms, studies, and compact media rooms. The 85\" to 100\" display uses 1.8mm pixel pitch for sharp 4K content at close viewing distances. Includes a slim video processor, basic ISF calibration, and wall-mount installation. Perfect entry point into LED home cinema without the space requirements of a dedicated theater room.",
        "pixel_pitch": "1.8mm",
        "brightness": "600 nits",
        "application": "Bedrooms, Studies, Small Media Rooms, Guest Suites",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.8mm"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Processor", "value": "Slim 4K HDR"},
            {"label": "Calibration", "value": "ISF Basic"},
            {"label": "Depth", "value": "45mm"},
            {"label": "Sizes", "value": "85\", 100\""},
        ],
        "features": ["Compact Form Factor", "4K HDR", "ISF Calibration", "Slim Processor", "Easy Installation", "3-Year Warranty"],
        "image_url": "https://files.ihgbrands.com/emergent-images/274aea0bafb14d0892ce8fab0e20da43_brightluxx-metaled-p29.png",
    },

    # --- Gaming (gaming-display) ---
    {
        "name": "GameWall 240Hz",
        "slug": "gamewall-240hz",
        "product_code": "BL-HC-GW240",
        "category": "home-cinema",
        "sub_category": "gaming-display",
        "family": "GameWall",
        "tagline": "240Hz LED wall built for competitive and immersive gaming.",
        "description": "GameWall is purpose-built for gamers who demand the largest, fastest display possible. 240Hz native refresh rate with under 3ms input lag delivers competitive-grade responsiveness on a massive LED canvas. VRR (Variable Refresh Rate) support for both AMD FreeSync and NVIDIA G-SYNC eliminates tearing. Game-specific display modes for FPS, racing, and RPG genres. HDMI 2.1 and DisplayPort 2.0 inputs support 4K@240Hz.",
        "pixel_pitch": "1.5mm",
        "brightness": "1000 nits",
        "application": "Gaming Rooms, Esports Training, Sim Racing Setups, VR Lounges",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.5mm"},
            {"label": "Refresh Rate", "value": "240Hz native"},
            {"label": "Input Lag", "value": "<3ms"},
            {"label": "VRR", "value": "FreeSync + G-SYNC"},
            {"label": "Inputs", "value": "HDMI 2.1, DP 2.0"},
            {"label": "Sizes", "value": "100\", 120\", 150\""},
        ],
        "features": ["240Hz Native", "<3ms Input Lag", "FreeSync + G-SYNC", "Game Display Modes", "HDMI 2.1", "RGB Ambient Sync"],
        "image_url": "https://files.ihgbrands.com/emergent-images/e88abae78ea54b8bb3107b916d7bcf93_brightluxx-interactiveart-floor-p39.png",
        "trending": True,
    },
    {
        "name": "GameWall Sim 180°",
        "slug": "gamewall-sim-180",
        "product_code": "BL-HC-GWS180",
        "category": "home-cinema",
        "sub_category": "gaming-display",
        "family": "GameWall",
        "tagline": "180° curved LED for sim racing and flight simulation.",
        "description": "The ultimate sim racing and flight simulation display. Three curved LED panels wrap 180° around your cockpit for complete peripheral vision immersion. Designed specifically for high-end sim rigs, flight simulators, and VR alternative setups. Ultra-low 2ms response time ensures zero motion blur at high speeds. Compatible with all major sim racing software and flight simulation platforms.",
        "pixel_pitch": "1.8mm",
        "brightness": "800 nits",
        "application": "Sim Racing, Flight Simulation, Driving Simulators, VR Alternative",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.8mm"},
            {"label": "Curvature", "value": "180° wraparound"},
            {"label": "Panels", "value": "3-panel system"},
            {"label": "Response Time", "value": "2ms"},
            {"label": "Refresh Rate", "value": "144Hz"},
            {"label": "Compatibility", "value": "iRacing, ACC, MSFS, DCS"},
        ],
        "features": ["180° Wraparound", "3-Panel System", "2ms Response", "Sim-Optimized", "Cockpit Mount Kit", "Multi-Source Input"],
        "image_url": "https://files.ihgbrands.com/emergent-images/d8aa0f3a397d43c3af6e72ef0c97cd99_brightluxx-interactivefloor-p39.png",
    },
]


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["products"]

    inserted = 0
    updated = 0
    for product in PRODUCTS:
        product["status"] = "published"
        product["created_at"] = datetime.now(timezone.utc)
        product["updated_at"] = datetime.now(timezone.utc)
        if "id" not in product:
            product["id"] = str(uuid.uuid4())

        existing = await col.find_one({"slug": product["slug"]})
        if existing:
            await col.update_one({"slug": product["slug"]}, {"$set": product})
            updated += 1
            print(f"  Updated: {product['name']}")
        else:
            await col.insert_one(product)
            inserted += 1
            print(f"  Inserted: {product['name']}")

    total = await col.count_documents({"category": "home-cinema"})
    print(f"\nDone: {inserted} inserted, {updated} updated. Total home-cinema products: {total}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
