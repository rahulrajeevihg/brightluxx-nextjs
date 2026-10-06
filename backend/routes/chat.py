"""AURA — AI-powered specifier chat assistant with dynamic product knowledge."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import uuid
import asyncio

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage
from database import db, products_col
from email_service import send_email, NOTIFICATION_EMAIL

router = APIRouter()

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

chat_sessions_col = db["chat_sessions"]

# ── Dynamic product knowledge cache ──────────────────────────────
_product_knowledge_cache = {"text": "", "updated_at": None}


async def _build_product_knowledge() -> str:
    """Fetch all products from DB and build a compact knowledge string."""
    products = await products_col.find(
        {},
        {"_id": 0, "name": 1, "category": 1, "pixel_pitch": 1, "brightness": 1,
         "application": 1, "tagline": 1, "product_code": 1, "slug": 1,
         "key_specs": 1}
    ).to_list(length=200)

    if not products:
        return ""

    # Group by category
    by_cat = {}
    for p in products:
        cat = p.get("category", "other").replace("-", " ").title()
        by_cat.setdefault(cat, []).append(p)

    lines = ["FULL PRODUCT CATALOG (57 products across 18 categories):\n"]
    for cat, prods in sorted(by_cat.items()):
        lines.append(f"\n{cat} ({len(prods)} products):")
        for p in prods:
            specs = ""
            if p.get("key_specs"):
                specs = " | " + ", ".join(f'{s["label"]}:{s["value"]}' for s in p["key_specs"][:3])
            lines.append(
                f"  - {p['name']} ({p.get('product_code','')}) — "
                f"Pitch:{p.get('pixel_pitch','N/A')}, "
                f"Brightness:{p.get('brightness','N/A')}, "
                f"For: {p.get('application','')[:80]}{specs}"
            )
    return "\n".join(lines)


async def get_product_knowledge() -> str:
    """Return cached product knowledge, refresh every 10 minutes."""
    now = datetime.now(timezone.utc)
    if (
        not _product_knowledge_cache["text"]
        or not _product_knowledge_cache["updated_at"]
        or (now - _product_knowledge_cache["updated_at"]).total_seconds() > 600
    ):
        _product_knowledge_cache["text"] = await _build_product_knowledge()
        _product_knowledge_cache["updated_at"] = now
    return _product_knowledge_cache["text"]


# ── Page context mapping ─────────────────────────────────────────
PAGE_CONTEXT_MAP = {
    "/": "The user is on the homepage — they are a new visitor exploring Brightluxx.",
    "/products": "The user is browsing the full product catalog. Help them find the right product for their needs.",
    "/technology/microled": "The user is reading about MicroLED technology. Focus on MicroLED advantages and use cases.",
    "/technology/cob-led": "The user is reading about COB LED technology. Emphasize durability and anti-glare benefits.",
    "/technology/fine-pitch": "The user is exploring Fine Pitch LED. Discuss 24/7 reliability and corporate applications.",
    "/technology/transparent-led": "The user is looking at Transparent LED. Discuss glass facade applications and transparency rates.",
    "/technology/creative-led": "The user is exploring Creative LED. Discuss curved, cylindrical, and custom shape possibilities.",
    "/technology/3d-anamorphic": "The user is reading about 3D Anamorphic LED. Discuss glasses-free 3D and landmark installations.",
    "/technology/all-in-one-dvled": "The user is looking at All-in-One dvLED. Emphasize plug-and-play simplicity.",
    "/technology/media-facade": "The user is reading about Media Facades. Discuss building-scale outdoor installations.",
    "/technology/mip-led": "The user is exploring MiP LED. Discuss the balance of quality and cost.",
    "/calculator": "The user is on the Screen Calculator. Help them with pixel pitch and resolution calculations.",
    "/budget-estimator": "The user is using the Budget Estimator. Help with cost estimation and budget planning.",
    "/viewing-distance": "The user is on the Viewing Distance Calculator. Help with distance-to-pitch relationships.",
    "/power-estimator": "The user is using the Power Consumption Estimator. Help with electrical specs and MEP planning.",
    "/project-planner": "The user is on the Project Planner wizard. Guide them through the specification process.",
    "/installation-guide": "The user is reading the Installation Method Guide. Help with mounting method selection.",
    "/technology-selector": "The user is on the Technology Selector Quiz. Help them find the right LED technology.",
    "/for-architects": "The user is an architect exploring specifier resources. Recommend CPD sessions and spec packs.",
    "/design-assist": "The user is on the Design Assist page. They're interested in free consultation — encourage booking.",
    "/solutions": "The user is browsing solutions by industry. Help match their industry to the right products.",
    "/case-studies": "The user is reviewing case studies. Reference specific project details and outcomes.",
    "/value-engineering": "The user is a contractor exploring value engineering. Focus on cost optimization strategies.",
    "/spec-substitution": "The user is looking at spec substitution. Help them find equivalent Brightluxx products.",
    "/digital-experience": "The user is exploring digital experience architecture applications.",
    "/cpd-programme": "The user is interested in CPD/Lunch & Learn sessions. Encourage booking for their team.",
    "/knowledge": "The user is in the Knowledge Hub reading technical articles.",
}


def _get_page_context(page_url: str) -> str:
    """Build a context hint based on the user's current page."""
    if not page_url:
        return ""

    # Direct match
    if page_url in PAGE_CONTEXT_MAP:
        return f"\nCURRENT PAGE CONTEXT: {PAGE_CONTEXT_MAP[page_url]}\n"

    # Prefix matches
    for prefix, ctx in PAGE_CONTEXT_MAP.items():
        if page_url.startswith(prefix) and prefix != "/":
            return f"\nCURRENT PAGE CONTEXT: {ctx}\n"

    # Dynamic route patterns
    if "/products/" in page_url:
        slug = page_url.split("/products/")[-1]
        return f"\nCURRENT PAGE CONTEXT: The user is viewing a specific product: {slug}. Provide detailed info about this product.\n"
    if "/technology/" in page_url:
        tech = page_url.split("/technology/")[-1].replace("-", " ").title()
        return f"\nCURRENT PAGE CONTEXT: The user is reading about {tech} technology.\n"
    if "/case-studies/" in page_url:
        case = page_url.split("/case-studies/")[-1].replace("-", " ").title()
        return f"\nCURRENT PAGE CONTEXT: The user is reading the {case} case study.\n"
    if "/digital-experience/" in page_url:
        dea = page_url.split("/digital-experience/")[-1].replace("-", " ").title()
        return f"\nCURRENT PAGE CONTEXT: The user is exploring {dea} digital experience applications.\n"

    return ""


