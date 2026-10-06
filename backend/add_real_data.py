"""
Add real Brightluxx projects and modern LED products to the database.
Run once: python3 add_real_data.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ─── REAL PROJECTS from brightluxx.com/our-works ───
REAL_PROJECTS = [
    {
        "title": "Nesto Hypermarket — LED Pixel Display",
        "client_name": "Nesto Hypermarket",
        "location": "Al Warsan, Dubai",
        "sector": "retail",
        "screen_size": "Custom",
        "description": "Large-format LED Pixel display installation for Nesto Hypermarket at Al Warsan, enhancing the retail storefront with vibrant digital signage to attract shoppers.",
        "technologies_used": ["LED Pixel", "Indoor Display"],
        "featured": True,
    },
    {
        "title": "LED Screen — MICROVISION INTERIORS LLC",
        "client_name": "MICROVISION INTERIORS LLC",
        "location": "Dubai",
        "sector": "corporate",
        "screen_size": "P5 Indoor",
        "description": "P5 indoor LED screen solution for MICROVISION INTERIORS LLC, delivering sharp visuals for their corporate office and showroom environment.",
        "technologies_used": ["P5 Indoor", "SMD Display"],
        "featured": False,
    },
    {
        "title": "Outdoor LED Screen — N W Z West Zone Mall",
        "client_name": "N W Z West Zone Mall",
        "location": "Dubai",
        "sector": "retail",
        "screen_size": "P10 Outdoor",
        "description": "High-brightness P10 outdoor LED display at West Zone Mall, delivering eye-catching advertising content visible in direct sunlight.",
        "technologies_used": ["P10 Outdoor", "SMD Display", "High Brightness"],
        "featured": True,
    },
    {
        "title": "Indian Pavilion — Expo 2020 Dubai",
        "client_name": "Indian Pavilion, Expo 2020",
        "location": "Dubai",
        "sector": "exhibitions",
        "screen_size": "P2.5 Indoor",
        "description": "Premium P2.5 indoor LED screen installation at the Indian Pavilion during Expo 2020 Dubai, showcasing India's culture and innovation to millions of global visitors.",
        "technologies_used": ["P2.5 Indoor", "High Resolution", "Exhibition Grade"],
        "featured": True,
    },
    {
        "title": "Exhibition Display — Dubai World Trade Centre",
        "client_name": "Dubai World Trade Centre",
        "location": "Dubai",
        "sector": "exhibitions",
        "screen_size": "P2.5 with Processor",
        "description": "High-resolution P2.5 LED display with dedicated video processor for exhibitions at the prestigious Dubai World Trade Centre.",
        "technologies_used": ["P2.5 Indoor", "Video Processor", "Exhibition Grade"],
        "featured": True,
    },
    {
        "title": "MEB Kiosk Display — Delma Mall",
        "client_name": "MEB",
        "location": "Delma Mall, Abu Dhabi",
        "sector": "retail",
        "screen_size": "P2.5",
        "description": "Interactive P2.5 LED kiosk display at Delma Mall in Abu Dhabi, providing clear digital communication for MEB brand engagement.",
        "technologies_used": ["P2.5 Indoor", "Kiosk Display"],
        "featured": False,
    },
    {
        "title": "Conference Room Screen — FNAC Fujairah Airport",
        "client_name": "FNAC",
        "location": "Fujairah Airport",
        "sector": "corporate",
        "screen_size": "P2.5 with Processor",
        "description": "P2.5 LED screen with video processor for the FNAC conference room at Fujairah Airport, enabling high-quality presentations and video conferencing.",
        "technologies_used": ["P2.5 Indoor", "Video Processor", "Conference Room"],
        "featured": False,
    },
    {
        "title": "Office Internal Screen — Division Nine",
        "client_name": "Division Nine",
        "location": "Jumeirah Lakes Towers, Dubai",
        "sector": "corporate",
        "screen_size": "P1.8 Indoor",
        "description": "Fine-pitch P1.8 indoor LED screen for Division Nine's office at JLT, delivering ultra-sharp content for internal communications and presentations.",
        "technologies_used": ["P1.8 Indoor", "Fine Pitch", "Corporate Display"],
        "featured": False,
    },
    {
        "title": "Shop Front Screen — Infinity Café",
        "client_name": "Infinity Café",
        "location": "Al Nahda, Dubai",
        "sector": "hospitality",
        "screen_size": "P5 Outdoor",
        "description": "Vibrant P5 outdoor LED shopfront display for Infinity Café in Al Nahda, attracting foot traffic with dynamic menu boards and promotional content.",
        "technologies_used": ["P5 Outdoor", "Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Kijora Office Display — I2D Interiors",
        "client_name": "I2D Interiors",
        "location": "Business Bay, Dubai",
        "sector": "corporate",
        "screen_size": "P3.8",
        "description": "P3.8 LED display for Kijora Office at Business Bay, designed by I2D Interiors, creating a modern digital wall for the corporate workspace.",
        "technologies_used": ["P3.8 Indoor", "Corporate Display"],
        "featured": False,
    },
    {
        "title": "External Screen — Al Mutakamela Vehicle Testing",
        "client_name": "Al Mutakamela Vehicle Testing",
        "location": "Al Quoz 3, Dubai",
        "sector": "government",
        "screen_size": "P6 Outdoor",
        "description": "P6 outdoor LED screen at Al Mutakamela Vehicle Testing center, providing clear public information and queue management displays.",
        "technologies_used": ["P6 Outdoor", "Public Information"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Sharaf Exchange",
        "client_name": "Sharaf Exchange",
        "location": "Satwa, Dubai",
        "sector": "retail",
        "screen_size": "P5 Outdoor",
        "description": "P5 outdoor shopfront LED display for Sharaf Exchange in Satwa, displaying real-time exchange rates and promotional offers to passersby.",
        "technologies_used": ["P5 Outdoor", "Shopfront Display", "Financial Services"],
        "featured": False,
    },
    {
        "title": "Jehangir Shopfront — Top Rock Interiors",
        "client_name": "Top Rock Interiors",
        "location": "Al Mankhool, Dubai",
        "sector": "retail",
        "screen_size": "P6 Outdoor",
        "description": "P6 outdoor LED shopfront screen designed by Top Rock Interiors for the Jehangir store in Al Mankhool.",
        "technologies_used": ["P6 Outdoor", "Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Fine Mart",
        "client_name": "Fine Mart",
        "location": "The Marina Torch, Dubai",
        "sector": "retail",
        "screen_size": "P5 Outdoor",
        "description": "Eye-catching P5 outdoor LED display at Fine Mart in The Marina Torch, Dubai, drawing customers with bright digital content.",
        "technologies_used": ["P5 Outdoor", "Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Cosmomed External Screen — FNAC",
        "client_name": "FNAC / Cosmomed",
        "location": "Al Faseel Rd (E99), Fujairah",
        "sector": "healthcare",
        "screen_size": "P5 Outdoor",
        "description": "P5 outdoor LED display for Cosmomed medical center, providing high-visibility digital signage on the Al Faseel Road in Fujairah.",
        "technologies_used": ["P5 Outdoor", "Healthcare Signage"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Planer First General Trading",
        "client_name": "Planer First General Trading",
        "location": "Al Rigga, Dubai",
        "sector": "retail",
        "screen_size": "P6 Outdoor",
        "description": "P6 outdoor LED shopfront display in the busy Al Rigga commercial area.",
        "technologies_used": ["P6 Outdoor", "Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Ahmed Al Maghribi",
        "client_name": "Ahmed Al Maghribi",
        "location": "Deira, Dubai",
        "sector": "retail",
        "screen_size": "P4 Outdoor",
        "description": "P4 outdoor high-resolution LED shopfront screen for Ahmed Al Maghribi perfumes in the heart of Deira, Dubai.",
        "technologies_used": ["P4 Outdoor", "HD Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Sulthan Gold and Diamond",
        "client_name": "Sulthan Gold and Diamond",
        "location": "Al Souq Al Kabeer, Dubai",
        "sector": "retail",
        "screen_size": "P4 Outdoor",
        "description": "Premium P4 outdoor LED display for Sulthan Gold and Diamond at the iconic Al Souq Al Kabeer, showcasing luxury jewellery collections.",
        "technologies_used": ["P4 Outdoor", "Luxury Retail Display"],
        "featured": True,
    },
    {
        "title": "Shopfront Screen — Jawhara Jewellery",
        "client_name": "Jawhara Jewellery",
        "location": "Al Wahda Mall, Abu Dhabi",
        "sector": "retail",
        "screen_size": "P6 Outdoor",
        "description": "P6 LED shopfront screen for Jawhara Jewellery at Al Wahda Mall, Abu Dhabi, displaying stunning jewellery visuals.",
        "technologies_used": ["P6 Outdoor", "Mall Display"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Oud Majed",
        "client_name": "Oud Majed",
        "location": "Dubai Hills Mall",
        "sector": "retail",
        "screen_size": "P2.5 Indoor",
        "description": "Elegant P2.5 indoor LED display for Oud Majed perfumery at Dubai Hills Mall, creating an immersive luxury brand experience.",
        "technologies_used": ["P2.5 Indoor", "Luxury Retail"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — Shater Restaurant",
        "client_name": "Shater Restaurant",
        "location": "Al Nahda, Sharjah",
        "sector": "hospitality",
        "screen_size": "P6 Outdoor",
        "description": "Vibrant P6 outdoor LED display for Shater Restaurant in Sharjah, showcasing menu highlights and promotions.",
        "technologies_used": ["P6 Outdoor", "Restaurant Signage"],
        "featured": False,
    },
    {
        "title": "Sulthan Gold & Diamond — Bur Dubai",
        "client_name": "Sulthan Gold and Diamond",
        "location": "Bur Dubai",
        "sector": "retail",
        "screen_size": "P4 Outdoor",
        "description": "Second Sulthan Gold & Diamond location with P4 outdoor LED display in the busy Bur Dubai commercial district.",
        "technologies_used": ["P4 Outdoor", "Luxury Retail"],
        "featured": False,
    },
    {
        "title": "Restaurant Front Screen — Sulthanate",
        "client_name": "Sulthanate Restaurant",
        "location": "Ajman",
        "sector": "hospitality",
        "screen_size": "P6 Outdoor",
        "description": "P6 outdoor LED front display for Sulthanate Restaurant in Ajman, delivering appetizing menu visuals to attract diners.",
        "technologies_used": ["P6 Outdoor", "Restaurant Signage"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — LED World LLC (Khorfakan)",
        "client_name": "LED World LLC",
        "location": "Khorfakan",
        "sector": "retail",
        "screen_size": "P5 Outdoor",
        "description": "P5 outdoor LED display for LED World LLC's storefront in Khorfakan.",
        "technologies_used": ["P5 Outdoor", "Shopfront Display"],
        "featured": False,
    },
    {
        "title": "Shopfront Screen — LED World LLC (Ajman)",
        "client_name": "LED World LLC",
        "location": "Ajman",
        "sector": "retail",
        "screen_size": "P6 Outdoor",
        "description": "P6 outdoor LED display installation for LED World LLC's Ajman branch.",
        "technologies_used": ["P6 Outdoor", "Shopfront Display"],
        "featured": False,
    },
]

# ─── NEW PRODUCTS (modern trending pitches) ───
NEW_PRODUCTS = [
    # Indoor fine-pitch modules from their website + modern trends
    {
        "product_code": "BL-ISF156",
        "name": "Indoor Soft Flex P1.5625",
        "category": "flexible",
        "tagline": "Ultra-Fine Curved Display Module",
        "description": "P1.5625 indoor 200x150mm soft flexible LED screen module for curved iron cabinets. High-quality black surface small pixel LED, ideal for creative installations and curved video walls.",
        "pixel_pitch": "1.5625mm",
        "resolution": "128x96 per module",
        "brightness": "1,000 nits",
        "application": "Creative curved displays, retail feature walls, immersive environments",
        "key_specs": [
            {"label": "Module Size", "value": "200x150mm"},
            {"label": "Pixel Config", "value": "SMD1010"},
            {"label": "Bend Radius", "value": "Min 500mm"},
            {"label": "Service", "value": "Front / Magnetic"},
        ],
    },
    {
        "product_code": "BL-IP3",
        "name": "IndoorPro P3 Soft Module",
        "category": "indoor",
        "tagline": "Versatile Indoor LED Module",
        "description": "P3 1/32 scan indoor 64x64 dot 192x192mm LED screen soft flexible module. Can be used for curved iron cabinets and irregular installations where standard flat panels won't fit.",
        "pixel_pitch": "3mm",
        "resolution": "64x64 per module",
        "brightness": "1,200 nits",
        "application": "Conference rooms, retail, curved columns, creative installations",
        "key_specs": [
            {"label": "Module Size", "value": "192x192mm"},
            {"label": "Scan Mode", "value": "1/32 Scan"},
            {"label": "Pixel Config", "value": "SMD2121"},
            {"label": "Refresh Rate", "value": "3,840Hz"},
        ],
    },
    {
        "product_code": "BL-IP307",
        "name": "IndoorPro P3.076 HD Module",
        "category": "indoor",
        "tagline": "HD Video Screen Module",
        "description": "P3.076 320x160mm indoor HD LED video screen module. 72-hour continuous aging test ensures zero broken pixels. Ideal for permanent installations requiring reliability.",
        "pixel_pitch": "3.076mm",
        "resolution": "104x52 per module",
        "brightness": "1,200 nits",
        "application": "Meeting rooms, lobbies, digital signage, video walls",
        "key_specs": [
            {"label": "Module Size", "value": "320x160mm"},
            {"label": "Pixel Config", "value": "SMD2121"},
            {"label": "Aging Test", "value": "72hr Continuous"},
            {"label": "Refresh Rate", "value": "3,840Hz"},
        ],
    },
    {
        "product_code": "BL-CRC400",
        "name": "Circular Round LED P4",
        "category": "sphere",
        "tagline": "360-Degree Circular Display",
        "description": "P4 indoor circular round LED display module screen. 64x64 resolution with 62,500 dots/sqm pixel density. Perfect for museums, exhibitions, and unique architectural features.",
        "pixel_pitch": "4mm",
        "resolution": "64x64",
        "brightness": "1,500 nits",
        "application": "Museums, exhibitions, retail centerpieces, architectural features",
        "key_specs": [
            {"label": "Pixel Density", "value": "62,500 dots/sqm"},
            {"label": "Shape", "value": "Circular / Round"},
            {"label": "Module Res", "value": "64x64"},
            {"label": "Service", "value": "Front / Rear"},
        ],
    },
    # Outdoor modern pitches (replacing old DIP modules)
    {
        "product_code": "BL-OR391",
        "name": "Outdoor Rental P3.91",
        "category": "rental",
        "tagline": "HD Outdoor Rental Solution",
        "description": "P3.91mm outdoor high-definition rental LED display module, 250x250mm size, fits 500x500mm and 500x1000mm die-cast rental screen cabinets. IP65 rated for all-weather outdoor events.",
        "pixel_pitch": "3.91mm",
        "resolution": "64x64 per module",
        "brightness": "5,500 nits",
        "application": "Outdoor concerts, festivals, sporting events, temporary installations",
        "key_specs": [
            {"label": "Module Size", "value": "250x250mm"},
            {"label": "Cabinet", "value": "500x500 / 500x1000mm"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Brightness", "value": "5,500 nits"},
        ],
    },
    {
        "product_code": "BL-OP4HD",
        "name": "Outdoor HD P4 Advertising",
        "category": "outdoor",
        "tagline": "Ultra HD Outdoor Advertising Display",
        "description": "Outdoor P4 1/8 scan SMD2525 64x32 dot 256x128mm HD LED display screen module. Fine image performance for high-end outdoor advertising and digital billboards.",
        "pixel_pitch": "4mm",
        "resolution": "64x32 per module",
        "brightness": "6,500 nits",
        "application": "Digital billboards, highway signage, building facades, outdoor advertising",
        "key_specs": [
            {"label": "Module Size", "value": "256x128mm"},
            {"label": "Scan Mode", "value": "1/8 Scan"},
            {"label": "Pixel Config", "value": "SMD2525"},
            {"label": "IP Rating", "value": "IP65"},
        ],
    },
    {
        "product_code": "BL-OP5SMD",
        "name": "Outdoor SMD P5 Billboard",
        "category": "outdoor",
        "tagline": "Cost-Effective Outdoor Billboard",
        "description": "Outdoor P5 SMD2525 320x160mm LED screen module. Cost-effective outdoor HD display with fine image performance. Industry workhorse for outdoor fixed installations.",
        "pixel_pitch": "5mm",
        "resolution": "64x32 per module",
        "brightness": "6,000 nits",
        "application": "Outdoor billboards, shopping centers, building wraps, gas stations",
        "key_specs": [
            {"label": "Module Size", "value": "320x160mm"},
            {"label": "Pixel Config", "value": "SMD2525"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Lifespan", "value": "100,000 hrs"},
        ],
    },
    {
        "product_code": "BL-OP667",
        "name": "Outdoor P6.67 Nationstar",
        "category": "outdoor",
        "tagline": "Premium Outdoor Signage",
        "description": "P6.67mm outdoor Nationstar SMD LED display screen module 320x160mm IP67. Premium outdoor solution for rental LED screens and fixed installation displays with superior weatherproofing.",
        "pixel_pitch": "6.67mm",
        "resolution": "48x24 per module",
        "brightness": "7,000 nits",
        "application": "Highway billboards, large-format outdoor signage, stadium perimeters",
        "key_specs": [
            {"label": "Module Size", "value": "320x160mm"},
            {"label": "LED Brand", "value": "Nationstar"},
            {"label": "IP Rating", "value": "IP67"},
            {"label": "Brightness", "value": "7,000 nits"},
        ],
    },
    # Flexible modules from their website
    {
        "product_code": "BL-SF150",
        "name": "Soft Flex P1.5 Module",
        "category": "flexible",
        "tagline": "Ultra-Fine Flexible LED",
        "description": "P1.5 indoor soft flexible LED display module designed for creative LED screen applications. Ultra-flexible with magnetic backside design, fits any curved surface for round and custom shape video walls.",
        "pixel_pitch": "1.5mm",
        "resolution": "160x80 per module",
        "brightness": "1,000 nits",
        "application": "Curved columns, cylindrical displays, creative retail, art installations",
        "key_specs": [
            {"label": "Module Size", "value": "240x120mm"},
            {"label": "Flexibility", "value": "Ultra-Flex Magnetic"},
            {"label": "Service", "value": "Front / Magnetic"},
            {"label": "Min Curve", "value": "Radius 300mm"},
        ],
    },
    {
        "product_code": "BL-SF400",
        "name": "Soft Flex P4 Creative Module",
        "category": "flexible",
        "tagline": "Creative Shape LED Module",
        "description": "P4 indoor soft flexible LED display module for creative LED screen applications. Designed for rolling, bending, and swing installations with magnetic backside mount.",
        "pixel_pitch": "4mm",
        "resolution": "64x32 per module",
        "brightness": "1,500 nits",
        "application": "Creative installations, curved walls, cylindrical columns, stage backdrops",
        "key_specs": [
            {"label": "Module Size", "value": "256x128mm"},
            {"label": "Flexibility", "value": "Roll / Bend / Swing"},
            {"label": "Service", "value": "Magnetic Front"},
            {"label": "Weight", "value": "Ultra-light"},
        ],
    },
    # Road Signal (new category from their website)
    {
        "product_code": "BL-RSL250",
        "name": "Road Signal LED P2.5",
        "category": "road-signal",
        "tagline": "Highway & Traffic Signage",
        "description": "Road signal LED display for highway messaging, overhead traffic signs, and tollbooth queuing. High-brightness, weather-resistant display with auto-brightness adjustment for day/night visibility.",
        "pixel_pitch": "2.5mm",
        "resolution": "Custom modular",
        "brightness": "8,000 nits",
        "application": "Highway messaging, traffic management, toll booths, variable message signs",
        "key_specs": [
            {"label": "IP Rating", "value": "IP68"},
            {"label": "Brightness", "value": "8,000 nits auto-dim"},
            {"label": "Viewing Distance", "value": "50-300m"},
            {"label": "Operating Temp", "value": "-40°C to +60°C"},
        ],
    },
    {
        "product_code": "BL-RSL400",
        "name": "Road Signal LED P4",
        "category": "road-signal",
        "tagline": "Variable Message Traffic Display",
        "description": "P4 road signal LED display for variable message signs (VMS), speed limit indicators, and toll plaza information. Built for 24/7 operation in extreme weather conditions.",
        "pixel_pitch": "4mm",
        "resolution": "Custom modular",
        "brightness": "7,500 nits",
        "application": "Variable message signs, speed displays, parking guidance, intersection alerts",
        "key_specs": [
            {"label": "IP Rating", "value": "IP68"},
            {"label": "Operation", "value": "24/7 Continuous"},
            {"label": "Certification", "value": "Traffic Safety Compliant"},
            {"label": "Power", "value": "Low consumption, solar compatible"},
        ],
    },
    # Modern trending products (2025-2026 market demands)
    {
        "product_code": "BL-COB040",
        "name": "COB MicroLED 0.4mm",
        "category": "cob-microled",
        "tagline": "Next-Gen Ultra-Fine Pixel",
        "description": "0.4mm COB MicroLED display module with flip-chip technology. The finest pixel pitch in the Brightluxx lineup, delivering 8K+ resolution for mission-critical control rooms and luxury installations.",
        "pixel_pitch": "0.4mm",
        "resolution": "600x337 per module",
        "brightness": "600 nits",
        "application": "Control rooms, broadcast studios, luxury residences, command centers",
        "key_specs": [
            {"label": "Technology", "value": "Flip-Chip COB"},
            {"label": "Contrast", "value": "20,000:1"},
            {"label": "Lifespan", "value": "150,000 hrs"},
            {"label": "Viewing Angle", "value": "170°/170°"},
        ],
    },
    {
        "product_code": "BL-IP18",
        "name": "IndoorPro P1.8 Fine Pitch",
        "category": "indoor",
        "tagline": "Premium Fine Pitch Indoor",
        "description": "P1.8 fine-pitch indoor LED display module for enterprise and corporate environments. High refresh rate and wide color gamut for demanding video wall applications.",
        "pixel_pitch": "1.8mm",
        "resolution": "160x90 per module",
        "brightness": "800 nits",
        "application": "Corporate lobbies, boardrooms, retail flagships, hospitality",
        "key_specs": [
            {"label": "Module Size", "value": "288x162mm"},
            {"label": "Refresh Rate", "value": "7,680Hz"},
            {"label": "Color Gamut", "value": "Wide NTSC"},
            {"label": "HDR", "value": "Supported"},
        ],
    },
    # Clear Film Screen (from their homepage - latest tech)
    {
        "product_code": "BL-CLR120",
        "name": "ClearFilm LED Screen",
        "category": "transparent",
        "tagline": "Thinnest LED Display in the World",
        "description": "Revolutionary clear film LED screen with just 1.2mm thickness and 0.3kg weight per panel. The latest transparent LED technology enabling see-through digital displays on any glass surface.",
        "pixel_pitch": "2mm",
        "resolution": "Custom",
        "brightness": "3,500 nits",
        "application": "Glass facades, retail windows, museum exhibits, automotive showrooms",
        "key_specs": [
            {"label": "Thickness", "value": "1.2mm"},
            {"label": "Weight", "value": "0.3 kg/panel"},
            {"label": "Transparency", "value": "95%"},
            {"label": "Installation", "value": "Adhesive / Glass Mount"},
        ],
    },
    # Floor LED (from their homepage)
    {
        "product_code": "BL-FLR391",
        "name": "InteractiveFloor 3D P3.91",
        "category": "interactive",
        "tagline": "3D Interactive Floor Display",
        "description": "P3.91 3D interactive LED floor display with pressure-sensitive interaction and real-time motion tracking. Creates immersive ground-level visual experiences for retail, events, and exhibitions.",
        "pixel_pitch": "3.91mm",
        "resolution": "128x128 per panel",
        "brightness": "2,000 nits",
        "application": "Shopping malls, exhibitions, events, entertainment venues, museums",
        "key_specs": [
            {"label": "Load Bearing", "value": "2,000 kg/sqm"},
            {"label": "Interaction", "value": "Pressure + Motion"},
            {"label": "IP Rating", "value": "IP54"},
            {"label": "Surface", "value": "Anti-slip tempered glass"},
        ],
    },
]


def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text


async def main():
    # ─── Add real projects ───
    print("=== Adding Real Projects ===")
    # Remove only the old fictional projects (keep Test Project as it may be from testing)
    fictional_titles = [
        "Dubai Mall Digital Atrium",
        "Sheikh Zayed Road DOOH Network",
        "ADNOC HQ Command Centre",
        "Atlantis The Royal Grand Ballroom",
        "Riyadh Season Main Stage",
        "Mall of the Emirates Glass Facade",
        "DIFC Luxury VIP Lounge",
        "Abu Dhabi Expo Interactive Pavilion",
    ]
    del_result = await db.projects.delete_many({"title": {"$in": fictional_titles}})
    print(f"  Removed {del_result.deleted_count} fictional projects")

    added_projects = 0
    for p in REAL_PROJECTS:
        existing = await db.projects.find_one({"title": p["title"]})
        if existing:
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "title": p["title"],
            "slug": slugify(p["title"]),
            "client_name": p["client_name"],
            "location": p["location"],
            "sector": p["sector"],
            "screen_size": p["screen_size"],
            "description": p["description"],
            "image_url": "",
            "gallery": [],
            "technologies_used": p["technologies_used"],
            "metrics": [],
            "featured": p.get("featured", False),
            "status": "published",
            "created_at": datetime.now(timezone.utc),
        }
        await db.projects.insert_one(doc)
        added_projects += 1
    print(f"  Added {added_projects} real projects")

    # ─── Add new products ───
    print("\n=== Adding New Products ===")
    added_products = 0
    for p in NEW_PRODUCTS:
        existing = await db.products.find_one({"product_code": p["product_code"]})
        if existing:
            print(f"  Skipping {p['product_code']} (exists)")
            continue
        doc = {
            "id": str(uuid.uuid4()),
            "product_code": p["product_code"],
            "name": p["name"],
            "slug": slugify(p["name"]),
            "category": p["category"],
            "tagline": p["tagline"],
            "description": p["description"],
            "pixel_pitch": p["pixel_pitch"],
            "resolution": p["resolution"],
            "brightness": p["brightness"],
            "application": p["application"],
            "key_specs": p["key_specs"],
            "image_url": "",
            "gallery": [],
            "featured": False,
            "trending": False,
            "new_arrival": True,
            "status": "published",
            "created_at": datetime.now(timezone.utc),
        }
        await db.products.insert_one(doc)
        added_products += 1
    print(f"  Added {added_products} new products")

    # Print totals
    total_products = await db.products.count_documents({})
    total_projects = await db.projects.count_documents({})
    print(f"\n=== Totals ===")
    print(f"  Products: {total_products}")
    print(f"  Projects: {total_projects}")


asyncio.run(main())
