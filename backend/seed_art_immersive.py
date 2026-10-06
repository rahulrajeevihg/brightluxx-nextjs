"""
Seed Art & Immersive products into the database.
"""
import asyncio
from datetime import datetime, timezone
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "brightluxx")

PRODUCTS = [
    # --- NFT & Digital Art (nft-gallery) ---
    {
        "name": "ArtFrame Pro 0.9",
        "slug": "artframe-pro-09",
        "product_code": "BL-ART-AF09",
        "category": "art-immersive",
        "sub_category": "nft-gallery",
        "family": "ArtFrame",
        "tagline": "Museum-grade NFT display with 16-bit color depth.",
        "description": "Premium fine-pitch LED panel designed for NFT galleries and digital art exhibitions. Features 16-bit color processing for over 281 trillion colors, anti-glare nano coating, and built-in NFT authentication via blockchain integration. Ideal for high-value digital art installations requiring absolute color accuracy.",
        "pixel_pitch": "0.9mm",
        "brightness": "600 nits",
        "application": "NFT Galleries, Digital Art Museums, Private Collections",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "0.9mm"},
            {"label": "Color Depth", "value": "16-bit"},
            {"label": "Contrast", "value": "20000:1"},
            {"label": "Viewing Angle", "value": "178°"},
            {"label": "Refresh Rate", "value": "7680Hz"},
            {"label": "Coating", "value": "Anti-glare Nano"}
        ],
        "features": ["16-bit Color Depth", "Anti-Glare Nano Coating", "NFT Authentication", "HDR10+ Support"],
        "image_url": "https://files.ihgbrands.com/downloaded-images_ext_65be281cb148.jpg",
        "featured": True,
    },
    {
        "name": "ArtFrame Gallery 1.2",
        "slug": "artframe-gallery-12",
        "product_code": "BL-ART-AG12",
        "category": "art-immersive",
        "sub_category": "nft-gallery",
        "family": "ArtFrame",
        "tagline": "Seamless bezel-free display for digital art galleries.",
        "description": "Ultra-slim bezel-free LED display designed for gallery walls. Zero visible gap technology creates a perfect canvas for digital artwork. Front-serviceable design allows flush wall mounting. Integrated color calibration ensures consistent reproduction across multi-panel installations.",
        "pixel_pitch": "1.2mm",
        "brightness": "800 nits",
        "application": "Art Galleries, Exhibition Spaces, Auction Houses",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.2mm"},
            {"label": "Brightness", "value": "800 nits"},
            {"label": "Gap", "value": "Zero Bezel"},
            {"label": "Service", "value": "Front Access"},
            {"label": "Weight", "value": "18kg/m²"},
            {"label": "Depth", "value": "38mm"}
        ],
        "features": ["Zero Bezel", "Front Serviceable", "Auto Calibration", "Art Mode Sleep"],
        "image_url": "https://files.ihgbrands.com/downloaded-images_ext_65be281cb148.jpg",
    },
    # --- Immersive Experience (immersive-experience) ---
    {
        "name": "ImmersaWall 360",
        "slug": "immersawall-360",
        "product_code": "BL-ART-IW360",
        "category": "art-immersive",
        "sub_category": "immersive-experience",
        "family": "ImmersaWall",
        "tagline": "Floor-to-ceiling immersive LED for teamLab-style experiences.",
        "description": "360-degree immersive LED wall system designed for interactive museum experiences. Modular panels cover floor, walls, and ceiling to create fully enclosed digital environments. Integrated motion sensors and real-time content generation enable visitor-reactive installations. Used in over 20 immersive art museums worldwide.",
        "pixel_pitch": "2.5mm",
        "brightness": "1200 nits",
        "application": "Immersive Museums, Theme Parks, Brand Experience Centers",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "2.5mm"},
            {"label": "Coverage", "value": "360° (Floor+Wall+Ceiling)"},
            {"label": "Sensors", "value": "IR Motion + LiDAR"},
            {"label": "Brightness", "value": "1200 nits"},
            {"label": "IP Rating", "value": "IP54 (Floor panels)"},
            {"label": "Weight", "value": "22kg/m²"}
        ],
        "features": ["360° Coverage", "Motion Sensors", "Real-time Generative Content", "Multi-visitor Tracking"],
        "image_url": "/downloaded-images/ext_bc8c12ee1348.jpg",
        "featured": True,
    },
    {
        "name": "ImmersaFloor P3.9",
        "slug": "immersafloor-p39",
        "product_code": "BL-ART-IF39",
        "category": "art-immersive",
        "sub_category": "immersive-experience",
        "family": "ImmersaWall",
        "tagline": "Walk-on interactive LED floor for immersive installations.",
        "description": "High-durability interactive LED floor panel rated for 2000kg/m² load capacity. Integrated pressure sensors detect footsteps for reactive visual content. Anti-slip tempered glass surface with IP65 rating. Perfect for immersive museum floors, retail experiences, and event installations.",
        "pixel_pitch": "3.9mm",
        "brightness": "1500 nits",
        "application": "Museum Floors, Retail Experiences, Event Installations",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "3.9mm"},
            {"label": "Load Capacity", "value": "2000 kg/m²"},
            {"label": "Surface", "value": "Anti-slip Tempered Glass"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Sensors", "value": "Pressure + Proximity"},
            {"label": "Thickness", "value": "95mm"}
        ],
        "features": ["Walk-on Interactive", "2000kg Load Capacity", "IP65 Waterproof", "Pressure Sensors"],
        "image_url": "/downloaded-images/ext_bc8c12ee1348.jpg",
    },
    # --- Virtual Production (virtual-production) ---
    {
        "name": "XR Stage Pro 1.5",
        "slug": "xr-stage-pro-15",
        "product_code": "BL-ART-XR15",
        "category": "art-immersive",
        "sub_category": "virtual-production",
        "family": "XR Stage",
        "tagline": "Cinema-grade LED wall for virtual production and XR stages.",
        "description": "Professional XR/VP LED wall system designed for film, TV, and commercial production. Features 7680Hz refresh rate for flicker-free camera capture, Unreal Engine ICVFX integration, and genlock synchronization. HDR processing with 10000:1 contrast ratio delivers photorealistic backgrounds. Used on major film and broadcast productions.",
        "pixel_pitch": "1.5mm",
        "brightness": "1500 nits",
        "application": "Film Production, TV Studios, Commercial Shoots, XR Stages",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.5mm"},
            {"label": "Refresh Rate", "value": "7680Hz"},
            {"label": "Contrast", "value": "10000:1"},
            {"label": "Color Gamut", "value": "DCI-P3 98%"},
            {"label": "Genlock", "value": "Yes (Blackburst/Tri-level)"},
            {"label": "Processing", "value": "Brompton Tessera SX40"}
        ],
        "features": ["7680Hz Refresh", "Unreal Engine Ready", "Camera Genlock", "DCI-P3 Color"],
        "image_url": "https://files.ihgbrands.com/downloaded-images_ext_00eecd7267f8.jpg",
        "featured": True,
    },
    {
        "name": "XR Curve 2.6",
        "slug": "xr-curve-26",
        "product_code": "BL-ART-XRC26",
        "category": "art-immersive",
        "sub_category": "virtual-production",
        "family": "XR Stage",
        "tagline": "Curved LED volume for wrap-around virtual production.",
        "description": "Curved LED panel system for building wrap-around XR volumes. Concave and convex configurations from 500mm to 5000mm radius. Magnetic front-service modules enable rapid setup and striking. Integrated with disguise and Pixotope for real-time tracking and rendering.",
        "pixel_pitch": "2.6mm",
        "brightness": "1200 nits",
        "application": "XR Volumes, Broadcast Studios, Automotive Reveals",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "2.6mm"},
            {"label": "Curve Radius", "value": "500mm - 5000mm"},
            {"label": "Refresh Rate", "value": "7680Hz"},
            {"label": "Service", "value": "Magnetic Front Access"},
            {"label": "Weight", "value": "12kg/panel"},
            {"label": "Setup", "value": "Quick-lock System"}
        ],
        "features": ["Curved Configurations", "Quick-lock Setup", "Magnetic Service", "disguise Compatible"],
        "image_url": "https://files.ihgbrands.com/downloaded-images_ext_00eecd7267f8.jpg",
    },
    # --- Metaverse (metaverse) ---
    {
        "name": "MetaPortal 1.8",
        "slug": "metaportal-18",
        "product_code": "BL-ART-MP18",
        "category": "art-immersive",
        "sub_category": "metaverse",
        "family": "MetaPortal",
        "tagline": "Mixed reality LED gateway for metaverse experiences.",
        "description": "LED display portal designed for bridging physical and metaverse environments. Ultra-fast 15360Hz refresh rate eliminates motion blur for AR/VR pass-through applications. Built-in depth sensors and hand-tracking cameras enable gesture-based interaction with virtual objects. Supports WebXR, OpenXR, and major metaverse platforms.",
        "pixel_pitch": "1.8mm",
        "brightness": "1000 nits",
        "application": "Metaverse Portals, Mixed Reality Spaces, Gaming Arenas",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "1.8mm"},
            {"label": "Refresh Rate", "value": "15360Hz"},
            {"label": "Sensors", "value": "Depth + Hand Tracking"},
            {"label": "Latency", "value": "<5ms"},
            {"label": "Protocols", "value": "WebXR / OpenXR"},
            {"label": "Brightness", "value": "1000 nits"}
        ],
        "features": ["Mixed Reality Ready", "Hand Tracking", "Ultra-low Latency", "WebXR Support"],
        "image_url": "/generated-images/immersive-museum-1.webp",
        "featured": True,
    },
    {
        "name": "MetaRoom Cube",
        "slug": "metaroom-cube",
        "product_code": "BL-ART-MRC",
        "category": "art-immersive",
        "sub_category": "metaverse",
        "family": "MetaPortal",
        "tagline": "6-sided LED cube for fully immersive metaverse environments.",
        "description": "Modular 6-sided LED room that creates a fully enclosed virtual environment. Each wall, floor, and ceiling panel is independently driven for seamless 360° immersion. Positional audio and haptic floor feedback complete the multi-sensory experience. Ideal for enterprise metaverse meetings, virtual tourism, and training simulations.",
        "pixel_pitch": "2.5mm",
        "brightness": "800 nits",
        "application": "Enterprise Metaverse, Virtual Tourism, Training Simulation",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "2.5mm"},
            {"label": "Panels", "value": "6-sided (All surfaces)"},
            {"label": "Audio", "value": "Positional 32-channel"},
            {"label": "Floor", "value": "Haptic Feedback"},
            {"label": "Tracking", "value": "Inside-out 6DoF"},
            {"label": "Brightness", "value": "800 nits"}
        ],
        "features": ["6-Sided Immersion", "Haptic Floor", "Positional Audio", "6DoF Tracking"],
        "image_url": "/generated-images/immersive-museum-1.webp",
    },
    # --- Sculptural LED (sculptural) ---
    {
        "name": "SculptLED Sphere 3D",
        "slug": "sculptled-sphere-3d",
        "product_code": "BL-ART-SL3D",
        "category": "art-immersive",
        "sub_category": "sculptural",
        "family": "SculptLED",
        "tagline": "LED sphere display for iconic installations and public art.",
        "description": "Spherical LED display available in diameters from 1m to 8m. Custom-mapped pixel layout ensures seamless content across the curved surface. IP65 weatherproof for outdoor installations. Built-in content management system with real-time generative art capabilities. Iconic centerpiece for museums, corporate lobbies, and public plazas.",
        "pixel_pitch": "4mm",
        "brightness": "5000 nits",
        "application": "Public Art, Museum Centerpieces, Corporate Lobbies, Plazas",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "4mm"},
            {"label": "Diameter", "value": "1m - 8m"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Brightness", "value": "5000 nits"},
            {"label": "CMS", "value": "Built-in Generative"},
            {"label": "Viewing", "value": "360° Omni-directional"}
        ],
        "features": ["Spherical 360° Display", "IP65 Outdoor", "Generative Content", "Custom Diameters"],
        "image_url": "/generated-images/sphere-led-1.webp",
    },
    {
        "name": "SculptLED Ribbon Flex",
        "slug": "sculptled-ribbon-flex",
        "product_code": "BL-ART-SRF",
        "category": "art-immersive",
        "sub_category": "sculptural",
        "family": "SculptLED",
        "tagline": "Flexible LED ribbon for organic sculptural forms.",
        "description": "Ultra-flexible LED strip that bends to any organic shape. Minimum bend radius of 50mm enables wrapping around columns, creating waves, spirals, and freeform sculptures. Silicone encapsulation provides IP67 waterproofing. Individually addressable pixels allow complex animations across sculptural forms.",
        "pixel_pitch": "10mm",
        "brightness": "2000 nits",
        "application": "Art Sculptures, Architectural Features, Stage Design",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "10mm"},
            {"label": "Bend Radius", "value": "50mm min"},
            {"label": "IP Rating", "value": "IP67"},
            {"label": "Encapsulation", "value": "Silicone"},
            {"label": "Addressability", "value": "Per-pixel"},
            {"label": "Brightness", "value": "2000 nits"}
        ],
        "features": ["Ultra-Flexible 50mm Bend", "IP67 Waterproof", "Per-pixel Control", "Silicone Sealed"],
        "image_url": "/generated-images/sphere-led-1.webp",
    },
    # --- Public Art (public-art) ---
    {
        "name": "UrbanCanvas P6 Outdoor",
        "slug": "urbancanvas-p6-outdoor",
        "product_code": "BL-ART-UC6",
        "category": "art-immersive",
        "sub_category": "public-art",
        "family": "UrbanCanvas",
        "tagline": "Weatherproof LED canvas for large-scale public art installations.",
        "description": "Industrial-grade outdoor LED display designed for permanent public art installations. IP65 rated with anti-corrosion treatment for coastal environments. Brightness up to 8000 nits ensures visibility in direct sunlight. Remote content management with 4G/5G connectivity. Designed for 10+ year continuous outdoor operation.",
        "pixel_pitch": "6mm",
        "brightness": "8000 nits",
        "application": "Public Art, Urban Landmarks, Building Facades, Plazas",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "6mm"},
            {"label": "Brightness", "value": "8000 nits"},
            {"label": "IP Rating", "value": "IP65"},
            {"label": "Lifespan", "value": "100,000 hours"},
            {"label": "Connectivity", "value": "4G/5G Remote"},
            {"label": "Operating Temp", "value": "-30°C to 60°C"}
        ],
        "features": ["8000 nits Outdoor", "IP65 Weatherproof", "10+ Year Lifespan", "Remote Management"],
        "image_url": "/downloaded-images/ext_7e32a28621f2.jpg",
        "featured": True,
    },
    {
        "name": "UrbanCanvas Transparent Mesh",
        "slug": "urbancanvas-transparent-mesh",
        "product_code": "BL-ART-UCTM",
        "category": "art-immersive",
        "sub_category": "public-art",
        "family": "UrbanCanvas",
        "tagline": "See-through LED mesh for building-scale public art.",
        "description": "Transparent LED mesh with 70% transparency for building facade installations. Content appears to float in mid-air while maintaining see-through views. Wind-resistant design rated for 120km/h. Lightweight aluminum frame at 8kg/m² simplifies structural requirements. Perfect for creating building-scale digital art without blocking natural light or views.",
        "pixel_pitch": "15mm",
        "brightness": "6000 nits",
        "application": "Building Facades, Bridges, Architectural Art, Skyline Features",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "15mm"},
            {"label": "Transparency", "value": "70%"},
            {"label": "Wind Rating", "value": "120 km/h"},
            {"label": "Weight", "value": "8 kg/m²"},
            {"label": "Brightness", "value": "6000 nits"},
            {"label": "Maintenance", "value": "Front Access"}
        ],
        "features": ["70% Transparent", "Building-scale", "Wind Resistant", "Lightweight 8kg/m²"],
        "image_url": "/downloaded-images/ext_7e32a28621f2.jpg",
    },
    # --- Interactive (interactive) ---
    {
        "name": "TouchWall Interactive P2.5",
        "slug": "touchwall-interactive-p25",
        "product_code": "BL-ART-TWI25",
        "category": "art-immersive",
        "sub_category": "interactive",
        "family": "TouchWall",
        "tagline": "Multi-touch LED wall for interactive art and education.",
        "description": "Large-format interactive LED wall with 32-point multi-touch capability via infrared overlay. Supports gesture recognition, object detection, and collaborative drawing. Low-latency touch response under 8ms for natural interaction. Pre-loaded with interactive art applications and SDK for custom development. Perfect for museums, science centers, and interactive exhibitions.",
        "pixel_pitch": "2.5mm",
        "brightness": "800 nits",
        "application": "Museums, Science Centers, Interactive Exhibitions, Education",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "2.5mm"},
            {"label": "Touch Points", "value": "32-point Multi-touch"},
            {"label": "Touch Latency", "value": "<8ms"},
            {"label": "Object Detection", "value": "Yes"},
            {"label": "SDK", "value": "Custom Development"},
            {"label": "Brightness", "value": "800 nits"}
        ],
        "features": ["32-Point Multi-touch", "Gesture Recognition", "Object Detection", "Developer SDK"],
        "image_url": "/generated-images/immersive-museum-1.webp",
    },
    {
        "name": "KineticLED Responsive P3.9",
        "slug": "kineticled-responsive-p39",
        "product_code": "BL-ART-KLR39",
        "category": "art-immersive",
        "sub_category": "interactive",
        "family": "TouchWall",
        "tagline": "Motion-reactive LED display that responds to audience movement.",
        "description": "LED display panel with integrated depth cameras and AI-powered motion tracking. Content dynamically responds to viewer proximity, gesture, and movement in real-time. Supports up to 50 simultaneous visitors. Pre-loaded generative art algorithms create unique visual responses to each interaction. Ideal for lobby installations, retail windows, and public art.",
        "pixel_pitch": "3.9mm",
        "brightness": "1200 nits",
        "application": "Lobby Installations, Retail Windows, Public Art, Events",
        "key_specs": [
            {"label": "Pixel Pitch", "value": "3.9mm"},
            {"label": "Tracking", "value": "AI Motion + Depth"},
            {"label": "Max Visitors", "value": "50 simultaneous"},
            {"label": "Response Time", "value": "<16ms"},
            {"label": "AI Engine", "value": "Built-in GPU"},
            {"label": "Brightness", "value": "1200 nits"}
        ],
        "features": ["AI Motion Tracking", "50-Person Tracking", "Generative Art Engine", "Real-time Response"],
        "image_url": "/generated-images/immersive-museum-1.webp",
    },
]


async def seed_art_immersive():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    col = db["products"]

    inserted = 0
    skipped = 0
    for product in PRODUCTS:
        existing = await col.find_one({"product_code": product["product_code"]})
        if existing:
            skipped += 1
            continue

        product["id"] = str(uuid.uuid4())
        product["created_at"] = datetime.now(timezone.utc)
        product["trending"] = False
        product["new_arrival"] = True
        product.setdefault("featured", False)
        await col.insert_one(product)
        inserted += 1

    print(f"Art & Immersive products: {inserted} inserted, {skipped} skipped (already exist)")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_art_immersive())
