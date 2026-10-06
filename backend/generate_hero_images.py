#!/usr/bin/env python3
"""
Generate Luxury LED Display Hero Images using Gemini Nano Banana
Creates cinematic, premium visuals for Brightluxx website
"""

import asyncio
import os
import base64
from datetime import datetime
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv('/app/backend/.env')

# Image generation prompts for different sections
IMAGE_PROMPTS = [
    {
        "name": "hero_main",
        "prompt": """Create a breathtaking, cinematic photograph of a massive premium LED display wall in a luxury Dubai setting. 
        The display shows vibrant, crystal-clear content with perfect color accuracy. 
        Ultra-modern corporate environment with marble floors, gold accents, and dramatic lighting. 
        The LED wall is sleek, seamless, and absolutely stunning. 
        Professional photography, 8K quality, shallow depth of field, golden hour lighting.
        Photorealistic, luxury commercial photography style."""
    },
    {
        "name": "microled_display",
        "prompt": """Professional product photography of an ultra-fine pitch MicroLED display panel showing incredible detail and clarity.
        Close-up shot revealing the precision of micro-LED pixels, with a luxury product on screen (high-end watch or jewelry).
        Dark premium background with gold accents and dramatic side lighting.
        Studio photography, macro lens, premium commercial quality, photorealistic.
        Emphasize precision, technology, and luxury."""
    },
    {
        "name": "outdoor_dooh_dubai",
        "prompt": """Stunning photograph of a giant outdoor LED billboard on Sheikh Zayed Road, Dubai at golden hour.
        Modern skyscrapers in background, the LED display is incredibly bright and clear even in daylight.
        Shows premium brand advertisement on the screen.
        Professional architectural photography, 8K quality, dramatic sky, luxury cityscape.
        Photorealistic, emphasize scale and premium positioning."""
    },
    {
        "name": "transparent_led_retail",
        "prompt": """Luxury retail store window with transparent LED film display showing dynamic content while maintaining visibility through the glass.
        High-end fashion store in Dubai mall, models visible behind the transparent screen.
        Natural daylight mixed with LED content creating a magical effect.
        Professional architectural photography, premium retail environment, photorealistic.
        Gold and black color scheme visible in store design."""
    },
    {
        "name": "3d_holographic_mall",
        "prompt": """Futuristic 3D holographic LED display in a luxury shopping mall creating jaw-dropping visual effects.
        Content appears to float in mid-air (anamorphic 3D effect), shoppers amazed in background.
        Premium mall environment with marble, gold accents, dramatic lighting.
        Professional commercial photography, 8K quality, photorealistic.
        Emphasize wow-factor and premium technology."""
    },
    {
        "name": "corporate_boardroom",
        "prompt": """Ultra-luxury corporate boardroom with a seamless LED video wall displaying data visualizations.
        Executive meeting in progress, premium furniture, floor-to-ceiling windows with Dubai skyline view.
        The LED wall is massive, perfectly color-calibrated, showing sharp graphs and presentations.
        Professional interior photography, cinematic lighting, photorealistic.
        Gold accents and premium materials throughout."""
    },
    {
        "name": "event_stage_led",
        "prompt": """Spectacular concert stage with massive LED walls creating an immersive visual experience.
        Dynamic colorful content on displays, professional stage lighting, dramatic atmosphere.
        High-end production value, seen from audience perspective.
        Professional event photography, 8K quality, vibrant colors, photorealistic.
        Emphasize scale, impact, and premium technology."""
    },
    {
        "name": "control_room_led",
        "prompt": """State-of-the-art control room with multiple fine-pitch LED video walls displaying real-time data.
        Operators monitoring screens, premium command center environment.
        Dark room with ambient blue and gold lighting, ultra-modern technology.
        Professional architectural photography, cinematic mood, photorealistic.
        Emphasize precision, reliability, and advanced technology."""
    }
]


async def generate_image(prompt_config: dict, api_key: str, output_dir: str) -> bool:
    """Generate a single image using Nano Banana"""
    
    name = prompt_config["name"]
    prompt = prompt_config["prompt"]
    
    print(f"\n{'='*60}")
    print(f"🎨 Generating: {name}")
    print(f"{'='*60}")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        # Initialize chat for image generation
        chat = LlmChat(
            api_key=api_key,
            session_id=f"image_gen_{name}_{int(datetime.now().timestamp())}",
            system_message="You are an expert luxury commercial photographer specializing in LED display technology."
        )
        
        # Configure for image generation
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        # Create message
        msg = UserMessage(text=prompt)
        
        # Generate image
        print("⏳ Generating image...")
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            print(f"✅ Generated {len(images)} image(s)")
            
            # Save the first image
            img = images[0]
            image_bytes = base64.b64decode(img['data'])
            
            output_path = os.path.join(output_dir, f"{name}.png")
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"💾 Saved to: {output_path}")
            print(f"📊 Size: {len(image_bytes) / 1024:.1f} KB")
            
            if text:
                print(f"📝 AI Comment: {text[:100]}")
            
            return True
        else:
            print(f"❌ No images generated")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {name}: {str(e)}")
        return False


async def main():
    """Generate all hero images"""
    
    print("\n" + "="*60)
    print("BRIGHTLUXX LUXURY IMAGE GENERATION")
    print("Using Gemini Nano Banana")
    print("="*60)
    
    # Get API key
    api_key = os.getenv('EMERGENT_LLM_KEY')
    if not api_key:
        print("❌ EMERGENT_LLM_KEY not found in environment")
        return
    
    print(f"✅ API Key loaded")
    
    # Create output directory
    output_dir = "/app/frontend/public/generated"
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Generate images
    results = []
    for i, prompt_config in enumerate(IMAGE_PROMPTS, 1):
        print(f"\n[{i}/{len(IMAGE_PROMPTS)}]")
        success = await generate_image(prompt_config, api_key, output_dir)
        results.append({
            "name": prompt_config["name"],
            "success": success
        })
        
        # Small delay between generations
        if i < len(IMAGE_PROMPTS):
            await asyncio.sleep(2)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r["success"])
    print(f"✅ Successfully generated: {successful}/{len(results)} images")
    
    if successful < len(results):
        print(f"\n⚠️  Failed generations:")
        for r in results:
            if not r["success"]:
                print(f"   - {r['name']}")
    
    print(f"\n📁 Images saved to: {output_dir}")
    print(f"{'='*60}\n")
    
    return successful == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
