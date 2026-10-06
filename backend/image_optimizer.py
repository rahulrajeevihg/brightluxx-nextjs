"""
Image optimization utilities for CDN uploads.
Auto-resizes, compresses, and converts images to WebP before uploading.
"""
from PIL import Image
from io import BytesIO

MAX_WIDTH = 1920
MAX_HEIGHT = 1920
WEBP_QUALITY = 82
JPEG_QUALITY = 82
THUMBNAIL_WIDTH = 400
THUMBNAIL_QUALITY = 60


def optimize_image(content: bytes, max_width: int = MAX_WIDTH, max_height: int = MAX_HEIGHT, quality: int = WEBP_QUALITY) -> tuple[bytes, str]:
    """
    Optimize an image: resize if oversized, convert to WebP, compress.
    
    Returns:
        tuple of (optimized_bytes, new_extension)
    """
    try:
        img = Image.open(BytesIO(content))
    except Exception:
        return content, ""

    original_format = img.format or "PNG"

    # Skip SVG and GIF (animated) — return as-is
    if original_format in ("SVG", "GIF"):
        return content, ""

    # Convert RGBA/P to RGB for WebP (with white background)
    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Resize if larger than max dimensions
    w, h = img.size
    if w > max_width or h > max_height:
        img.thumbnail((max_width, max_height), Image.LANCZOS)

    # Save as WebP
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=4)
    optimized = buf.getvalue()

    # Only use optimized if it's actually smaller
    if len(optimized) < len(content):
        return optimized, ".webp"

    # If WebP is somehow larger, try saving in original format with compression
    buf2 = BytesIO()
    if original_format in ("JPEG", "JPG"):
        img.save(buf2, format="JPEG", quality=quality, optimize=True)
    elif original_format == "PNG":
        img.save(buf2, format="PNG", optimize=True)
    else:
        img.save(buf2, format="WEBP", quality=quality, method=4)
        return buf2.getvalue(), ".webp"

    fallback = buf2.getvalue()
    if len(fallback) < len(content):
        ext = ".jpg" if original_format in ("JPEG", "JPG") else f".{original_format.lower()}"
        return fallback, ext

    return content, ""


def create_thumbnail(content: bytes, width: int = THUMBNAIL_WIDTH, quality: int = THUMBNAIL_QUALITY) -> tuple[bytes, str]:
    """
    Create a small thumbnail for blur-up placeholders.
    
    Returns:
        tuple of (thumbnail_bytes, extension)
    """
    try:
        img = Image.open(BytesIO(content))
    except Exception:
        return b"", ""

    if img.format in ("SVG", "GIF"):
        return b"", ""

    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Resize to thumbnail width maintaining aspect ratio
    w, h = img.size
    ratio = width / w
    new_h = int(h * ratio)
    img = img.resize((width, new_h), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=4)
    return buf.getvalue(), ".webp"


def get_image_info(content: bytes) -> dict:
    """Get image dimensions and format info."""
    try:
        img = Image.open(BytesIO(content))
        return {
            "width": img.size[0],
            "height": img.size[1],
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(content),
        }
    except Exception:
        return {"size_bytes": len(content)}
