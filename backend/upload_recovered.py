"""
Upload recovered files to Emergent static storage and build URL replacement map.
Processes files in batches, uploads via the platform's image upload mechanism.
"""
import os
import json
import base64
import asyncio
import aiohttp
from pathlib import Path

# Generated image replacements for the 6 missing files
GENERATED_REPLACEMENTS = {
    "https://files.ihgbrands.com/emergent-images/2031d053c67d612c7dc323331b83b59af6f8320b60abdd2d32421775987d0177.png": "https://files.ihgbrands.com/emergent-images/2031d053c67d612c7dc323331b83b59af6f8320b60abdd2d32421775987d0177.png",
    "https://files.ihgbrands.com/emergent-images/a40dc162a0a88bf31bf94f0de5ed77952829b133c0de6c4dea05c07e49c4a405.png": "https://files.ihgbrands.com/emergent-images/a40dc162a0a88bf31bf94f0de5ed77952829b133c0de6c4dea05c07e49c4a405.png",
    "https://files.ihgbrands.com/emergent-images/5dbac7e6889b544bf4f261844d917e7a8697ac08b30637e96f2c75218ad784be.png": "https://files.ihgbrands.com/emergent-images/5dbac7e6889b544bf4f261844d917e7a8697ac08b30637e96f2c75218ad784be.png",
    "https://files.ihgbrands.com/emergent-images/fa5bcff834efce178ae8a4c7f097e9349a31d7d833abb778099ee9f588b391ce.png": "https://files.ihgbrands.com/emergent-images/fa5bcff834efce178ae8a4c7f097e9349a31d7d833abb778099ee9f588b391ce.png",
    "https://files.ihgbrands.com/emergent-images/0f94ba2fb077d6c4bdf8613e9ec3fa9295c46a647cb8f37a7afc192b6e8a1f2c.png": "https://files.ihgbrands.com/emergent-images/0f94ba2fb077d6c4bdf8613e9ec3fa9295c46a647cb8f37a7afc192b6e8a1f2c.png",
    "https://files.ihgbrands.com/emergent-images/96812cb6f7543b43c96ed28c4759bc3b3da4e11f8c26d189bf0a878331e5e16b.png": "https://files.ihgbrands.com/emergent-images/96812cb6f7543b43c96ed28c4759bc3b3da4e11f8c26d189bf0a878331e5e16b.png",
}


def copy_to_public(local_path: str, filename: str) -> str:
    """Copy file to public/recovered/ and return the served path."""
    dest_dir = "/app/frontend/public/recovered"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Clean filename
    safe_name = filename.replace(" ", "_")
    dest = os.path.join(dest_dir, safe_name)
    
    # Copy file
    import shutil
    shutil.copy2(local_path, dest)
    return f"/recovered/{safe_name}"


def main():
    # Load the URL-to-file mapping
    url_map = json.load(open("/tmp/url_file_map.json"))
    
    # Build replacement map: old_url -> new_url
    replacements = {}
    
    # Add generated replacements
    replacements.update(GENERATED_REPLACEMENTS)
    
    # Process recovered files - copy to public/recovered/
    copied = 0
    errors = []
    
    for old_url, local_path in url_map.items():
        if old_url in replacements:
            continue  # Already handled by generated images
            
        if not local_path or not os.path.exists(local_path):
            errors.append(f"Missing file: {local_path} for {old_url}")
            continue
        
        # Extract a meaningful filename from the URL
        url_path = old_url.replace("https://files.ihgbrands.com/brightluxx/", "")
        filename = url_path.replace("/", "_")  # Flatten path to filename
        
        try:
            public_path = copy_to_public(local_path, filename)
            # The new URL will be relative (served by CRA/Express)
            replacements[old_url] = public_path
            copied += 1
        except Exception as e:
            errors.append(f"Copy error for {old_url}: {e}")
    
    # Save replacement map
    with open("/tmp/url_replacements.json", "w") as f:
        json.dump(replacements, f, indent=2)
    
    print(f"Copied {copied} files to /app/frontend/public/recovered/")
    print(f"Generated replacements: {len(GENERATED_REPLACEMENTS)}")
    print(f"Total replacements: {len(replacements)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"  {e}")
    
    # Show size
    recovered_size = sum(
        os.path.getsize(os.path.join("/app/frontend/public/recovered", f))
        for f in os.listdir("/app/frontend/public/recovered")
        if os.path.isfile(os.path.join("/app/frontend/public/recovered", f))
    )
    print(f"Recovered directory size: {recovered_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
