"""
CMS Data Seeder - Populates the database with static content from the frontend
Run this script to migrate all hardcoded frontend data to dynamic CMS collections.
"""
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ============ PIXELVUE PRODUCTS DATA ============
PIXELVUE_PRODUCTS = [
    # LED Poster Series
    {
        "name": "iPoster",
        "slug": "iposter",
        "category": "poster",
        "tagline": "Seamless Splicing. Stunning Impact.",
        "description": "Advanced indoor moveable digital signage with seamless 16:9 splicing capability. Ultra-slim 40mm profile, magnetic assembly, and flexible control options make iPoster the perfect choice for any environment.",
        "hero_image": "https://files.ihgbrands.com/emergent-images/74f81d159d7f59d83970b8e2a9edd0b1e5d2ebc4d70495f5578fdee1a9875f37.png",
        "quick_specs": [
            {"label": "Thickness", "value": "40mm"},
            {"label": "Weight", "value": "69kg"},
            {"label": "Splicing Ratio", "value": "16:9"},
            {"label": "Refresh Rate", "value": "3840Hz"}
        ],
        "features": [
            {"icon": "Grid3X3", "title": "Seamless Splicing", "desc": "5-piece iPoster with 16:9 resolution ratio creates flawless, cohesive video walls."},
            {"icon": "Layers", "title": "Ultra-Slim Design", "desc": "Only 40mm thick and 69kg weight for easy transport and placement."},
            {"icon": "Monitor", "title": "High Performance", "desc": "High brightness, contrast, and 3840Hz refresh rate for stunning visuals."},
            {"icon": "Wifi", "title": "Easy Control", "desc": "USB, HDMI, WiFi for local control. Optional 4G for remote access."},
            {"icon": "Zap", "title": "Magnetic Assembly", "desc": "Precision magnetic frames for quick, tool-free setup and seamless alignment."},
            {"icon": "Smartphone", "title": "Flexible Packaging", "desc": "Flight case or nylon bag options. 1-in-1, 2-in-1, or 4-in-1 configurations."}
        ],
        "applications": [
            {"name": "Hotels & Lobbies", "desc": ""},
            {"name": "Shopping Malls", "desc": ""},
            {"name": "Reception Areas", "desc": ""},
            {"name": "Retail Stores", "desc": ""},
            {"name": "Exhibition Halls", "desc": ""},
            {"name": "Airports", "desc": ""},
            {"name": "Banks", "desc": ""},
            {"name": "Restaurants", "desc": ""}
        ],
        "specifications": [
            {"label": "Pixel Pitch", "value": "P2.5 / P3"},
            {"label": "Resolution", "value": "192x768 / 160x640"},
            {"label": "Brightness", "value": "1000-1500 cd/m²"},
            {"label": "Refresh Rate", "value": "3840Hz"},
            {"label": "Viewing Angle", "value": "160°"},
            {"label": "Contrast", "value": "5000:1"},
            {"label": "Dimensions", "value": "480x1920x40mm"},
            {"label": "Weight", "value": "69kg"},
            {"label": "Frame Material", "value": "Aluminum alloy"},
            {"label": "Input", "value": "USB, HDMI, WiFi, 4G"},
            {"label": "Power", "value": "200W max"},
            {"label": "Lifespan", "value": "100,000 hours"}
        ],
        "faqs": [
            {"question": "How many iPoster units can be spliced together?", "answer": "iPoster supports unlimited splicing thanks to its magnetic frame design. Common configurations include 5-panel video walls (16:9 ratio), but larger installations are easily achievable."},
            {"question": "What content formats are supported?", "answer": "iPoster supports all major video and image formats. Content can be loaded via USB drive, HDMI input, WiFi transfer, or optional 4G remote transmission."},
            {"question": "How portable is the iPoster?", "answer": "At 40mm thin and 69kg, iPoster is designed for mobility. It comes with flight case or nylon bag packaging options, making it ideal for events and temporary installations."},
            {"question": "What is the pixel pitch?", "answer": "iPoster is available in P2.5 and P3 pixel pitch options. P2.5 is recommended for closer viewing distances (2-5m), while P3 works well for larger spaces."}
        ],
        "seo_title": "iPoster - Indoor LED Standee Display | PixelVue",
        "seo_description": "Advanced indoor LED poster with seamless splicing, 40mm thin design, and easy WiFi/HDMI control. Perfect for hotels, retail, and exhibitions.",
        "is_active": True,
        "order": 1
    },
    {
        "name": "iFlip",
        "slug": "iflip",
        "category": "poster",
        "tagline": "Double-Sided LED. Double the Impact.",
        "description": "Revolutionary double-sided LED poster display with seamless rotation capability. Show different content on each side or mirror for maximum exposure in high-traffic areas.",
        "hero_image": "https://static.prod-images.emergentagent.com/jobs/a2ffd883-d4cb-4f8a-b10e-28b67c771781/images/iflip-hero.png",
        "quick_specs": [
            {"label": "Sides", "value": "Double"},
            {"label": "Profile", "value": "65mm"},
            {"label": "Brightness", "value": "2500nits"},
            {"label": "Refresh", "value": "3840Hz"}
        ],
        "features": [
            {"icon": "RotateCcw", "title": "Double-Sided Display", "desc": "Two full LED screens back-to-back for 360° visibility in any space."},
            {"icon": "Layers", "title": "Slim Profile", "desc": "65mm total thickness houses two complete display systems."},
            {"icon": "Sun", "title": "High Brightness", "desc": "2500 nits ensures visibility even in bright ambient lighting."},
            {"icon": "Wifi", "title": "Wireless Control", "desc": "WiFi and 4G connectivity for remote content management."}
        ],
        "applications": [{"name": "Shopping Malls", "desc": ""}, {"name": "Airport Terminals", "desc": ""}, {"name": "Train Stations", "desc": ""}, {"name": "Exhibition Centers", "desc": ""}, {"name": "Retail Stores", "desc": ""}],
        "specifications": [{"label": "Pixel Pitch", "value": "P2.5 / P3"}, {"label": "Brightness", "value": "2500 cd/m²"}, {"label": "Refresh Rate", "value": "3840Hz"}, {"label": "Viewing Angle", "value": "160°"}, {"label": "Thickness", "value": "65mm"}, {"label": "Lifespan", "value": "100,000 hours"}],
        "faqs": [{"question": "Can I show different content on each side?", "answer": "Yes, iFlip supports independent content on each side, or you can mirror the same content for consistent branding."}, {"question": "Is it suitable for outdoor use?", "answer": "iFlip is primarily designed for indoor high-traffic areas. For outdoor use, consider our OOH Poster series."}],
        "is_active": True, "order": 2
    },
    {"name": "UltraFlip", "slug": "ultra-flip", "category": "poster", "tagline": "Ultra-Thin Double-Sided Excellence.", "description": "The thinnest double-sided LED display in its class.", "hero_image": "", "quick_specs": [{"label": "Profile", "value": "45mm"}, {"label": "Weight", "value": "35kg"}, {"label": "Brightness", "value": "2000nits"}, {"label": "Pixel Pitch", "value": "P2.0"}], "features": [{"icon": "Layers", "title": "Ultra-Thin", "desc": "Industry-leading 45mm profile."}, {"icon": "Zap", "title": "Lightweight", "desc": "Only 35kg makes it easy to install."}, {"icon": "Monitor", "title": "Fine Pixel Pitch", "desc": "P2.0 for exceptional clarity."}], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 3},
    {"name": "DigiStandee", "slug": "digi-standee", "category": "poster", "tagline": "Smart Digital Standee. Instant Attention.", "description": "Modern digital standee for quick deployment.", "hero_image": "", "quick_specs": [{"label": "Setup Time", "value": "5 min"}, {"label": "Battery", "value": "8 hours"}, {"label": "Weight", "value": "25kg"}, {"label": "Pixel Pitch", "value": "P2.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 4},
    {"name": "OOH Poster", "slug": "ooh-poster", "category": "poster", "tagline": "Outdoor Excellence. Weather-Proof Impact.", "description": "High-brightness outdoor LED poster for DOOH.", "hero_image": "", "quick_specs": [{"label": "Brightness", "value": "5000nits"}, {"label": "IP Rating", "value": "IP65"}, {"label": "Operating Temp", "value": "-20°C to 50°C"}, {"label": "Pixel Pitch", "value": "P4"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 5},
    {"name": "Eagle Wing", "slug": "eagle-wing", "category": "poster", "tagline": "Spread Your Message. Unfold Your Brand.", "description": "Innovative foldable LED display.", "hero_image": "", "quick_specs": [{"label": "Expansion", "value": "3x Width"}, {"label": "Mechanism", "value": "Motorized"}, {"label": "Max Size", "value": "6m span"}, {"label": "Pixel Pitch", "value": "P2.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 6},
    # Commercial Series
    {"name": "Unity", "slug": "unity", "category": "commercial", "tagline": "Modular Excellence. Unified Vision.", "description": "Versatile modular LED for flat, curved, and column installations.", "hero_image": "", "quick_specs": [{"label": "Panel Size", "value": "1000x250mm"}, {"label": "Curve", "value": "90° Column"}, {"label": "Clearance", "value": "15cm rear"}, {"label": "Maintenance", "value": "Front & Rear"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 7},
    {"name": "VideoBrick", "slug": "videobrick", "category": "commercial", "tagline": "Build Your Vision. Brick by Brick.", "description": "Stackable LED modules that snap together.", "hero_image": "", "quick_specs": [{"label": "Module", "value": "500x500mm"}, {"label": "Assembly", "value": "Magnetic"}, {"label": "Max Size", "value": "Unlimited"}, {"label": "Pixel Pitch", "value": "P1.5-P4"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 8},
    {"name": "iConference", "slug": "iconference", "category": "commercial", "tagline": "Professional Display. Perfect Meetings.", "description": "All-in-one LED conference display.", "hero_image": "", "quick_specs": [{"label": "Screen Size", "value": "138\" / 163\""}, {"label": "Camera", "value": "4K PTZ"}, {"label": "Audio", "value": "8-Mic Array"}, {"label": "Pixel Pitch", "value": "P1.2 / P1.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 9},
    {"name": "EzeeSign", "slug": "ezeesign", "category": "commercial", "tagline": "Simple Setup. Stunning Results.", "description": "Plug-and-play LED signage.", "hero_image": "", "quick_specs": [{"label": "Setup", "value": "Plug & Play"}, {"label": "Software", "value": "Cloud CMS"}, {"label": "Sizes", "value": "24\" to 75\""}, {"label": "Pixel Pitch", "value": "P2.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 10},
    {"name": "iShelf", "slug": "ishelf", "category": "commercial", "tagline": "Smart Shelf. Smart Retail.", "description": "LED shelf-edge display system.", "hero_image": "", "quick_specs": [{"label": "Height", "value": "50mm"}, {"label": "Length", "value": "Custom"}, {"label": "Viewing", "value": "175°"}, {"label": "Pixel Pitch", "value": "P1.0 / P1.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 11},
    {"name": "TableVision", "slug": "tablevision", "category": "commercial", "tagline": "Interactive Tables. Engaging Experiences.", "description": "LED-embedded tables with multi-touch.", "hero_image": "", "quick_specs": [{"label": "Touch Points", "value": "40"}, {"label": "Surface", "value": "Tempered Glass"}, {"label": "Size", "value": "43\" / 55\" / 65\""}, {"label": "Pixel Pitch", "value": "P1.8"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 12},
    {"name": "iFlex Pro", "slug": "iflex-pro", "category": "commercial", "tagline": "Flex Your Creativity. Pro Results.", "description": "Professional-grade flexible LED display.", "hero_image": "", "quick_specs": [{"label": "Bend Radius", "value": "500mm min"}, {"label": "Thickness", "value": "12mm"}, {"label": "Weight", "value": "8kg/m²"}, {"label": "Pixel Pitch", "value": "P2.0-P4.0"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 13},
    {"name": "iTransformers", "slug": "itransformers", "category": "commercial", "tagline": "Transform Your Space. Adapt Instantly.", "description": "Modular transforming LED system.", "hero_image": "", "quick_specs": [{"label": "Configurations", "value": "6+"}, {"label": "Movement", "value": "Motorized"}, {"label": "Transform Time", "value": "30 sec"}, {"label": "Pixel Pitch", "value": "P2.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 14},
    {"name": "Tetris", "slug": "tetris", "category": "commercial", "tagline": "Stack. Create. Display.", "description": "Stackable LED cube modules.", "hero_image": "", "quick_specs": [{"label": "Cube Size", "value": "250mm³"}, {"label": "Sides Active", "value": "4 or 6"}, {"label": "Connection", "value": "Magnetic"}, {"label": "Pixel Pitch", "value": "P2.5"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 15},
    {"name": "Ellipse Counter", "slug": "ellipse-counter", "category": "commercial", "tagline": "Curved Elegance. Reception Excellence.", "description": "LED-integrated reception counter.", "hero_image": "", "quick_specs": [{"label": "Shape", "value": "Elliptical"}, {"label": "Display Area", "value": "Front Face"}, {"label": "Counter Top", "value": "Solid Surface"}, {"label": "Pixel Pitch", "value": "P2.0"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 16},
    # Creative Series
    {"name": "Creative Shapes", "slug": "creative-shapes", "category": "creative", "tagline": "Any Shape. Any Dream. Made Real.", "description": "Custom-shaped LED displays.", "hero_image": "", "quick_specs": [{"label": "Experience", "value": "10+ Years"}, {"label": "Shapes", "value": "Unlimited"}, {"label": "Viewing", "value": "360°"}, {"label": "Custom", "value": "100%"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 17},
    {"name": "Interactive", "slug": "interactive", "category": "creative", "tagline": "Touch. Play. Engage.", "description": "Interactive LED floor and wall displays.", "hero_image": "", "quick_specs": [{"label": "Response", "value": "<30ms"}, {"label": "Detection", "value": "Multi-Touch"}, {"label": "Load Capacity", "value": "2000kg/m²"}, {"label": "Pixel Pitch", "value": "P3.9 / P4.8"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 18},
    {"name": "CrystalFlex", "slug": "crystalflex", "category": "creative", "tagline": "Transparent Beauty. Crystal Clarity.", "description": "Flexible transparent LED.", "hero_image": "", "quick_specs": [{"label": "Transparency", "value": "85%"}, {"label": "Flexibility", "value": "Bendable"}, {"label": "Weight", "value": "6kg/m²"}, {"label": "Pixel Pitch", "value": "P10-P15"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 19},
    {"name": "Rolling Floor", "slug": "rolling-floor", "category": "creative", "tagline": "Walk on Wonder. Dance on Light.", "description": "LED floor panels for walkways and stages.", "hero_image": "", "quick_specs": [{"label": "Load Capacity", "value": "3000kg/m²"}, {"label": "IP Rating", "value": "IP65"}, {"label": "Surface", "value": "Anti-Slip"}, {"label": "Pixel Pitch", "value": "P3.9 / P6.25"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 20},
    {"name": "MagicStage", "slug": "magicstage", "category": "creative", "tagline": "Stage. Screen. Spectacle.", "description": "Complete stage LED solution.", "hero_image": "", "quick_specs": [{"label": "Coverage", "value": "360°"}, {"label": "Components", "value": "Floor + Wall + Ceiling"}, {"label": "Rental Ready", "value": "Yes"}, {"label": "Pixel Pitch", "value": "P2.6-P4.8"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 21},
    {"name": "Magic Blanket", "slug": "magic-blanket", "category": "creative", "tagline": "Drape Your Space in Light.", "description": "Flexible LED mesh.", "hero_image": "", "quick_specs": [{"label": "Flexibility", "value": "Full Drape"}, {"label": "Weight", "value": "4kg/m²"}, {"label": "Transparency", "value": "70%"}, {"label": "Pixel Pitch", "value": "P15-P30"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 22},
    {"name": "MagicSky", "slug": "magicsky", "category": "creative", "tagline": "Bring the Sky Inside.", "description": "LED ceiling system.", "hero_image": "", "quick_specs": [{"label": "Installation", "value": "Ceiling"}, {"label": "Effect", "value": "Sky Simulation"}, {"label": "Control", "value": "DMX + Video"}, {"label": "Pixel Pitch", "value": "P4-P10"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 23},
    {"name": "Magic Garments", "slug": "magic-garments", "category": "creative", "tagline": "Wear Your Message. Light Up the Room.", "description": "Wearable LED solutions.", "hero_image": "", "quick_specs": [{"label": "Weight", "value": "200g/panel"}, {"label": "Power", "value": "Battery"}, {"label": "Runtime", "value": "4 hours"}, {"label": "Flexibility", "value": "Wearable"}], "features": [], "applications": [], "specifications": [], "faqs": [], "is_active": True, "order": 24}
]

# ============ SOLUTIONS DATA ============
SOLUTIONS = [
    {"title": "Retail & Hospitality", "slug": "retail", "tagline": "Transform Shopping Experiences", "description": "Elevate your retail or hospitality space with stunning LED displays.", "icon": "ShoppingBag", "hero_image": "", "features": [{"title": "Dynamic Storefronts", "description": "Attract foot traffic"}, {"title": "In-Store Experience", "description": "Guide customers"}, {"title": "Promotional Flexibility", "description": "Update content instantly"}], "benefits": [{"title": "Increased Foot Traffic", "description": "63% more attention"}, {"title": "Higher Engagement", "description": "30% more time viewing"}, {"title": "Revenue Growth", "description": "29% spending increase"}], "use_cases": ["Window Displays", "In-Store Signage", "Menu Boards", "Hotel Lobbies"], "is_active": True, "order": 1},
    {"title": "Corporate & Conference", "slug": "corporate", "tagline": "Elevate Professional Spaces", "description": "Create impressive boardrooms with seamless video wall technology.", "icon": "Briefcase", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Boardrooms", "Training Centers", "Command Centers"], "is_active": True, "order": 2},
    {"title": "Outdoor & DOOH", "slug": "outdoor", "tagline": "Dominate the Skyline", "description": "High-brightness outdoor LED solutions.", "icon": "Sun", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Billboards", "Building Facades", "Stadium Perimeter"], "is_active": True, "order": 3},
    {"title": "Events & Exhibitions", "slug": "events", "tagline": "Create Unforgettable Moments", "description": "Rental-ready LED solutions for events.", "icon": "Music", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Concert Stages", "Trade Shows", "Award Ceremonies"], "is_active": True, "order": 4},
    {"title": "Creative & Curved", "slug": "creative", "tagline": "Break the Boundaries", "description": "Custom shapes and artistic LED installations.", "icon": "Sparkles", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Architectural Features", "Art Installations", "Theme Parks"], "is_active": True, "order": 5},
    {"title": "Traffic & Road Signs", "slug": "traffic", "tagline": "Guide Safely. Inform Instantly.", "description": "Variable message signs for smart cities.", "icon": "Car", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Highway VMS", "Parking Guidance", "Speed Warnings"], "is_active": True, "order": 6},
    {"title": "Immersive & VP", "slug": "immersive", "tagline": "Step Into Another World", "description": "Virtual production stages and immersive LED rooms.", "icon": "Video", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Film Studios", "Broadcast Sets", "XR Stages"], "is_active": True, "order": 7},
    {"title": "Transparent & Glass", "slug": "transparent", "tagline": "See Through. Stand Out.", "description": "Transparent LED solutions for glass facades.", "icon": "Eye", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Retail Windows", "Glass Facades", "Showrooms"], "is_active": True, "order": 8},
    {"title": "Healthcare & Medical", "slug": "healthcare", "tagline": "Inform. Guide. Heal.", "description": "Medical-grade displays for healthcare facilities.", "icon": "Heart", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Hospital Lobbies", "Waiting Areas", "Wayfinding"], "is_active": True, "order": 9},
    {"title": "Education & Training", "slug": "education", "tagline": "Inspire Learning. Enable Discovery.", "description": "Interactive displays for education.", "icon": "GraduationCap", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Lecture Halls", "Libraries", "Campus Signage"], "is_active": True, "order": 10},
    {"title": "Sports & Stadiums", "slug": "sports", "tagline": "Amplify the Action.", "description": "Stadium-scale LED solutions.", "icon": "Trophy", "hero_image": "", "features": [], "benefits": [], "use_cases": ["Scoreboards", "Perimeter Ads", "Jumbotrons"], "is_active": True, "order": 11}
]

# ============ PRODUCT FAMILIES DATA ============
PRODUCT_FAMILIES = [
    {"name": "LumiMorph", "slug": "lumimorph", "tagline": "Where Art Meets Technology", "description": "Revolutionary texture-changing LED displays.", "hero_image": "/recovered/artmorph-assets_room-setting.jpg", "hero_video": "/artmorph-assets/grande-video.mp4", "brand_color": "cyan", "stats": [{"value": "200+", "label": "Texture Options"}, {"value": "147K", "label": "Pixels/m²"}, {"value": "5 Year", "label": "Warranty"}], "overview": "LumiMorph combines the beauty of natural textures with digital displays.", "key_features": ["Interchangeable texture covers", "Magnetic mounting", "Front-serviceable"], "products": [{"name": "Elite", "slug": "lumimorph/elite", "description": "Premium P2.6", "image": ""}, {"name": "Grande", "slug": "lumimorph/grande", "description": "Large-scale P6.2", "image": ""}, {"name": "Mini", "slug": "lumimorph/mini", "description": "Compact panels", "image": ""}], "use_cases": ["Hotel Lobbies", "Corporate Reception", "Restaurants"], "faqs": [], "is_active": True, "order": 1},
    {"name": "NaturaTex", "slug": "naturatex", "tagline": "Turn Off the Display, Turn On the Art", "description": "Nano-optical texture screens.", "hero_image": "", "brand_color": "emerald", "stats": [{"value": "5", "label": "Pixel Options"}, {"value": "600-800", "label": "cd/m²"}, {"value": "COB", "label": "Technology"}], "key_features": ["Nano-optical coating", "COB technology"], "products": [{"name": "NaturaTex", "slug": "naturatex", "description": "Texture screen", "image": ""}, {"name": "HoloVeil", "slug": "naturatex/holoveil", "description": "Transparent holographic", "image": ""}], "is_active": True, "order": 2},
    {"name": "SignaTouch", "slug": "signatouch", "tagline": "Interactive Kiosks. Elevated Experiences.", "description": "Professional-grade touch screen kiosks.", "hero_image": "", "brand_color": "amber", "stats": [{"value": "63%", "label": "More Attention"}, {"value": "47%", "label": "Brand Awareness"}, {"value": "29%", "label": "Spending Boost"}], "key_features": ["40-point IR touch", "4K UHD display"], "products": [{"name": "Touch Kiosk", "slug": "signatouch/touch-kiosk", "description": "Standard kiosk", "image": ""}, {"name": "Smart Signage", "slug": "signatouch/smart-signage", "description": "Transparent OLED", "image": ""}, {"name": "Self-Service", "slug": "signatouch/self-service", "description": "Payment-enabled", "image": ""}], "is_active": True, "order": 3},
    {"name": "GlassMorph", "slug": "glassmorph", "tagline": "Make Glass Do More", "description": "Smart glass and LED film solutions.", "hero_image": "", "brand_color": "violet", "stats": [{"value": "99%", "label": "UV Protection"}, {"value": "95%", "label": "Transparency"}, {"value": "75%", "label": "Energy Savings"}], "key_features": ["PDLC technology", "Retrofit capability"], "products": [{"name": "Smart Film", "slug": "glassmorph/smart-film", "description": "Switchable privacy", "image": ""}, {"name": "LED Film", "slug": "glassmorph/led-film", "description": "Transparent LED", "image": ""}, {"name": "Media Glass", "slug": "glassmorph/media-glass", "description": "Building-integrated", "image": ""}], "is_active": True, "order": 4},
    {"name": "PixelVue", "slug": "pixelvue", "tagline": "Illuminate Your Vision", "description": "Professional LED display solutions.", "hero_image": "", "brand_color": "rose", "stats": [{"value": "100K+", "label": "Hours Lifespan"}, {"value": "3840Hz", "label": "Refresh Rate"}, {"value": "160°", "label": "Viewing Angle"}], "key_features": ["24 product options", "3 categories"], "categories": [{"name": "LED Poster Series", "slug": "poster", "count": 6}, {"name": "Commercial Series", "slug": "commercial", "count": 10}, {"name": "Creative Series", "slug": "creative", "count": 8}], "is_active": True, "order": 5}
]

async def seed_collection(collection_name, data):
    """Seed a collection with data, clearing existing data first"""
    collection = db[collection_name]
    result = await collection.delete_many({})
    print(f"Cleared {result.deleted_count} existing records from {collection_name}")
    now = datetime.now(timezone.utc).isoformat()
    for item in data:
        item["created_at"] = now
        item["updated_at"] = now
    if data:
        result = await collection.insert_many(data)
        print(f"Inserted {len(result.inserted_ids)} records into {collection_name}")
    else:
        print(f"No data to insert into {collection_name}")

# ============ TECHNOLOGIES DATA ============
TECHNOLOGIES = [
    {"name": "COB (Chip-on-Board)", "slug": "cob", "tagline": "Next-Generation LED Technology", "description": "Chip-on-Board technology offers superior image quality with better contrast, wider viewing angles, and improved durability compared to traditional SMD.", "icon": "Cpu", "features": ["Higher contrast ratio", "Wider viewing angles", "Better color uniformity", "Enhanced durability"], "benefits": ["No dead pixels", "Surface protection", "Easy maintenance"], "is_active": True, "order": 1},
    {"name": "SMD (Surface Mount)", "slug": "smd", "tagline": "Proven LED Technology", "description": "Surface Mount Device LEDs offer excellent brightness and reliability for most commercial applications.", "icon": "Layers", "features": ["High brightness", "Cost-effective", "Wide availability"], "is_active": True, "order": 2},
    {"name": "Transparent LED", "slug": "transparent", "tagline": "See-Through Display Technology", "description": "Transparent LED technology maintains up to 95% transparency while displaying vivid content.", "icon": "Eye", "features": ["High transparency", "Natural light preservation", "Architectural integration"], "is_active": True, "order": 3},
    {"name": "Flexible LED", "slug": "flexible", "tagline": "Bendable Display Solutions", "description": "Flexible LED modules can conform to curved surfaces and creative installations.", "icon": "Wind", "features": ["Curved surfaces", "Creative shapes", "Lightweight design"], "is_active": True, "order": 4},
    {"name": "MicroLED", "slug": "microled", "tagline": "Ultimate Visual Experience", "description": "MicroLED delivers unmatched brightness, contrast, and energy efficiency for premium installations.", "icon": "Sparkles", "features": ["Self-emissive pixels", "Perfect blacks", "Infinite contrast"], "is_active": True, "order": 5},
    {"name": "Interactive Touch", "slug": "interactive", "tagline": "Engage Through Touch", "description": "Multi-touch interactive technology enables engaging user experiences on LED displays.", "icon": "Hand", "features": ["40+ touch points", "IR detection", "Gesture recognition"], "is_active": True, "order": 6}
]

# ============ APPLICATIONS DATA ============
APPLICATIONS = [
    {"name": "Retail Signage", "slug": "retail-signage", "description": "Dynamic displays for stores, malls, and shopping centers.", "icon": "ShoppingBag", "use_cases": ["Window displays", "In-store promotion", "Price displays"], "is_active": True, "order": 1},
    {"name": "Corporate AV", "slug": "corporate-av", "description": "Professional display solutions for boardrooms and offices.", "icon": "Briefcase", "use_cases": ["Video conferencing", "Presentations", "Lobby displays"], "is_active": True, "order": 2},
    {"name": "Hospitality", "slug": "hospitality", "description": "Guest-facing displays for hotels and restaurants.", "icon": "Coffee", "use_cases": ["Digital menus", "Lobby screens", "Event signage"], "is_active": True, "order": 3},
    {"name": "Entertainment", "slug": "entertainment", "description": "Large-scale displays for venues and events.", "icon": "Music", "use_cases": ["Concert backdrops", "Stadium screens", "Theater displays"], "is_active": True, "order": 4},
    {"name": "Transportation", "slug": "transportation", "description": "Information displays for transit hubs.", "icon": "Train", "use_cases": ["Flight information", "Wayfinding", "Advertising"], "is_active": True, "order": 5},
    {"name": "Education", "slug": "education", "description": "Interactive displays for learning environments.", "icon": "GraduationCap", "use_cases": ["Lecture halls", "Digital whiteboards", "Campus signage"], "is_active": True, "order": 6},
    {"name": "Healthcare", "slug": "healthcare", "description": "Information displays for medical facilities.", "icon": "Heart", "use_cases": ["Wayfinding", "Patient info", "Emergency alerts"], "is_active": True, "order": 7},
    {"name": "Broadcasting", "slug": "broadcasting", "description": "Displays for TV studios and production.", "icon": "Video", "use_cases": ["Virtual sets", "News backdrops", "Control rooms"], "is_active": True, "order": 8}
]

async def main():
    print("=" * 60)
    print("CMS Data Seeder - Starting...")
    print("=" * 60)
    try:
        print("\n[1/5] Seeding PixelVue Products...")
        await seed_collection("pixelvue_products", PIXELVUE_PRODUCTS)
        print("\n[2/5] Seeding Solutions...")
        await seed_collection("solutions", SOLUTIONS)
        print("\n[3/5] Seeding Product Families...")
        await seed_collection("product_families", PRODUCT_FAMILIES)
        print("\n[4/5] Seeding Technologies...")
        await seed_collection("technologies_content", TECHNOLOGIES)
        print("\n[5/5] Seeding Applications...")
        await seed_collection("applications_content", APPLICATIONS)
        print("\n" + "=" * 60)
        print("CMS Data Seeding Complete!")
        print("=" * 60)
    except Exception as e:
        print(f"Error during seeding: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