# ── System prompt builder ────────────────────────────────────────

STATIC_SYSTEM_PROMPT = """You are AURA, the AI specification assistant for Brightluxx — a premium LED display company serving architects, consultants, and contractors across the UAE and GCC region.

Your role: Help specifiers choose the right LED display technology for their projects. You provide expert, concise advice on pixel pitch, brightness, mounting, technology selection, and project planning.

PERSONALITY:
- Professional but approachable — like a senior AV consultant
- Concise: keep responses under 150 words unless technical detail is needed
- Always recommend next steps (view a technology page, use a tool, request design assist)
- Reference Brightluxx products and resources when relevant
- When mentioning a page, use the format [Page Name](/path) so users can click through

TECHNOLOGIES (recommend by application):
- MicroLED (P0.4-P0.9): Ultra-premium, luxury hospitality, close viewing (<2m), best contrast/colour → /technology/microled
- COB LED (P0.6-P1.2): High-end retail & hospitality, excellent durability, anti-glare → /technology/cob-led
- MiP LED (P0.7-P1.5): Next-gen packaging, balance of quality and cost → /technology/mip-led
- Fine Pitch LED (P1.2-P2.5): Corporate, command centers, 24/7 operation, best value → /technology/fine-pitch
- All-in-One dvLED (P0.9-P1.8): Healthcare, plug-and-play, no external processors → /technology/all-in-one-dvled
- Transparent LED (P2.6-P10): Glass facades, retail storefronts, 60-90% transparency → /technology/transparent-led
- 3D Anamorphic LED (P2.5-P4.0): Landmark outdoor, glasses-free 3D, corner L-shaped → /technology/3d-anamorphic
- Creative LED (P1.5-P4.0): Curved, cylindrical, ceiling, custom shapes → /technology/creative-led
- Media Facade (P3.9-P25): Building-scale outdoor, integrated with architecture → /technology/media-facade

PIXEL PITCH GUIDE:
- Under 2m viewing: P0.7-P1.2 (MicroLED or COB)
- 2-5m viewing: P1.2-P2.0 (Fine Pitch or COB)
- 5-10m viewing: P2.0-P4.0 (Fine Pitch or Creative)
- 10m+: P4.0-P10+ (Outdoor, Transparent, Media Facade)
- Formula: Minimum pitch (mm) = viewing distance (m) × 0.6

BRIGHTNESS GUIDE:
- Indoor controlled (office, museum): 400-600 nits
- Indoor bright (retail, lobby): 800-1,200 nits
- Semi-outdoor (covered terrace): 1,500-3,000 nits
- Fully outdoor: 5,000-8,000 nits

INTERACTIVE TOOLS (recommend these to users):
- Screen Calculator → /calculator: Calculate pixel pitch, resolution, and total pixels for any display size
- Budget Estimator → /budget-estimator: Get budgetary project cost estimates by technology and size
- Viewing Distance Calculator → /viewing-distance: Find optimal pixel pitch based on viewing distance, or vice versa
- Power Consumption Estimator → /power-estimator: Calculate electrical load, running costs, heat output, breaker/cable sizing for MEP
- Project Planner → /project-planner: All-in-one 4-step wizard combining dimensions, usage, and budget into a downloadable PDF report
- Installation Method Guide → /installation-guide: Compare 6 mounting methods (wall, recessed, ceiling, freestanding, ground, curved) with technical specs
- Technology Selector Quiz → /technology-selector: 5-question interactive quiz to find the right LED technology
- Compare Products → /compare: Side-by-side product comparison tool

SERVICES:
- Free Design Assist → /design-assist: concept consultation, specifications, budget estimates — completely free
- CPD / Lunch & Learn → /cpd-programme: free 1-hour training sessions for architect/consultant teams (6 topics available)
- For Architects Hub → /for-architects: dedicated resources, spec packs, BIM/CAD references, cheat sheets
- Value Engineering → /value-engineering: contractor-focused cost optimization and alternative specifications
- Spec Substitution → /spec-substitution: upload competitor specs, get Brightluxx equivalent recommendations

CASE STUDIES:
- Jumeirah Al Naseem → /case-studies/jumeirah-al-naseem: MicroLED P0.7, hotel lobby, 42 sqm
- Dubai Mall → /case-studies/dubai-mall: COB P0.9, luxury retail, 32 sqm
- ADNOC HQ → /case-studies/adnoc-hq: Fine Pitch P1.2, command center, 54 sqm
- Riyadh Metro → /case-studies/riyadh-metro: Fine Pitch P1.5, transport, 186 displays
- Expo City Dubai → /case-studies/expo-city-dubai: Creative LED P2.6, 360° cylindrical, 280 sqm
- Cleveland Clinic → /case-studies/cleveland-clinic-abu-dhabi: All-in-One dvLED P1.2, hospital, 24 displays
- The View at The Palm → /case-studies/the-view-at-the-palm: Transparent LED P3.9, observation deck, 208 sqm
- KAPSARC → /case-studies/kapsarc-riyadh: 3D Anamorphic P2.5, corporate landmark, 144 sqm

DIGITAL EXPERIENCE APPLICATIONS:
- Media Facades → /digital-experience/media-facades: Building-scale illuminated facades
- Immersive LED Rooms → /digital-experience/immersive-led-rooms: 360° immersive environments
- Retail Experiential Screens → /digital-experience/retail-experiential-screens: Interactive retail displays

IMPORTANT RULES:
1. Never make up specifications or prices — recommend contacting Brightluxx for exact pricing
2. When recommending a technology or tool, include the link in markdown format: [Tool Name](/path)
3. For project-specific questions, recommend the Design Assist service
4. Keep the conversation focused on LED displays and Brightluxx services
5. If asked about competitors, stay neutral and focus on Brightluxx's strengths
6. For pricing questions, say "All our pricing is in AED. For accurate pricing, I recommend our [Budget Estimator](/budget-estimator) or [Design Assist](/design-assist) service"
7. Proactively suggest relevant tools based on the user's question
8. If you know the user's current page, tailor your response to be relevant to that context
"""


