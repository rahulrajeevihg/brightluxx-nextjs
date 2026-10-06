"""
Image regeneration endpoint for updating product images with UAE-themed realistic images
Uses OpenAI GPT Image 1 (latest) via Emergent Integrations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

load_dotenv()

router = APIRouter(prefix="/api/admin/images", tags=["Image Management"])

# Emergent LLM Key for GPT Image 1
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "brightluxx")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# UNIQUE scenes for each product - deterministic based on slug hash
# This ensures each product ALWAYS gets a different scene
UNIQUE_SCENES = {
    "indoor": [
        "LED video wall in luxury hotel reception showing abstract art, marble desk, chandelier lighting",
        "LED display in shopping mall atrium showing lifestyle fashion imagery, shoppers walking, high ceiling",
        "LED screen in modern fitness center showing workout graphics, gym equipment, people exercising",
        "LED wall in corporate boardroom showing data charts, executive chairs, city view through windows",
        "LED display in hospital lobby showing health visuals, reception area, clean modern design",
        "LED screen in university lecture hall showing educational content, students in seats",
        "LED wall in restaurant showing food imagery, dining tables, ambient evening lighting",
        "LED display in bank branch showing financial graphics, customer service area, modern interior",
        "LED screen in museum gallery showing digital art exhibition, visitors viewing, white walls",
        "LED wall in airport departure lounge showing travel imagery, passengers waiting, terminal view",
    ],
    "outdoor": [
        "Outdoor LED on shopping mall exterior showing fashion advertising, evening lighting, pedestrians",
        "LED screen at modern petrol station showing brand imagery, vehicles, canopy lighting",
        "Outdoor LED at sports stadium entrance showing event graphics, fans gathering",
        "LED display on restaurant exterior showing food imagery, outdoor seating, evening atmosphere",
        "Outdoor LED at beach resort showing vacation imagery, pool area, sunset sky",
        "LED screen on hotel facade showing lifestyle imagery, valet area, palm trees",
        "Outdoor LED at theme park entrance showing entertainment graphics, families visiting",
        "LED billboard at urban plaza showing brand campaign, people walking, modern architecture",
        "Outdoor LED at transit station showing information graphics, commuters, modern station",
        "LED display at construction site showing property renders, cranes, urban development",
    ],
    "cob-microled": [
        "MicroLED wall in private home cinema showing movie scene, leather recliners, dark room",
        "COB display in luxury watch boutique showing product imagery, glass cases, elegant interior",
        "MicroLED in art gallery showing digital artwork, visitors, minimalist white space",
        "COB screen in VIP lounge showing travel imagery, premium seating, window view",
        "MicroLED in executive office showing data visualization, designer furniture, city panorama",
        "COB display in jewelry store showing sparkling product shots, luxury retail environment",
    ],
    "transparent": [
        "Transparent LED in jewelry store window, products visible through, luxury environment",
        "Transparent LED on office building facade, city reflections, modern architecture",
        "Transparent LED partition in restaurant, diners visible through, elegant interior",
        "Transparent LED in car showroom window, vehicles visible behind, premium showroom",
        "Transparent LED in retail storefront, mannequins visible through, shopping mall",
        "Transparent LED in museum display, artifacts visible behind, exhibition space",
    ],
    "flexible": [
        "Curved LED around hotel lobby column showing flowing art, chandelier, luxury interior",
        "Wave-shaped LED in exhibition hall showing brand graphics, trade show visitors",
        "Cylindrical LED in retail store showing product imagery, modern design, shoppers",
        "Curved LED ceiling installation in mall showing sky imagery, atrium space",
        "Flexible LED wrapped around pillar in nightclub, colorful visuals, party atmosphere",
    ],
    "all-in-one": [
        "All-in-one LED in classroom showing diagrams, students at desks, teacher presenting",
        "Conference display in meeting room showing presentation, professionals collaborating",
        "All-in-one LED in medical consultation showing health data, doctor with patient",
        "Training room display showing course content, corporate learning environment",
        "All-in-one LED in coworking space showing analytics, entrepreneurs working",
    ],
    "rental": [
        "Rental LED at outdoor wedding showing couple photos, decorated venue, string lights",
        "Portable LED at corporate gala showing brand presentation, formal dinner setup",
        "Rental LED at music festival showing stage visuals, crowd dancing, night scene",
        "Event LED at product launch showing brand reveal, audience seated, spotlights",
        "Rental LED at sports event showing live match, spectators cheering, arena setting",
    ],
    "poster-totem": [
        "LED totem in hotel lobby showing event info, guests in lobby, elegant design",
        "Digital poster in metro station showing transit info, commuters walking",
        "LED kiosk in hospital showing wayfinding, medical staff, clean interior",
        "Digital totem in retail store showing promotions, shoppers browsing",
        "LED poster in office building showing directory, business professionals",
    ],
    "digital-signage": [
        "Digital menu in restaurant showing food items, customers ordering, modern interior",
        "Information display in service center showing queue info, people waiting",
        "Wayfinding screen in hospital showing directions, visitors, clean design",
        "Digital signage in retail showing product info, shoppers, store interior",
        "Menu board in cafe showing beverages, barista counter, cozy atmosphere",
    ],
    "signage-solutions": [
        "Illuminated LED channel letters on upscale restaurant storefront at night, warm lighting, outdoor dining area, city street",
        "Halo-lit 3D channel letters on luxury hotel entrance, valet parking area, evening atmosphere, palm trees",
        "RGB LED channel letters on retail store facade, shopping mall exterior, colorful glow, pedestrians walking",
        "Neon-style LED letters on trendy bar entrance, nightlife scene, urban setting, people gathering",
        "Digital menu board inside fast food restaurant, customers ordering at counter, bright modern interior",
        "Drive-thru LED menu display at night, car waiting, outdoor lighting, fast food restaurant",
        "Interactive wayfinding kiosk in shopping mall, families browsing, bright atrium, stores in background",
        "Airport flight information display showing departures, travelers with luggage, terminal interior",
        "Outdoor LED pylon sign at business park entrance, cars passing, landscaping, modern architecture",
        "Transparent LED window display in high-end jewelry store, products visible through, luxury retail",
        "Gas station LED price sign at dusk, cars fueling, canopy lights, convenience store",
        "Large 3D fabricated letters on corporate building rooftop, city skyline, blue hour lighting",
        "Video wall menu system in food court, multiple restaurants, diners choosing, shopping mall",
        "Digital directory kiosk in hospital lobby, visitors checking directions, clean modern interior",
    ],
}

import hashlib

# Category prompts derived from UNIQUE_SCENES for preview/listing endpoints
CATEGORY_PROMPTS = {k: v[0] for k, v in UNIQUE_SCENES.items()}
CATEGORY_PROMPTS["default"] = UNIQUE_SCENES["indoor"][0]

def get_unique_prompt(category: str, product_name: str, pixel_pitch: str) -> str:
    """Get a UNIQUE prompt for each product based on its slug - ensures variety"""
    scenes = UNIQUE_SCENES.get(category, UNIQUE_SCENES.get("indoor"))
    
    # Use product name hash to deterministically select a scene
    hash_val = int(hashlib.sha256(product_name.encode()).hexdigest(), 16)
    scene_index = hash_val % len(scenes)
    scene = scenes[scene_index]
    
    base_prompt = f"Ultra realistic photograph of {scene}, professional photography, 8K resolution, natural lighting"
    
    return f"{base_prompt}, featuring premium {pixel_pitch} LED technology with crystal clear image quality"

class ImageGenerationRequest(BaseModel):
    product_slug: str
    custom_prompt: Optional[str] = None

class BulkImageRequest(BaseModel):
    category: Optional[str] = None
    limit: Optional[int] = 10

async def generate_image_openai(prompt: str) -> bytes:
    """Generate image using OpenAI GPT Image 1 (latest, most realistic)"""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="Emergent LLM key not configured")
    
    try:
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            return images[0]
        else:
            raise HTTPException(status_code=500, detail="No image was generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")

async def upload_to_cdn(image_bytes: bytes, filename: str) -> str:
    """Upload image to local storage and return URL"""
    upload_dir = Path("/app/frontend/public/generated-images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = upload_dir / unique_filename
    
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    
    # Return relative URL that can be served by frontend
    return f"/generated-images/{unique_filename}"

@router.post("/regenerate/{product_slug}")
async def regenerate_product_image(product_slug: str, custom_prompt: Optional[str] = None):
    """Regenerate image for a specific product using OpenAI"""
    
    # Get product
    product = await db.products.find_one({"slug": product_slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get product details
    category = product.get("category", "default")
    product_name = product.get("name", "LED display")
    pixel_pitch = product.get("pixel_pitch", "")
    
    if custom_prompt:
        prompt = custom_prompt
    else:
        # Use the new unique prompt function
        prompt = get_unique_prompt(category, product_name, pixel_pitch)
    
    try:
        # Generate image
        image_bytes = await generate_image_openai(prompt)
        
        # Upload to CDN
        image_url = await upload_to_cdn(image_bytes, f"{product_slug}.png")
        
        # Update product in database
        await db.products.update_one(
            {"slug": product_slug},
            {
                "$set": {
                    "image_url": image_url,
                    "image_updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "product_slug": product_slug,
            "new_image_url": image_url,
            "prompt_used": prompt
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview-prompt/{product_slug}")
async def preview_prompt(product_slug: str):
    """Preview the prompt that would be used for a product"""
    
    product = await db.products.find_one({"slug": product_slug})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = product.get("category", "default")
    base_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["default"])
    product_name = product.get("name", "LED display")
    pixel_pitch = product.get("pixel_pitch", "")
    
    full_prompt = f"{base_prompt}, showing {product_name} {pixel_pitch} LED technology"
    
    return {
        "product_slug": product_slug,
        "product_name": product_name,
        "category": category,
        "prompt": full_prompt
    }

@router.get("/categories")
async def list_categories():
    """List all available category prompts"""
    return {
        "categories": list(CATEGORY_PROMPTS.keys()),
        "prompts": CATEGORY_PROMPTS
    }
