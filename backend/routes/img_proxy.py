"""
Image optimization proxy — resizes & converts images to WebP on the fly.
GET /api/img?url=<source>&w=<width>&q=<quality>
"""
from fastapi import APIRouter, Query, Response
from fastapi.responses import Response as FastAPIResponse
import httpx
import hashlib
import io
from PIL import Image
from collections import OrderedDict

router = APIRouter()

# Simple LRU cache (max 200 entries, ~100MB)
_cache = OrderedDict()
_CACHE_MAX = 200


def _cache_get(key):
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    return None


def _cache_set(key, value):
    _cache[key] = value
    _cache.move_to_end(key)
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)


@router.get("/api/img")
async def optimize_image(
    url: str = Query(..., description="Source image URL"),
    w: int = Query(800, ge=50, le=2000, description="Target width"),
    q: int = Query(75, ge=10, le=100, description="WebP quality"),
):
    """Download, resize, convert to WebP, and serve an optimized image."""
    # Cache key based on url + dimensions + quality
    cache_key = hashlib.sha256(f"{url}:{w}:{q}".encode()).hexdigest()

    cached = _cache_get(cache_key)
    if cached:
        return Response(
            content=cached,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=604800, immutable",
                "X-Img-Cache": "HIT",
            },
        )

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url, headers={"User-Agent": "BrightluxxImageProxy/1.0"})
            if resp.status_code != 200:
                return Response(status_code=resp.status_code, content="Upstream error")

            img_bytes = resp.content
            content_type = resp.headers.get("content-type", "")
            if "image" not in content_type and len(img_bytes) < 1000:
                return Response(status_code=400, content="Not an image")

        # Process with Pillow
        img = Image.open(io.BytesIO(img_bytes))

        # Convert RGBA to RGB (WebP supports both, but smaller as RGB for photos)
        if img.mode in ("RGBA", "P"):
            bg = Image.new("RGB", img.size, (0, 0, 0))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize maintaining aspect ratio
        orig_w, orig_h = img.size
        if orig_w > w:
            ratio = w / orig_w
            new_h = int(orig_h * ratio)
            img = img.resize((w, new_h), Image.LANCZOS)

        # Convert to WebP
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=q, method=4)
        webp_bytes = buf.getvalue()

        # Cache it
        _cache_set(cache_key, webp_bytes)

        return Response(
            content=webp_bytes,
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=604800, immutable",
                "X-Img-Cache": "MISS",
                "X-Img-Original-Size": str(len(img_bytes)),
                "X-Img-Optimized-Size": str(len(webp_bytes)),
            },
        )

    except Exception as e:
        # Fallback: redirect to original URL
        return Response(
            status_code=302,
            headers={"Location": url},
        )