async def build_system_prompt(page_url: str = "") -> str:
    """Build the full system prompt with dynamic product data and page context."""
    product_knowledge = await get_product_knowledge()
    page_context = _get_page_context(page_url)

    parts = [STATIC_SYSTEM_PROMPT]
    if product_knowledge:
        parts.append(product_knowledge)
    if page_context:
        parts.append(page_context)
    return "\n".join(parts)


# ── Models ───────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    session_id: str
    message: str
    page_url: Optional[str] = ""


class LeadCapture(BaseModel):
    session_id: str
    name: str
    email: str
    company: str
    role: Optional[str] = ""
    fax: Optional[str] = None


# ── Chat instances with page-aware context ───────────────────────
_chat_instances = {}


async def _get_chat(session_id: str, page_url: str = "") -> LlmChat:
    """Get or create a chat instance. Updates system prompt with page context."""
    system_prompt = await build_system_prompt(page_url)

    if session_id not in _chat_instances:
        _chat_instances[session_id] = LlmChat(
            api_key=OPENAI_KEY,
            session_id=session_id,
            system_message=system_prompt,
        ).with_model("openai", "gpt-5.2")
    else:
        # Update system message with latest page context
        _chat_instances[session_id].system_message = system_prompt

    return _chat_instances[session_id]


