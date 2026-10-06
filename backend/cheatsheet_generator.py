"""
Cheat Sheet & BIM Reference PDF Generator.
Creates 1-page branded PDF cheat sheets and BIM technical reference docs.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

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
    s.add(ParagraphStyle('CS_Title', fontSize=18, textColor=BLX_WHITE, fontName='Helvetica-Bold', spaceAfter=2*mm, leading=22))
    s.add(ParagraphStyle('CS_Subtitle', fontSize=9, textColor=BLX_GOLD, fontName='Helvetica', spaceAfter=4*mm, leading=12))
    s.add(ParagraphStyle('CS_H2', fontSize=11, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=2*mm, spaceBefore=4*mm, leading=14))
    s.add(ParagraphStyle('CS_Body', fontSize=8, textColor=BLX_TEXT2, fontName='Helvetica', spaceAfter=2*mm, leading=11))
    s.add(ParagraphStyle('CS_Small', fontSize=7, textColor=BLX_MUTED, fontName='Helvetica', leading=9))
    s.add(ParagraphStyle('CS_Footer', fontSize=6, textColor=BLX_MUTED, fontName='Helvetica', alignment=TA_CENTER))
    return s


def _draw_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BLX_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1)
    canvas.setFillColor(BLX_GOLD)
    canvas.rect(0, PAGE_H - 2*mm, PAGE_W, 2*mm, fill=1)
    canvas.setFont('Helvetica', 6)
    canvas.setFillColor(BLX_MUTED)
    canvas.drawString(15*mm, 8*mm, "BRIGHTLUXX  |  brightluxx.com  |  +971 4 258 5754")
    canvas.setFillColor(BLX_GOLD_DARK)
    canvas.rect(0, 0, PAGE_W, 1*mm, fill=1)
    canvas.restoreState()


def _make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    if not col_widths:
        col_widths = [PAGE_W * 0.85 / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLX_GOLD_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLX_BG),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('TEXTCOLOR', (0, 1), (-1, -1), BLX_TEXT2),
        ('BACKGROUND', (0, 1), (-1, -1), BLX_PANEL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLX_PANEL, colors.HexColor('#1A1A1A')]),
        ('GRID', (0, 0), (-1, -1), 0.5, BLX_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_pixel_pitch_cheatsheet(path):
    s = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []
    story.append(Paragraph("PIXEL PITCH CHEAT SHEET", s['CS_Title']))
    story.append(Paragraph("Quick reference for viewing distance, resolution & cost | BRIGHTLUXX", s['CS_Subtitle']))
    story.append(_make_table(
        ['Pitch', 'Min Distance', 'Comfort Dist.', 'Resolution/sqm', 'Cost/sqm', 'Best For'],
        [
            ['P0.7', '1.1m', '1.8m', '2M pixels', '$12-20K', 'Control room, boardroom'],
            ['P0.9', '1.4m', '2.3m', '1.2M pixels', '$8-14K', 'Corporate, broadcast'],
            ['P1.2', '1.8m', '3.0m', '694K pixels', '$4-8K', 'Lobby, showroom, retail'],
            ['P1.5', '2.3m', '3.8m', '444K pixels', '$2.5-5K', 'Hotel lobby, meeting room'],
            ['P1.9', '2.9m', '4.8m', '277K pixels', '$1.8-3.5K', 'Conference, retail'],
            ['P2.5', '3.8m', '6.3m', '160K pixels', '$1.2-2.5K', 'Mall, ballroom'],
            ['P3.9', '5.9m', '9.8m', '66K pixels', '$800-1.8K', 'Event, large indoor'],
            ['P4.8', '7.2m', '12m', '43K pixels', '$600-1.5K', 'Outdoor, stadium'],
            ['P6', '9m', '15m', '28K pixels', '$500-1.2K', 'Billboard, facade'],
            ['P10', '15m', '25m', '10K pixels', '$300-700', 'Highway, rooftop'],
        ],
        [28*mm, 22*mm, 22*mm, 25*mm, 22*mm, 42*mm]
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("FORMULAS", s['CS_H2']))
    story.append(Paragraph("Minimum viewing distance = Pixel pitch (mm) x 1.5 = distance in metres", s['CS_Body']))
    story.append(Paragraph("Comfortable viewing distance = Pixel pitch (mm) x 2.5 = distance in metres", s['CS_Body']))
    story.append(Paragraph("Pixels per sqm = (1000 / pitch)^2", s['CS_Body']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("UAE/GCC NOTES", s['CS_H2']))
    story.append(Paragraph("Add 20-30% brightness headroom for thermal derating in 45C+ ambient. For outdoor: min 5,500 nits, 7,000+ for south/west facing. Always specify front-service for recessed installations.", s['CS_Body']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Prices are indicative 2026 UAE market. Hardware only — multiply by 1.3-1.4x for total installed cost.", s['CS_Small']))
    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)


def generate_brightness_cheatsheet(path):
    s = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []
    story.append(Paragraph("BRIGHTNESS &amp; NITS CHEAT SHEET", s['CS_Title']))
    story.append(Paragraph("LED display brightness specification for UAE/GCC environments | BRIGHTLUXX", s['CS_Subtitle']))
    story.append(_make_table(
        ['Environment', 'Ambient Lux', 'Min Nits', 'Recommended', 'Notes'],
        [
            ['Dark room / Cinema', '0-50 lux', '100-300', '200-500', 'Low brightness, high contrast priority'],
            ['Meeting room', '300-500 lux', '300-600', '600-800', 'Standard office lighting'],
            ['Hotel lobby', '500-1000 lux', '600-1000', '800-1200', 'Mixed lighting, feature wall'],
            ['Retail store', '800-1500 lux', '1000-1500', '1200-1800', 'Bright retail environments'],
            ['Mall atrium', '1000-2000 lux', '1500-2000', '2000-2500', 'Skylights, mixed natural light'],
            ['Semi-outdoor canopy', '2000-10000 lux', '2500-3500', '3500-5000', 'UAE covered walkways'],
            ['Outdoor (shade)', '10k-30k lux', '3500-5500', '5500-7000', 'North-facing, shaded'],
            ['Outdoor (direct sun)', '50k-100k lux', '5500-7000', '7000-10000', 'South/west-facing Dubai'],
        ],
        [35*mm, 25*mm, 20*mm, 25*mm, 56*mm]
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("UAE-SPECIFIC GUIDANCE", s['CS_H2']))
    story.append(Paragraph("Dubai direct sun reaches 100,000+ lux. Specify 7,000-10,000 nits for south/west-facing outdoor. Add 20-30% headroom for thermal derating at 45C+. East-facing is easier — morning sun is less intense.", s['CS_Body']))
    story.append(Paragraph("For semi-outdoor (parking canopies, covered walkways, pool decks): IP54 minimum + 3,500-5,000 nits.", s['CS_Body']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("POWER IMPACT", s['CS_H2']))
    story.append(Paragraph("Higher brightness = higher power consumption and heat generation. Outdoor 10,000-nit displays draw 600-800W/sqm vs indoor 250W/sqm. Ensure HVAC compensates for heat output.", s['CS_Body']))
    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)


def generate_cob_mip_smd_cheatsheet(path):
    s = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []
    story.append(Paragraph("COB vs MiP vs SMD CHEAT SHEET", s['CS_Title']))
    story.append(Paragraph("LED display technology comparison for specifiers | BRIGHTLUXX", s['CS_Subtitle']))
    story.append(_make_table(
        ['Specification', 'SMD', 'MiP', 'COB'],
        [
            ['Technology', 'Surface Mount Device', 'MicroLED in Package', 'Chip on Board'],
            ['Contrast Ratio', '3,000-5,000:1', '8,000-12,000:1', '15,000-20,000:1'],
            ['Surface', 'Individual LED bumps', 'Smooth, low-profile', 'Fully smooth, matte'],
            ['Pixel Pitch Range', 'P1.2 - P10+', 'P0.7 - P2.5', 'P0.4 - P1.9'],
            ['Repairability', 'Single LED replace', 'Single LED replace', 'Module-level swap'],
            ['Durability', 'Moderate (exposed LED)', 'High (protected)', 'Highest (fully encapsulated)'],
            ['Power Consumption', 'Baseline', '-20% vs SMD', '-40% vs SMD'],
            ['Lifespan', '50,000-80,000 hrs', '80,000-100,000 hrs', '100,000+ hrs'],
            ['Cost (relative)', '$', '$$', '$$$'],
            ['Best Application', 'Budget, large format', 'Mid-premium, versatile', 'Premium, close-view'],
        ],
        [30*mm, 40*mm, 40*mm, 40*mm]
    ))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("WHEN TO SPECIFY EACH", s['CS_H2']))
    story.append(Paragraph("<b>SMD:</b> Pixel pitch P2.5+, budget-sensitive projects, outdoor, rental/event, large viewing distances.", s['CS_Body']))
    story.append(Paragraph("<b>MiP:</b> P0.9-P2.5, best value for premium applications. Excellent contrast with easy serviceability. Ideal for lobby, retail, showroom.", s['CS_Body']))
    story.append(Paragraph("<b>COB:</b> P0.4-P1.5, highest image quality. Best for control rooms, broadcast studios, luxury hospitality, boardrooms. Module-level service acceptable.", s['CS_Body']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("VALUE ENGINEERING TIP", s['CS_H2']))
    story.append(Paragraph("MiP delivers 85-90% of COB visual quality at 30-40% lower cost. Most consultants accept MiP as equivalent to COB for viewing distances above 2m.", s['CS_Body']))
    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)


def generate_outdoor_checklist(path):
    s = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []
    story.append(Paragraph("OUTDOOR LED DURABILITY CHECKLIST", s['CS_Title']))
    story.append(Paragraph("UAE/GCC outdoor specification checklist — heat, dust, IP, service | BRIGHTLUXX", s['CS_Subtitle']))

    checks = [
        ("IP RATING", [
            ("IP65 front, IP54 rear (minimum)", "Protects against Gulf sand/dust + rain"),
            ("IP65 full if exposed to direct rain", "Pool areas, unprotected facades"),
            ("Conformal coating on PCBs", "Salt air corrosion protection (coastal)"),
        ]),
        ("THERMAL MANAGEMENT", [
            ("Operating range: -10C to 60C", "UAE summer ambient reaches 50C+"),
            ("Smart fan speed control", "Temperature-based automatic adjustment"),
            ("Thermal protection auto-dimming", "Reduces brightness to prevent damage"),
            ("Rear ventilation gap: min 200mm", "Essential for heat dissipation"),
        ]),
        ("BRIGHTNESS & VISIBILITY", [
            ("Minimum 5,500 nits for shade", "North-facing, canopy, covered areas"),
            ("7,000-10,000 nits for direct sun", "South and west-facing installations"),
            ("Anti-glare coating / matte surface", "Reduces reflection, improves readability"),
            ("Auto-brightness sensor", "Adjusts to ambient light automatically"),
        ]),
        ("STRUCTURAL & ELECTRICAL", [
            ("Wind load calculation (local code)", "UAE can have sandstorms, strong gusts"),
            ("Stainless steel or galvanized structure", "Prevents corrosion in Gulf humidity"),
            ("Surge protection (SPD)", "Essential — UAE has power fluctuations"),
            ("Dedicated electrical circuit + 20%", "Separate DB, MCBs, RCDs"),
        ]),
        ("SERVICE ACCESS", [
            ("Front-service cabinets preferred", "Allows maintenance from scaffold/cherry picker"),
            ("Tool-free module removal", "Reduces service time and risk"),
            ("Spare parts: 5% modules, 2x PSU", "Same-batch modules for colour match"),
            ("Remote monitoring capability", "Alert on failures, temperature, status"),
        ]),
    ]

    for section_title, items in checks:
        story.append(Paragraph(section_title, s['CS_H2']))
        rows = []
        for item, note in items:
            rows.append([item, note])
        t = Table([['Requirement', 'Notes']] + rows, colWidths=[80*mm, 80*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLX_GOLD_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), BLX_BG),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TEXTCOLOR', (0, 1), (0, -1), BLX_TEXT),
            ('TEXTCOLOR', (1, 1), (1, -1), BLX_TEXT2),
            ('BACKGROUND', (0, 1), (-1, -1), BLX_PANEL),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLX_PANEL, colors.HexColor('#1A1A1A')]),
            ('GRID', (0, 0), (-1, -1), 0.5, BLX_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 2*mm))

    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)


def generate_bim_reference(bim_type, path):
    """Generate a BIM/CAD technical reference PDF with dimensions and specs."""
    s = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []

    configs = {
        "all-in-one-dvled": {
            "title": "ALL-IN-ONE dvLED DISPLAY",
            "subtitle": "Technical Reference — Dimensions, Mounting & Electrical | BRIGHTLUXX",
            "sizes": [
                ['Model', 'Pitch', 'Size', 'Resolution', 'Weight', 'Depth', 'Power'],
                ['AIO-110', 'P1.2', '110" (2440x1372mm)', '3840x2160 (4K)', '65 kg', '42mm', '350W'],
                ['AIO-136', 'P1.5', '136" (3008x1692mm)', '3840x2160 (4K)', '80 kg', '42mm', '450W'],
                ['AIO-163', 'P1.8', '163" (3610x2030mm)', '3840x2160 (4K)', '95 kg', '42mm', '550W'],
                ['AIO-216', 'P1.2', '216" (4800x2700mm)', '7680x4320 (8K)', '150 kg', '42mm', '850W'],
            ],
            "mounting": "Wall bracket (supplied). Min wall: reinforced concrete or steel stud with bracing. Rear gap: 50mm minimum for ventilation. Front-service: all modules accessible from front.",
            "electrical": "Single-phase 220V. Dedicated 16A circuit (110/136) or 32A circuit (163/216). Include surge protection.",
        },
        "fine-pitch-wall": {
            "title": "FINE-PITCH LED VIDEO WALL",
            "subtitle": "Technical Reference — Cabinet Dimensions & Wall Configurations | BRIGHTLUXX",
            "sizes": [
                ['Cabinet', 'Pitch', 'Dimensions', 'Resolution', 'Weight', 'Power/cab'],
                ['FP-500', 'P0.9', '600x337.5mm', '667x375', '5.5 kg', '75W'],
                ['FP-500', 'P1.2', '600x337.5mm', '500x281', '5.5 kg', '65W'],
                ['FP-500', 'P1.5', '600x337.5mm', '400x225', '5.5 kg', '60W'],
                ['FP-500', 'P1.9', '600x337.5mm', '320x180', '5.2 kg', '55W'],
            ],
            "mounting": "Steel mounting frame (custom fabricated per wall size). Floor-standing or wall-mounted. Rear service: 600mm gap minimum. Front service: cabinets are magnetically attached, tool-free removal.",
            "electrical": "Three-phase for walls >10sqm. Per cabinet: 55-75W. Total = cabinets x power. Add 20% headroom.",
        },
        "outdoor-cabinet": {
            "title": "OUTDOOR LED CABINET",
            "subtitle": "Technical Reference — Cabinet Dimensions & Weather Protection | BRIGHTLUXX",
            "sizes": [
                ['Cabinet', 'Pitch', 'Dimensions', 'Resolution', 'Weight', 'IP', 'Nits'],
                ['OD-960', 'P3.9', '960x960mm', '246x246', '32 kg', 'IP65', '5500'],
                ['OD-960', 'P4.8', '960x960mm', '200x200', '30 kg', 'IP65', '6500'],
                ['OD-960', 'P6', '960x960mm', '160x160', '28 kg', 'IP65', '7000'],
                ['OD-960', 'P8', '960x960mm', '120x120', '26 kg', 'IP65', '8000'],
                ['OD-960', 'P10', '960x960mm', '96x96', '24 kg', 'IP65', '10000'],
            ],
            "mounting": "Steel structure with anti-corrosion coating. Wind load: designed for 120 km/h. Foundation: concrete pad or building structural steel. Front service: module removal from front with quick-lock.",
            "electrical": "Three-phase 380V for large installations. Per sqm: 600-800W peak. Dual power input per cabinet. Surge protection required.",
        },
        "transparent-film": {
            "title": "TRANSPARENT LED FILM",
            "subtitle": "Technical Reference — Window-Mount Transparent Display | BRIGHTLUXX",
            "sizes": [
                ['Model', 'Pitch', 'Transparency', 'Thickness', 'Weight/sqm', 'Nits', 'Power/sqm'],
                ['TF-3.9', 'P3.9', '85%', '3mm', '3.5 kg', '3000', '200W'],
                ['TF-7.8', 'P7.8', '90%', '3mm', '3.0 kg', '4000', '180W'],
                ['TF-10', 'P10', '92%', '3mm', '2.8 kg', '5000', '160W'],
            ],
            "mounting": "Direct adhesive to glass surface (no frame required). Glass requirement: min 10mm tempered glass. Can be curved to glass radius. Controller box mounted at sill or ceiling (200x100x50mm per sqm).",
            "electrical": "Single-phase 220V. Low power consumption. Per sqm: 160-200W. Controller requires CAT6 network connection.",
        },
    }

    cfg = configs.get(bim_type, configs["all-in-one-dvled"])

    story.append(Paragraph(cfg["title"], s['CS_Title']))
    story.append(Paragraph(cfg["subtitle"], s['CS_Subtitle']))

    story.append(Paragraph("PRODUCT SPECIFICATIONS", s['CS_H2']))
    headers = cfg["sizes"][0]
    rows = cfg["sizes"][1:]
    widths = [(PAGE_W - 30*mm) / len(headers)] * len(headers)
    story.append(_make_table(headers, rows, widths))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("MOUNTING & STRUCTURE", s['CS_H2']))
    story.append(Paragraph(cfg["mounting"], s['CS_Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("ELECTRICAL REQUIREMENTS", s['CS_H2']))
    story.append(Paragraph(cfg["electrical"], s['CS_Body']))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("NOTES FOR ARCHITECTS", s['CS_H2']))
    story.append(Paragraph("This reference document provides typical dimensions and specifications. Actual dimensions vary by manufacturer and configuration. Contact Brightluxx for project-specific technical drawings, Revit families, and structural calculations.", s['CS_Body']))
    story.append(Paragraph("For custom Revit families or AutoCAD blocks: WhatsApp +971 4 258 5754 or email info@brightluxx.com", s['CS_Small']))

    doc.build(story, onFirstPage=_draw_bg, onLaterPages=_draw_bg)


CHEATSHEET_GENERATORS = {
    "pixel-pitch-cheatsheet": generate_pixel_pitch_cheatsheet,
    "brightness-cheatsheet": generate_brightness_cheatsheet,
    "cob-mip-smd-cheatsheet": generate_cob_mip_smd_cheatsheet,
    "outdoor-checklist": generate_outdoor_checklist,
}

BIM_TYPES = ["all-in-one-dvled", "fine-pitch-wall", "outdoor-cabinet", "transparent-film"]
