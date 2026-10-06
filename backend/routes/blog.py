"""
Blog API routes for managing blog posts.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
import uuid
import os
import re

from database import db
from auth import get_current_admin
from routes.ssr_meta import clear_ssr_cache
router = APIRouter()

blogs_col = db["blogs"]

# External CDN base URL
EXTERNAL_CDN = ""


def slugify(text: str) -> str:
    """Generate URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


class BlogCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    excerpt: str
    content: str
    category: str
    author: str = "Brightluxx Team"
    image_url: Optional[str] = None
    read_time: str = "5 min"
    tags: List[str] = []
    is_published: bool = False
    featured: bool = False


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    read_time: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None


# Public endpoints
@router.get("/api/blogs")
async def get_published_blogs(category: Optional[str] = None):
    """Get all published blog posts for the public blog page."""
    query = {"is_published": True}
    if category and category.lower() != "all":
        query["category"] = category
    
    cursor = blogs_col.find(query, {"_id": 0}).sort("published_at", -1)
    blogs = await cursor.to_list(length=100)
    
    # Get unique categories efficiently via aggregation
    pipeline = [
        {"$match": {"is_published": True}},
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}},
    ]
    cat_docs = await blogs_col.aggregate(pipeline).to_list(length=100)
    categories = ["All"] + [doc["_id"] for doc in cat_docs if doc.get("_id")]
    
    return {"blogs": blogs, "categories": categories}


@router.get("/api/blogs/{slug}")
async def get_blog_by_slug(slug: str):
    """Get a single blog post by slug for the detail page."""
    blog = await blogs_col.find_one({"slug": slug, "is_published": True}, {"_id": 0})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {"blog": blog}


# Admin endpoints
@router.get("/api/admin/blogs")
async def admin_get_blogs(admin=Depends(get_current_admin)):
    """Get all blog posts for admin (including drafts)."""
    cursor = blogs_col.find({}, {"_id": 0}).sort("created_at", -1)
    blogs = await cursor.to_list(length=500)
    
    counts = {
        "total": await blogs_col.count_documents({}),
        "published": await blogs_col.count_documents({"is_published": True}),
        "drafts": await blogs_col.count_documents({"is_published": False}),
        "featured": await blogs_col.count_documents({"featured": True}),
    }
    
    return {"blogs": blogs, "counts": counts}


@router.post("/api/admin/blogs")
async def create_blog(data: BlogCreate, admin=Depends(get_current_admin)):
    """Create a new blog post."""
    blog_id = str(uuid.uuid4())[:12]
    
    # Generate slug if not provided
    slug = data.slug or slugify(data.title)
    
    # Ensure unique slug
    existing = await blogs_col.find_one({"slug": slug})
    if existing:
        slug = f"{slug}-{blog_id[:4]}"
    
    now = datetime.now(timezone.utc)
    
    blog = {
        "id": blog_id,
        "title": data.title,
        "slug": slug,
        "excerpt": data.excerpt,
        "content": data.content,
        "category": data.category,
        "author": data.author,
        "image_url": data.image_url,
        "read_time": data.read_time,
        "tags": data.tags,
        "is_published": data.is_published,
        "featured": data.featured,
        "created_at": now,
        "updated_at": now,
        "published_at": now if data.is_published else None,
    }
    
    await blogs_col.insert_one(blog)
    
    return {"success": True, "blog": {k: v for k, v in blog.items() if k != "_id"}}