# ── Routes ───────────────────────────────────────────────────────

@router.post("/api/chat/message")
async def chat_message(data: ChatMessage):
    if not OPENAI_KEY:
        raise HTTPException(status_code=500, detail="Chat service unavailable.")

    chat = await _get_chat(data.session_id, data.page_url)

    try:
        user_msg = UserMessage(text=data.message)
        response = await chat.send_message(user_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    # Store in DB
    now = datetime.now(timezone.utc)
    await chat_sessions_col.update_one(
        {"session_id": data.session_id},
        {
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": data.message, "ts": now},
                        {"role": "assistant", "content": response, "ts": now},
                    ]
                }
            },
            "$set": {"updated_at": now, "last_page": data.page_url},
            "$setOnInsert": {"created_at": now, "lead_captured": False},
            "$inc": {"message_count": 1},
        },
        upsert=True,
    )

    # Get current message count for lead gate
    session = await chat_sessions_col.find_one(
        {"session_id": data.session_id}, {"_id": 0, "message_count": 1, "lead_captured": 1}
    )
    msg_count = session.get("message_count", 0) if session else 0
    lead_captured = session.get("lead_captured", False) if session else False

    return {
        "response": response,
        "message_count": msg_count,
        "show_lead_form": msg_count >= 3 and not lead_captured,
    }


@router.post("/api/chat/lead")
async def chat_lead_capture(data: LeadCapture, request: Request):
    from database import leads_col
    from email_templates import chat_lead_email
    from anti_spam import validate_submission_full, check_recaptcha
    from utils import get_client_ip

    ip = get_client_ip(request)
    validation_data = {"name": data.name, "email": data.email, "fax": data.fax}
    is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
    if not is_valid:
        if error_msg == "__honeypot__":
            return {"success": True, "message": "Thank you! Continue chatting with AURA."}
        raise HTTPException(status_code=422, detail=error_msg)

    await check_recaptcha(request)

    lead_dict = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email,
        "company": data.company,
        "role": data.role,
        "source": "aura_chat",
        "application": "AURA Chat Assistant",
        "status": "new",
        "notes": f"Chat session: {data.session_id}",
        "spam_score": spam_score,
        "ip": ip,
        "geo": {"country": geo_data.get("country", ""), "city": geo_data.get("city", "")},
        "created_at": datetime.now(timezone.utc),
    }

    await leads_col.insert_one(lead_dict)
    await chat_sessions_col.update_one(
        {"session_id": data.session_id},
        {"$set": {"lead_captured": True, "lead_email": data.email}},
    )

    # Send enhanced email notification
    if NOTIFICATION_EMAIL:
        try:
            email_data = {
                "name": data.name,
                "email": data.email,
                "phone": "",
                "interest": data.role or "General",
                "conversation_summary": f"Chat session ID: {data.session_id}\nCompany: {data.company}",
            }
            subject, html = chat_lead_email(email_data)
            await send_email(NOTIFICATION_EMAIL, subject, html)
        except Exception:
            pass

    return {"success": True, "message": "Thank you! Continue chatting with AURA."}
