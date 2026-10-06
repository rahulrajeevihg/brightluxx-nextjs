"""Seed new product categories: Accessories, Custom LED Shapes, Digital Signage, Smart TVs, Ready-Made Products."""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

NEW_PRODUCTS = [
    # Accessories
    {
        "name": "NovaStar MCTRL4K Controller",
        "slug": "novastar-mctrl4k-controller",
        "product_code": "BL-ACC-NS4K",
        "category": "accessories",
        "pixel_pitch": "N/A",
        "brightness": "N/A",
        "tagline": "Professional 4K video controller. Seamless switching and processing.",
        "application": "Video processing and control for large LED displays, video walls, and multi-screen setups.",
        "key_specs": [
            {"label": "Resolution", "value": "4K@60Hz"},
            {"label": "Outputs", "value": "16x Ethernet"},
            {"label": "Inputs", "value": "HDMI 2.0, DP 1.2, DVI"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "Colorlight Z6 Media Server",
        "slug": "colorlight-z6-media-server",
        "product_code": "BL-ACC-CLZ6",
        "category": "accessories",
        "pixel_pitch": "N/A",
        "brightness": "N/A",
        "tagline": "All-in-one media playback and LED control. Cloud-managed.",
        "application": "Content scheduling, playback, and LED display management for digital signage and advertising.",
        "key_specs": [
            {"label": "Output", "value": "4K@60Hz"},
            {"label": "Storage", "value": "128GB SSD"},
            {"label": "Network", "value": "WiFi + 4G + LAN"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "LED Power Supply Unit 200W",
        "slug": "led-power-supply-200w",
        "product_code": "BL-ACC-PSU200",
        "category": "accessories",
        "pixel_pitch": "N/A",
        "brightness": "N/A",
        "tagline": "Industrial-grade 200W power supply. Wide voltage range for UAE installations.",
        "application": "Power supply for indoor LED displays and modules. 110-240V input, multiple DC outputs.",
        "key_specs": [
            {"label": "Power", "value": "200W"},
            {"label": "Input", "value": "110-240V AC"},
            {"label": "Efficiency", "value": "93%"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "Mounting Bracket Kit — Wall Mount",
        "slug": "mounting-bracket-wall",
        "product_code": "BL-ACC-WMK",
        "category": "accessories",
        "pixel_pitch": "N/A",
        "brightness": "N/A",
        "tagline": "Universal wall mounting system. Quick-lock design for fast installation.",
        "application": "Wall mounting brackets and rails for indoor LED cabinets. Adjustable alignment.",
        "key_specs": [
            {"label": "Load", "value": "Up to 80kg/m"},
            {"label": "Material", "value": "Galvanized Steel"},
            {"label": "Adjustment", "value": "3-axis"}
        ],
        "image_url": "",
        "featured": False,
    },

    # Custom LED Shapes
    {
        "name": "Round LED Display P2.5",
        "slug": "round-led-display-p25",
        "product_code": "BL-CUS-RND25",
        "category": "custom-shapes",
        "pixel_pitch": "2.5mm",
        "brightness": "1,200 nits",
        "tagline": "Circular LED module. Perfect for lobbies, retail, and architectural features.",
        "application": "Circular and round LED displays for lobby ceilings, retail window displays, museum installations, and architectural centerpieces.",
        "key_specs": [
            {"label": "Shape", "value": "Circular"},
            {"label": "Diameter", "value": "500-3000mm"},
            {"label": "Pixel Pitch", "value": "2.5mm"}
        ],
        "image_url": "",
        "featured": True,
    },
    {
        "name": "Cube LED Display P3",
        "slug": "cube-led-display-p3",
        "product_code": "BL-CUS-CUBE3",
        "category": "custom-shapes",
        "pixel_pitch": "3mm",
        "brightness": "1,500 nits",
        "tagline": "6-sided LED cube. Eye-catching centerpiece for exhibitions and retail.",
        "application": "Suspended or freestanding LED cubes for retail, exhibitions, and events. Fully programmable on all 6 faces.",
        "key_specs": [
            {"label": "Shape", "value": "Cube (6 sides)"},
            {"label": "Size", "value": "500-1500mm per side"},
            {"label": "Pixel Pitch", "value": "3mm"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "Cone LED Display P4",
        "slug": "cone-led-display-p4",
        "product_code": "BL-CUS-CONE4",
        "category": "custom-shapes",
        "pixel_pitch": "4mm",
        "brightness": "1,800 nits",
        "tagline": "Conical LED structure. Architectural landmark for malls and public spaces.",
        "application": "Custom cone and pyramid LED structures for mall atriums, public art installations, and event centerpieces.",
        "key_specs": [
            {"label": "Shape", "value": "Cone / Pyramid"},
            {"label": "Height", "value": "1-5 meters"},
            {"label": "Pixel Pitch", "value": "4mm"}
        ],
        "image_url": "",
        "featured": False,
    },

    # Digital Signage
    {
        "name": "Digital Signage Pro 55\" 4K",
        "slug": "digital-signage-pro-55",
        "product_code": "BL-DS-55PRO",
        "category": "digital-signage",
        "pixel_pitch": "N/A",
        "brightness": "700 nits",
        "tagline": "Commercial-grade 55\" display. 24/7 operation. Built-in CMS.",
        "application": "Indoor digital signage for retail, corporate, hospitality, and healthcare. Built-in content management.",
        "key_specs": [
            {"label": "Size", "value": "55 inch"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Operation", "value": "24/7"}
        ],
        "image_url": "",
        "featured": True,
    },
    {
        "name": "Digital Signage Outdoor 75\" IP65",
        "slug": "digital-signage-outdoor-75",
        "product_code": "BL-DS-75OUT",
        "category": "digital-signage",
        "pixel_pitch": "N/A",
        "brightness": "3,000 nits",
        "tagline": "Outdoor-rated 75\" display. IP65 weatherproof. Sunlight-readable.",
        "application": "Outdoor digital signage for storefronts, parks, transport hubs. Withstands rain, dust, and direct sunlight.",
        "key_specs": [
            {"label": "Size", "value": "75 inch"},
            {"label": "Protection", "value": "IP65"},
            {"label": "Brightness", "value": "3,000 nits"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "Digital Kiosk Interactive 43\"",
        "slug": "digital-kiosk-interactive-43",
        "product_code": "BL-DS-KSK43",
        "category": "digital-signage",
        "pixel_pitch": "N/A",
        "brightness": "500 nits",
        "tagline": "Freestanding interactive kiosk. Touchscreen with wayfinding and menu boards.",
        "application": "Self-service kiosks for malls, airports, hotels, and restaurants. Touchscreen wayfinding and information.",
        "key_specs": [
            {"label": "Size", "value": "43 inch"},
            {"label": "Touch", "value": "10-point capacitive"},
            {"label": "OS", "value": "Android / Windows"}
        ],
        "image_url": "",
        "featured": False,
    },

    # Smart TVs
    {
        "name": "Commercial Smart TV 85\" 4K",
        "slug": "commercial-smart-tv-85",
        "product_code": "BL-TV-85COM",
        "category": "smart-tv",
        "pixel_pitch": "N/A",
        "brightness": "500 nits",
        "tagline": "Commercial-grade 85\" Smart TV. Built for boardrooms and luxury residences.",
        "application": "Large-format smart TV for corporate boardrooms, luxury villas, and hospitality suites.",
        "key_specs": [
            {"label": "Size", "value": "85 inch"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Smart OS", "value": "Android TV"}
        ],
        "image_url": "",
        "featured": True,
    },
    {
        "name": "Outdoor Smart TV 65\" IP55",
        "slug": "outdoor-smart-tv-65",
        "product_code": "BL-TV-65OUT",
        "category": "smart-tv",
        "pixel_pitch": "N/A",
        "brightness": "2,500 nits",
        "tagline": "Weatherproof outdoor Smart TV. Perfect for villas, pools, and terraces.",
        "application": "Outdoor entertainment TV for luxury villas, pool areas, rooftop terraces, and yacht decks.",
        "key_specs": [
            {"label": "Size", "value": "65 inch"},
            {"label": "Protection", "value": "IP55"},
            {"label": "Brightness", "value": "2,500 nits"}
        ],
        "image_url": "",
        "featured": False,
    },

    # Ready-Made Products
    {
        "name": "Plug & Play Video Wall 2x2 P1.5",
        "slug": "plug-play-videowall-2x2",
        "product_code": "BL-RDY-VW22",
        "category": "ready-made",
        "pixel_pitch": "1.5mm",
        "brightness": "600 nits",
        "tagline": "Pre-configured 2x2 video wall. Unbox, mount, and display in under 2 hours.",
        "application": "Turnkey video wall for corporate lobbies, meeting rooms, and retail. Zero configuration needed.",
        "key_specs": [
            {"label": "Config", "value": "2x2 (4 panels)"},
            {"label": "Total Size", "value": "~110 inch"},
            {"label": "Setup Time", "value": "Under 2 hours"}
        ],
        "image_url": "",
        "featured": True,
    },
    {
        "name": "Portable LED Stand P2.5",
        "slug": "portable-led-stand-p25",
        "product_code": "BL-RDY-PRT25",
        "category": "ready-made",
        "pixel_pitch": "2.5mm",
        "brightness": "1,000 nits",
        "tagline": "Portable LED poster with wheeled stand. Ideal for events and retail.",
        "application": "Mobile LED display for trade shows, events, retail promotions, and temporary installations. Battery option available.",
        "key_specs": [
            {"label": "Size", "value": "1920x640mm"},
            {"label": "Weight", "value": "28kg with stand"},
            {"label": "Setup", "value": "5 minutes"}
        ],
        "image_url": "",
        "featured": False,
    },
    {
        "name": "Meeting Room LED All-in-One 136\"",
        "slug": "meeting-room-led-136",
        "product_code": "BL-RDY-MTG136",
        "category": "ready-made",
        "pixel_pitch": "1.5mm",
        "brightness": "600 nits",
        "tagline": "Drop-in replacement for projectors. 136\" 4K LED. Plug and play.",
        "application": "Complete meeting room solution replacing projectors. 136 inch seamless LED display with built-in audio and conferencing.",
        "key_specs": [
            {"label": "Size", "value": "136 inch diagonal"},
            {"label": "Resolution", "value": "4K UHD"},
            {"label": "Audio", "value": "Built-in 40W"}
        ],
        "image_url": "",
        "featured": False,
    },
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["products"]

    added = 0
    for p in NEW_PRODUCTS:
        exists = await col.find_one({"slug": p["slug"]})
        if not exists:
            await col.insert_one(p)
            added += 1
            print(f"  Added: {p['name']} ({p['category']})")
        else:
            print(f"  Exists: {p['name']}")

    print(f"\nDone: {added} new products added.")
    total = await col.count_documents({})
    cats = await col.distinct("category")
    print(f"Total products: {total}, Categories: {len(cats)}")
    print(f"Categories: {sorted(cats)}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
