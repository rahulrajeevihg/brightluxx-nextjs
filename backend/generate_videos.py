"""Generate photorealistic hero videos using Sora 2 for Brightluxx homepage.
Uses cinematographer-level prompts optimized for maximum realism."""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

# PROMPT 1: Dubai skyline → premium indoor LED video wall
# Technique: One clear camera move (slow aerial push-in), defined lighting (golden hour),
# specific lens reference (anamorphic), authentic atmospheric details
VIDEO_1_PROMPT = (
    "Luxury commercial shot on ARRI Alexa Mini with anamorphic lens. "
    "Slow aerial drone push-in over Dubai Marina at golden hour. "
    "The Burj Khalifa and surrounding skyscrapers are visible in warm amber sunlight "
    "with long shadows and atmospheric haze over the Persian Gulf. "
    "A massive LED screen on a modern glass building facade displays vivid blue ocean waves. "
    "Camera continues pushing forward through the city. "
    "Natural lens flares from the setting sun. "
    "Warm color grading with teal shadows and amber highlights. "
    "Photorealistic, 4K cinematic quality, shallow depth of field, smooth stabilized movement."
)

# PROMPT 2: Premium mall LED signage → luxury villa outdoor LED
# Technique: One subject (LED display), one camera move (steady gimbal tracking),
# defined lighting (soft retail interior), authentic details (reflections, materials)
VIDEO_2_PROMPT = (
    "Luxury real estate commercial shot on 35mm film. "
    "Steady gimbal tracking shot inside a premium Dubai shopping mall with polished marble floors. "
    "A large curved LED video wall displays vibrant luxury fashion content, "
    "casting colorful reflections on the glossy floor. "
    "Elegant shoppers walk past in soft focus. "
    "Warm overhead spotlights illuminate the space with soft ambient fill light. "
    "The architecture features brushed gold accents and floor-to-ceiling glass. "
    "Natural reflections on surfaces. "
    "Photorealistic, cinematic color grading, warm tones, shallow depth of field, "
    "professional commercial quality."
)

OUTPUT_DIR = "/app/frontend/public/videos"


def generate_video(prompt, output_path, video_num):
    print(f"\n{'='*60}")
    print(f"Starting Video {video_num} generation...")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Output: {output_path}")
    print(f"{'='*60}")
    start = time.time()

    video_gen = OpenAIVideoGeneration(api_key=os.environ["EMERGENT_LLM_KEY"])
    video_bytes = video_gen.text_to_video(
        prompt=prompt,
        model="sora-2",
        size="1280x720",
        duration=12,
        max_wait_time=900,
    )

    if video_bytes:
        video_gen.save_video(video_bytes, output_path)
        elapsed = time.time() - start
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Video {video_num} SAVED: {output_path} ({size_mb:.1f} MB) in {elapsed:.0f}s")
        return True
    else:
        print(f"Video {video_num} FAILED after {time.time()-start:.0f}s")
        return False


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    which = sys.argv[1] if len(sys.argv) > 1 else "both"

    if which in ("1", "both"):
        generate_video(VIDEO_1_PROMPT, f"{OUTPUT_DIR}/hero-video-1.mp4", 1)

    if which in ("2", "both"):
        generate_video(VIDEO_2_PROMPT, f"{OUTPUT_DIR}/hero-video-2.mp4", 2)

    print("\nAll done!")
