"""Project Planner PDF Generator — generates a complete LED specification report."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from database import leads_col
from email_service import notify_new_lead
from anti_spam import validate_submission_full, check_recaptcha
from utils import get_client_ip
import io

router = APIRouter(prefix="/api")

BLX_BG = colors.HexColor('#0B0B0B')
BLX_GOLD = colors.HexColor('#E5C574')
BLX_GOLD_DARK = colors.HexColor('#B78E3A')
BLX_TEXT = colors.HexColor('#F5F5F5')
BLX_TEXT2 = colors.HexColor('#B0B0B0')
BLX_MUTED = colors.HexColor('#787878')
BLX_PANEL = colors.HexColor('#161616')
BLX_BORDER = colors.HexColor('#2A2A2A')
BLX_WHITE = colors.HexColor('#FFFFFF')
PAGE_W, PAGE_H = A4


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('T', parent=s['Title'], fontSize=22, textColor=BLX_WHITE, fontName='Helvetica-Bold', spaceAfter=4*mm, leading=26))
    s.add(ParagraphStyle('ST', parent=s['Normal'], fontSize=11, textColor=BLX_GOLD, fontName='Helvetica', spaceAfter=8*mm, leading=14))
    s.add(ParagraphStyle('H1', parent=s['Heading1'], fontSize=16, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=4*mm, spaceBefore=8*mm, leading=20))
    s.add(ParagraphStyle('H2', parent=s['Heading2'], fontSize=13, textColor=BLX_WHITE, fontName='Helvetica-Bold', spaceAfter=3*mm, spaceBefore=6*mm, leading=16))
    s.add(ParagraphStyle('B', parent=s['Normal'], fontSize=9.5, textColor=BLX_TEXT2, fontName='Helvetica', spaceAfter=3*mm, leading=14))
    s.add(ParagraphStyle('SM', parent=s['Normal'], fontSize=8, textColor=BLX_MUTED, fontName='Helvetica', leading=10))
    s.add(ParagraphStyle('HL', parent=s['Normal'], fontSize=9.5, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=2*mm, leading=13))
    s.add(ParagraphStyle('FT', parent=s['Normal'], fontSize=7, textColor=BLX_MUTED, fontName='Helvetica', alignment=TA_CENTER))
    return s


def _draw_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BLX_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1)
    canvas.setFillColor(BLX_GOLD)
    canvas.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(BLX_MUTED)
    canvas.drawString(20*mm, 10*mm, "BRIGHTLUXX  |  Premium LED Display Solutions  |  brightluxx.com  |  +971 559 954 274")
    canvas.drawRightString(PAGE_W - 20*mm, 10*mm, f"Page {doc.page}")
    canvas.setFillColor(BLX_GOLD_DARK)
    canvas.rect(0, 0, PAGE_W, 1*mm, fill=1)
    canvas.restoreState()


def _tbl(data, col_widths=None):
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLX_GOLD_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLX_BG),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), BLX_TEXT2),
        ('BACKGROUND', (0, 1), (-1, -1), BLX_PANEL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLX_PANEL, colors.HexColor('#1A1A1A')]),
        ('GRID', (0, 0), (-1, -1), 0.5, BLX_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(style)
    return t


PITCH_POWER = {
    0.9: {'maxW': 620, 'avgW': 220, 'tech': 'COB MicroLED'},
    1.2: {'maxW': 550, 'avgW': 195, 'tech': 'COB / MiP'},
    1.5: {'maxW': 480, 'avgW': 170, 'tech': 'MiP / SMD'},
    1.9: {'maxW': 420, 'avgW': 150, 'tech': 'MiP / SMD'},
    2.5: {'maxW': 360, 'avgW': 130, 'tech': 'SMD'},
    3.9: {'maxW': 300, 'avgW': 110, 'tech': 'SMD'},
    4.8: {'maxW': 280, 'avgW': 100, 'tech': 'SMD'},
    6.0: {'maxW': 450, 'avgW': 160, 'tech': 'SMD Outdoor'},
    8.0: {'maxW': 500, 'avgW': 180, 'tech': 'SMD Outdoor'},
    10.0: {'maxW': 550, 'avgW': 200, 'tech': 'SMD Outdoor'},
    16.0: {'maxW': 600, 'avgW': 220, 'tech': 'SMD Outdoor'},
}

PITCHES = [0.9, 1.2, 1.5, 1.9, 2.5, 3.9, 4.8, 6.0, 8.0, 10.0, 16.0]

INSTALL_METHODS = {
    'indoor': {
        'small': 'Wall-Mounted (Surface)',
        'medium': 'Wall-Mounted or Recessed',
        'large': 'Wall-Mounted with Steel Subframe',
    },
    'outdoor': {
        'small': 'Wall-Mounted (IP65)',
        'medium': 'Ground-Supported Structure',
        'large': 'Ground-Supported with Engineered Foundation',
    },
}


class ProjectPlannerRequest(BaseModel):
    project_name: str = "LED Display Project"
    application: str = "corporate-lobby"
    environment: str = "indoor"
    width: float = 4.0
    height: float = 2.5
    viewing_distance: float = 5.0
    content_type: str = "mixed"
    hours_per_day: int = 12
    brightness: int = 70
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""


def _calc_spec(req: ProjectPlannerRequest):
    content_mult = 0.8 if req.content_type == 'text' else 1.2 if req.content_type == 'video' else 1.0
    ideal_pitch = req.viewing_distance / (3.0 * content_mult)
    best = min(PITCHES, key=lambda p: abs(p - ideal_pitch))
    premium = min([p for p in PITCHES if p < best], key=lambda p: abs(p - ideal_pitch), default=best)

    area = req.width * req.height
    pw = PITCH_POWER.get(best, PITCH_POWER[2.5])
    bright_factor = req.brightness / 100
    max_kw = pw['maxW'] * area / 1000
    avg_kw = pw['avgW'] * area * bright_factor / 1000
    daily_kwh = avg_kw * req.hours_per_day
    monthly_kwh = daily_kwh * 30
    monthly_cost_aed = monthly_kwh * 0.29
    annual_cost_aed = daily_kwh * 365 * 0.29
    heat_btu = pw['maxW'] * area * 3.412
    heat_tons = heat_btu / 12000
    max_amps = pw['maxW'] * area / 220
    breaker = (int(max_amps * 1.25 / 5) + 1) * 5

    size_cat = 'small' if area < 10 else 'large' if area > 30 else 'medium'
    install = INSTALL_METHODS.get(req.environment, INSTALL_METHODS['indoor']).get(size_cat, 'Wall-Mounted')

    cost_sqm = {0.9: 11000, 1.2: 8500, 1.5: 6500, 1.9: 5000, 2.5: 3500, 3.9: 2500, 4.8: 2000, 6.0: 1500, 8.0: 1200, 10.0: 900, 16.0: 750}
    budget_low = cost_sqm.get(best, 1000) * area * 0.8
    budget_high = cost_sqm.get(best, 1000) * area * 1.3

    return {
        'ideal_pitch': round(ideal_pitch, 1),
        'recommended_pitch': best,
        'premium_pitch': premium,
        'tech': pw['tech'],
        'area': round(area, 1),
        'max_kw': round(max_kw, 1),
        'avg_kw': round(avg_kw, 1),
        'daily_kwh': round(daily_kwh, 1),
        'monthly_kwh': round(monthly_kwh, 0),
        'monthly_cost_aed': round(monthly_cost_aed, 0),
        'annual_cost_aed': round(annual_cost_aed, 0),
        'heat_btu': round(heat_btu, 0),
        'heat_tons': round(heat_tons, 1),
        'max_amps': round(max_amps, 1),
        'breaker': breaker,
        'install_method': install,
        'budget_low': round(budget_low, 0),
        'budget_high': round(budget_high, 0),
        'min_viewing': round(best * 1.0, 1),
        'optimal_viewing': round(best * 3.0, 1),
        'max_viewing': round(best * 8.0, 1),
    }


@router.post("/project-planner/calculate")
async def calculate_project(req: ProjectPlannerRequest):
    spec = _calc_spec(req)
    return {"status": "ok", "spec": spec}


@router.post("/project-planner/pdf")
async def generate_project_pdf(req: ProjectPlannerRequest, request: Request):
    spec = _calc_spec(req)
    st = _styles()

    if req.name and req.email:
        ip = get_client_ip(request)
        validation_data = {"name": req.name, "email": req.email, "phone": req.phone}
        is_valid, error_msg, spam_score, geo_data = await validate_submission_full(validation_data, ip)
        if is_valid:
            try:
                await check_recaptcha(request)
            except Exception:
                pass
            lead = {
                "name": req.name,
                "email": req.email,
                "phone": req.phone,
                "company": req.company,
                "source": "project_planner",
                "project_name": req.project_name,
                "application": req.application,
                "message": f"Project Planner: {req.width}m x {req.height}m, {req.environment}, P{spec['recommended_pitch']}, {req.viewing_distance}m distance",
                "spam_score": spam_score,
                "ip": ip,
                "geo": {"country": geo_data.get("country", ""), "city": geo_data.get("city", "")},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await leads_col.insert_one(lead)
            lead.pop("_id", None)
            await notify_new_lead({**lead, "role": "Project Planner Lead"})

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Spacer(1, 12*mm))
    story.append(Paragraph("LED DISPLAY PROJECT", st['T']))
    story.append(Paragraph("SPECIFICATION REPORT", st['ST']))
    story.append(HRFlowable(width="100%", thickness=1, color=BLX_GOLD, spaceAfter=6*mm))

    story.append(Paragraph("PROJECT OVERVIEW", st['H1']))
    project_data = [
        ['Parameter', 'Value'],
        ['Project Name', req.project_name],
        ['Application', req.application.replace('-', ' ').title()],
        ['Environment', req.environment.title()],
        ['Display Dimensions', f'{req.width}m x {req.height}m ({spec["area"]} m²)'],
        ['Viewing Distance', f'{req.viewing_distance}m'],
        ['Content Type', req.content_type.title()],
        ['Operating Hours', f'{req.hours_per_day} hours/day'],
        ['Average Brightness', f'{req.brightness}%'],
    ]
    story.append(_tbl(project_data, [60*mm, 100*mm]))

    story.append(Paragraph("RECOMMENDED SPECIFICATION", st['H1']))
    story.append(Paragraph(f"Based on your {req.viewing_distance}m viewing distance and {req.content_type} content:", st['B']))
    rec_data = [
        ['Specification', 'Value', 'Notes'],
        ['Recommended Pixel Pitch', f'P{spec["recommended_pitch"]}', spec['tech']],
        ['Premium Option', f'P{spec["premium_pitch"]}', 'Finer pitch for enhanced clarity'],
        ['Ideal Pixel Pitch (Calculated)', f'{spec["ideal_pitch"]}mm', 'Based on distance/content formula'],
        ['Minimum Viewing Distance', f'{spec["min_viewing"]}m', 'Below this, pixels visible'],
        ['Optimal Viewing Distance', f'{spec["optimal_viewing"]}m', 'Best image quality zone'],
        ['Maximum Effective Distance', f'{spec["max_viewing"]}m', 'Content still readable'],
    ]
    story.append(_tbl(rec_data, [55*mm, 40*mm, 65*mm]))

    story.append(Paragraph("ELECTRICAL & MEP REQUIREMENTS", st['H1']))
    story.append(Paragraph("Design your electrical infrastructure for maximum power draw with 25% safety margin:", st['B']))
    mep_data = [
        ['Parameter', 'Value', 'Notes'],
        ['Maximum Power Draw', f'{spec["max_kw"]} kW ({int(spec["max_kw"]*1000)}W)', 'Full white at full brightness'],
        ['Average Power Draw', f'{spec["avg_kw"]} kW ({int(spec["avg_kw"]*1000)}W)', f'At {req.brightness}% brightness'],
        ['Daily Energy Usage', f'{spec["daily_kwh"]} kWh', f'{req.hours_per_day} hours/day'],
        ['Monthly Energy Usage', f'{int(spec["monthly_kwh"])} kWh', '30 days'],
        ['Monthly Cost (UAE DEWA)', f'AED {int(spec["monthly_cost_aed"])}', 'At AED 0.29/kWh'],
        ['Annual Cost (UAE DEWA)', f'AED {int(spec["annual_cost_aed"])}', '365 days'],
        ['Maximum Current', f'{spec["max_amps"]}A', 'At 220V single phase'],
        ['Recommended Breaker', f'{spec["breaker"]}A', 'Including 25% safety margin'],
        ['Heat Output', f'{int(spec["heat_btu"]):,} BTU/h', f'{spec["heat_tons"]} tons cooling required'],
    ]
    story.append(_tbl(mep_data, [50*mm, 45*mm, 65*mm]))

    story.append(Paragraph("INSTALLATION RECOMMENDATION", st['H1']))
    story.append(Paragraph(f"Recommended Method: {spec['install_method']}", st['HL']))
    story.append(Paragraph(f"For a {spec['area']} m² {req.environment} display, {spec['install_method'].lower()} is the recommended installation approach. Key requirements:", st['B']))
    if 'recessed' in spec['install_method'].lower():
        story.append(Paragraph("• Niche depth: 250-400mm (panel + service space)", st['B']))
        story.append(Paragraph("• Front-service panels recommended if no rear access", st['B']))
        story.append(Paragraph("• Active ventilation required in enclosed niche", st['B']))
    elif 'ground' in spec['install_method'].lower():
        story.append(Paragraph("• Engineered concrete foundation per soil report", st['B']))
        story.append(Paragraph("• Hot-dip galvanised steel structure for GCC conditions", st['B']))
        story.append(Paragraph("• Municipality signage permit required (allow 4-8 weeks)", st['B']))
    else:
        story.append(Paragraph("• Structural wall: minimum 150mm reinforced concrete", st['B']))
        story.append(Paragraph("• Mounting points: M10/M12 anchors every 600mm", st['B']))
        story.append(Paragraph("• Rear clearance: 600-800mm for service access", st['B']))

    story.append(Paragraph("BUDGETARY ESTIMATE", st['H1']))
    story.append(Paragraph(f"Hardware cost range for {spec['area']} m² P{spec['recommended_pitch']} {req.environment} LED display:", st['B']))
    budget_data = [
        ['Component', 'Estimate (AED)'],
        ['LED Display Hardware', f'AED {int(spec["budget_low"]):,} — {int(spec["budget_high"]):,}'],
        ['Installation & Commissioning', f'AED {int(spec["budget_low"]*0.15):,} — {int(spec["budget_high"]*0.15):,}'],
        ['Content System (Media Server)', f'AED {10000:,} — {25000:,}'],
        ['Structural/MEP Works', f'AED {int(spec["budget_low"]*0.1):,} — {int(spec["budget_high"]*0.1):,}'],
        ['Total Estimated Range', f'AED {int(spec["budget_low"]*1.25 + 10000):,} — {int(spec["budget_high"]*1.25 + 25000):,}'],
    ]
    story.append(_tbl(budget_data, [65*mm, 95*mm]))
    story.append(Paragraph("Note: Estimates are budgetary and subject to final specification, supplier selection, and site conditions.", st['SM']))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLX_GOLD, spaceAfter=4*mm))
    story.append(Paragraph("This specification report was generated by Brightluxx Project Planner.", st['SM']))
    story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%d %B %Y')} | Contact: +971 559 954 274 | brightluxx.com", st['SM']))

    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)
    buf.seek(0)

    filename = f"Brightluxx_Project_Spec_{req.project_name.replace(' ', '_')}.pdf"
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