@router.post("/api/admin/blogs/upload-image")
async def upload_blog_image(
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Upload an image for a blog post."""
    from cdn_upload import upload_image_to_cdn
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
        )
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    unique_name = f"blog_{uuid.uuid4().hex[:8]}{ext}"
    
    # Read file content
    content = await file.read()
    
    # Upload to CDN
    try:
        image_url = upload_image_to_cdn(unique_name, content, "blog")
        
        return {
            "success": True,
            "image_url": image_url,
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/api/admin/blogs/{blog_id}")
async def update_blog(blog_id: str, data: BlogUpdate, admin=Depends(get_current_admin)):
    """Update a blog post."""
    existing = await blogs_col.find_one({"id": blog_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # If publishing for the first time, set published_at
    if data.is_published and not existing.get("published_at"):
        update_data["published_at"] = datetime.now(timezone.utc)
    
    # If slug changed, ensure uniqueness
    if data.slug and data.slug != existing.get("slug"):
        slug_exists = await blogs_col.find_one({"slug": data.slug, "id": {"$ne": blog_id}})
        if slug_exists:
            raise HTTPException(status_code=400, detail="Slug already exists")
    
    await blogs_col.update_one({"id": blog_id}, {"$set": update_data})
    clear_ssr_cache()
    updated = await blogs_col.find_one({"id": blog_id}, {"_id": 0})
    return {"success": True, "blog": updated}


@router.delete("/api/admin/blogs/{blog_id}")
async def delete_blog(blog_id: str, admin=Depends(get_current_admin)):
    """Delete a blog post."""
    result = await blogs_col.delete_one({"id": blog_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    clear_ssr_cache()
    return {"success": True, "message": "Blog post deleted"}


@router.post("/api/admin/blogs/seed")
async def seed_blogs(admin=Depends(get_current_admin)):
    """Seed sample blog posts (one-time)."""
    existing_count = await blogs_col.count_documents({})
    if existing_count > 0:
        return {"success": False, "message": f"Blogs already exist ({existing_count} found)."}
    
    now = datetime.now(timezone.utc)
    
    sample_blogs = [
        {
            "id": "blog-001",
            "title": "MicroLED vs OLED: Which Technology Wins in 2025?",
            "slug": "microled-vs-oled-2025",
            "excerpt": "A deep comparison of MicroLED and OLED for commercial applications. Brightness, lifespan, burn-in resistance, and total cost of ownership.",
            "content": """<h2>The Display Technology Landscape</h2>
<p>As we enter 2025, the battle between MicroLED and OLED technologies continues to shape the commercial display market. Both technologies offer exceptional image quality, but their differences make them suited for different applications.</p>

<h3>Brightness Performance</h3>
<p>MicroLED displays can achieve brightness levels exceeding 5,000 nits, making them ideal for high-ambient-light environments like retail storefronts and outdoor installations. OLED panels typically max out around 1,000-1,500 nits, which limits their use in bright environments.</p>

<h3>Lifespan and Burn-in</h3>
<p>One of MicroLED's strongest advantages is its immunity to burn-in. Unlike OLED, which can suffer from image retention when displaying static content for extended periods, MicroLED maintains consistent performance regardless of content type.</p>

<h3>Cost Considerations</h3>
<p>OLED remains more cost-effective for smaller displays and applications where extreme brightness isn't required. However, MicroLED's total cost of ownership over a 5-7 year period often makes it the smarter investment for 24/7 commercial applications.</p>

<h3>Our Recommendation</h3>
<p>For GCC installations where high brightness and durability are paramount, MicroLED is increasingly the technology of choice. Contact our team for a detailed analysis of your specific requirements.</p>""",
            "category": "Technology",
            "author": "Technical Team",
            "image_url": f"{EXTERNAL_CDN}/blog/microled-oled-comparison.jpg",
            "read_time": "8 min",
            "tags": ["MicroLED", "OLED", "Technology", "Comparison"],
            "is_published": True,
            "featured": True,
            "created_at": now,
            "updated_at": now,
            "published_at": now,
        },
        {
            "id": "blog-002",
            "title": "The Complete Guide to Choosing the Right Pixel Pitch",
            "slug": "choosing-pixel-pitch-guide",
            "excerpt": "How to select the optimal pixel pitch for your LED display based on viewing distance, content type, budget, and application environment.",
            "content": """<h2>Understanding Pixel Pitch</h2>
<p>Pixel pitch is the distance in millimeters between the center of one LED cluster to the center of the next. It's the single most important specification when selecting an LED display.</p>

<h3>The Viewing Distance Formula</h3>
<p>A simple rule of thumb: multiply the pixel pitch by 1.5-2 to get the minimum comfortable viewing distance in meters. For a P2.5 display, the minimum viewing distance is approximately 3.75-5 meters.</p>

<h3>Application-Based Recommendations</h3>
<ul>
<li><strong>Control Rooms:</strong> P0.9 - P1.5 (operators sitting 1-3m away)</li>
<li><strong>Corporate Meeting Rooms:</strong> P1.2 - P1.9</li>
<li><strong>Retail (Indoor):</strong> P2.5 - P3.9</li>
<li><strong>Outdoor Billboards:</strong> P6 - P10 (depending on road speed)</li>
</ul>

<h3>Budget vs Quality Trade-offs</h3>
<p>Smaller pixel pitch means more LEDs per square meter, which increases cost. Don't overspend on unnecessary resolution—a P1.2 display viewed from 10 meters away won't look better than a P2.5.</p>""",
            "category": "Guides",
            "author": "Brightluxx Team",
            "image_url": f"{EXTERNAL_CDN}/blog/pixel-pitch-guide.jpg",
            "read_time": "6 min",
            "tags": ["Pixel Pitch", "Guide", "Specification"],
            "is_published": True,
            "featured": False,
            "created_at": now,
            "updated_at": now,
            "published_at": now,
        },
        {
            "id": "blog-003",
            "title": "How LED Displays Are Transforming Dubai Retail",
            "slug": "led-displays-dubai-retail",
            "excerpt": "Case studies of LED display installations in Dubai malls — from interactive storefronts to immersive brand experiences.",
            "content": """<h2>The Retail Revolution</h2>
<p>Dubai's retail sector has embraced LED technology like no other market. From the world's largest malls to boutique luxury stores, digital displays are redefining the shopping experience.</p>

<h3>Case Study: Mall of the Emirates</h3>
<p>The recent renovation of a major fashion retailer included a 15-meter curved LED video wall at the entrance. The result: 40% increase in foot traffic and significant uplift in average transaction value.</p>

<h3>Interactive Experiences</h3>
<p>Touch-enabled LED displays are becoming standard in Dubai's premium retail spaces. Customers can browse collections, check availability, and even customize products directly on the display.</p>

<h3>Energy Efficiency Wins</h3>
<p>Despite their brightness, modern LED displays consume 30-40% less energy than previous generations. This aligns with Dubai's sustainability goals while delivering superior visual impact.</p>""",
            "category": "Industry",
            "author": "Market Insights Team",
            "image_url": f"{EXTERNAL_CDN}/blog/dubai-retail-led.jpg",
            "read_time": "5 min",
            "tags": ["Dubai", "Retail", "Case Study", "GCC"],
            "is_published": True,
            "featured": False,
            "created_at": now,
            "updated_at": now,
            "published_at": now,
        },
        {
            "id": "blog-004",
            "title": "Outdoor LED Displays in UAE Heat: What You Need to Know",
            "slug": "outdoor-led-uae-heat-guide",
            "excerpt": "Engineering LED displays for 60°C+ temperatures. IP ratings, cooling systems, brightness requirements, and Gulf-grade specifications.",
            "content": """<h2>The UAE Challenge</h2>
<p>Operating LED displays in the UAE presents unique challenges. Summer surface temperatures can exceed 60°C, ambient humidity fluctuates dramatically, and dust storms are a regular occurrence.</p>

<h3>IP Rating Requirements</h3>
<p>For outdoor installations in the UAE, IP65 is the minimum acceptable rating. IP65 front + IP54 rear is suitable for covered outdoor areas. For fully exposed locations, IP67 or IP68 rated displays should be specified.</p>

<h3>Thermal Management</h3>
<p>Proper thermal management is critical. Modern outdoor displays should feature:
<ul>
<li>Forced air cooling with filtered intakes</li>
<li>Automatic brightness adjustment to reduce heat generation</li>
<li>Operating temperature rating of -20°C to +60°C minimum</li>
</ul></p>

<h3>Brightness for Visibility</h3>
<p>In direct sunlight, displays need 5,000+ nits to remain visible. Even shaded outdoor areas in Dubai require 2,500-3,000 nits minimum.</p>""",
            "category": "Technical",
            "author": "Engineering Team",
            "image_url": f"{EXTERNAL_CDN}/blog/outdoor-led-uae.jpg",
            "read_time": "7 min",
            "tags": ["Outdoor", "UAE", "Technical", "IP Rating"],
            "is_published": True,
            "featured": True,
            "created_at": now,
            "updated_at": now,
            "published_at": now,
        },
        {
            "id": "blog-005",
            "title": "COB LED Technology Explained: Why It Matters",
            "slug": "cob-led-technology-explained",
            "excerpt": "Chip-on-Board LED delivers superior durability, anti-glare performance, and close-viewing quality. Understanding the advantages.",
            "content": """<h2>What is COB?</h2>
<p>COB (Chip-on-Board) technology represents a significant advancement over traditional SMD LED packaging. Instead of mounting individual LED chips in protective housings, COB integrates multiple chips directly onto the substrate and covers them with a protective resin layer.</p>

<h3>Key Advantages</h3>
<p><strong>Durability:</strong> COB displays are significantly more resistant to physical damage. There are no protruding LED lenses to break off, making them ideal for high-traffic areas.</p>
<p><strong>Anti-Glare:</strong> The matte surface finish reduces reflections, making COB displays more comfortable to view in bright environments or at close distances.</p>
<p><strong>Contrast:</strong> The black surface between pixels delivers superior contrast ratios compared to SMD displays.</p>

<h3>Best Applications</h3>
<p>COB technology excels in:
<ul>
<li>Corporate meeting rooms with close viewing</li>
<li>Control rooms requiring extended viewing sessions</li>
<li>Retail environments with customer interaction</li>
<li>Any installation requiring maximum durability</li>
</ul></p>""",
            "category": "Technology",
            "author": "Technical Team",
            "image_url": f"{EXTERNAL_CDN}/blog/cob-technology.jpg",
            "read_time": "5 min",
            "tags": ["COB", "Technology", "Innovation"],
            "is_published": True,
            "featured": False,
            "created_at": now,
            "updated_at": now,
            "published_at": now,
        },
    ]
    
    await blogs_col.insert_many(sample_blogs)
    
    return {"success": True, "message": f"Seeded {len(sample_blogs)} blog posts"}
