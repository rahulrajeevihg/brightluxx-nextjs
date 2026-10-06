"""
Brightluxx Spec Pack PDF Generator
Creates branded, professional specification pack PDFs using ReportLab.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

# Brand colors
BLX_BG = colors.HexColor('#0B0B0B')
BLX_GOLD = colors.HexColor('#E5C574')
BLX_GOLD_DARK = colors.HexColor('#B78E3A')
BLX_TEXT = colors.HexColor('#F5F5F5')
BLX_TEXT2 = colors.HexColor('#B0B0B0')
BLX_MUTED = colors.HexColor('#787878')
BLX_PANEL = colors.HexColor('#161616')
BLX_BORDER = colors.HexColor('#2A2A2A')
BLX_WHITE = colors.HexColor('#FFFFFF')
BLX_DARK = colors.HexColor('#111111')

PAGE_W, PAGE_H = A4


def _styles():
    """Create branded paragraph styles."""
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('BLX_Title', parent=s['Title'], fontSize=22, textColor=BLX_WHITE, fontName='Helvetica-Bold', spaceAfter=4*mm, leading=26))
    s.add(ParagraphStyle('BLX_Subtitle', parent=s['Normal'], fontSize=11, textColor=BLX_GOLD, fontName='Helvetica', spaceAfter=8*mm, leading=14))
    s.add(ParagraphStyle('BLX_H1', parent=s['Heading1'], fontSize=16, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=4*mm, spaceBefore=8*mm, leading=20))
    s.add(ParagraphStyle('BLX_H2', parent=s['Heading2'], fontSize=13, textColor=BLX_WHITE, fontName='Helvetica-Bold', spaceAfter=3*mm, spaceBefore=6*mm, leading=16))
    s.add(ParagraphStyle('BLX_H3', parent=s['Heading3'], fontSize=11, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=2*mm, spaceBefore=4*mm, leading=14))
    s.add(ParagraphStyle('BLX_Body', parent=s['Normal'], fontSize=9.5, textColor=BLX_TEXT2, fontName='Helvetica', spaceAfter=3*mm, leading=14))
    s.add(ParagraphStyle('BLX_Bullet', parent=s['Normal'], fontSize=9, textColor=BLX_TEXT2, fontName='Helvetica', spaceAfter=1.5*mm, leading=12, leftIndent=12*mm, bulletIndent=6*mm))
    s.add(ParagraphStyle('BLX_Small', parent=s['Normal'], fontSize=8, textColor=BLX_MUTED, fontName='Helvetica', leading=10))
    s.add(ParagraphStyle('BLX_Highlight', parent=s['Normal'], fontSize=9.5, textColor=BLX_GOLD, fontName='Helvetica-Bold', spaceAfter=2*mm, leading=13))
    s.add(ParagraphStyle('BLX_Footer', parent=s['Normal'], fontSize=7, textColor=BLX_MUTED, fontName='Helvetica', alignment=TA_CENTER))
    return s


def _draw_bg(canvas, doc):
    """Draw dark background and branding on every page."""
    canvas.saveState()
    canvas.setFillColor(BLX_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1)
    # Top gold line
    canvas.setFillColor(BLX_GOLD)
    canvas.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1)
    # Footer
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(BLX_MUTED)
    canvas.drawString(20*mm, 10*mm, "BRIGHTLUXX  |  Premium LED Display Solutions  |  brightluxx.com  |  +971 4 258 5754")
    canvas.drawRightString(PAGE_W - 20*mm, 10*mm, f"Page {doc.page}")
    # Bottom gold line
    canvas.setFillColor(BLX_GOLD_DARK)
    canvas.rect(0, 0, PAGE_W, 1*mm, fill=1)
    canvas.restoreState()


def _cover_page(canvas, doc):
    """Draw a branded cover page."""
    canvas.saveState()
    canvas.setFillColor(BLX_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1)
    # Gold accent bar
    canvas.setFillColor(BLX_GOLD)
    canvas.rect(0, PAGE_H - 5*mm, PAGE_W, 5*mm, fill=1)
    # Gold side stripe
    canvas.setFillColor(BLX_GOLD_DARK)
    canvas.rect(20*mm, PAGE_H * 0.3, 3*mm, PAGE_H * 0.4, fill=1)
    # Bottom gold line
    canvas.setFillColor(BLX_GOLD)
    canvas.rect(0, 0, PAGE_W, 2*mm, fill=1)
    # Footer on cover
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(BLX_MUTED)
    canvas.drawCentredString(PAGE_W / 2, 15*mm, "brightluxx.com  |  +971 4 258 5754  |  Dubai, UAE")
    canvas.restoreState()


def _make_table(headers, rows, col_widths=None):
    """Create a branded data table."""
    data = [headers] + rows
    if not col_widths:
        col_widths = [150*mm / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), BLX_PANEL),
        ('TEXTCOLOR', (0, 0), (-1, 0), BLX_GOLD),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), BLX_TEXT2),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BLX_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BLX_BG, BLX_DARK]),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
    ]
    t.setStyle(TableStyle(style))
    return t


def _gold_hr():
    return HRFlowable(width="100%", thickness=0.5, color=BLX_GOLD_DARK, spaceAfter=4*mm, spaceBefore=4*mm)


def _generate_cob_mip_smd(path):
    """COB vs MiP vs SMD Technology Comparison Spec Pack."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    # Cover
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph("COB vs MiP vs SMD", styles['BLX_Title']))
    story.append(Paragraph("LED Technology Comparison &amp; Specification Guide", styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("A comprehensive guide for architects, consultants, and AV specifiers.<br/>Covers technology fundamentals, specification criteria, and UAE/GCC application guidance.", styles['BLX_Body']))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("2026 Edition  |  For Professional Use Only", styles['BLX_Small']))
    story.append(PageBreak())

    # TOC
    story.append(Paragraph("CONTENTS", styles['BLX_H1']))
    for i, title in enumerate([
        "Technology Overview",
        "Head-to-Head Comparison Table",
        "When to Specify Each Technology",
        "UAE & GCC Climate Considerations",
        "Viewing Distance & Pixel Pitch Matrix",
        "What to Ask the Vendor",
        "Specification Checklist",
    ], 1):
        story.append(Paragraph(f"{i}.  {title}", styles['BLX_Body']))
    story.append(PageBreak())

    # Section 1
    story.append(Paragraph("1. TECHNOLOGY OVERVIEW", styles['BLX_H1']))

    story.append(Paragraph("SMD (Surface Mount Device)", styles['BLX_H2']))
    story.append(Paragraph("SMD is the traditional and most widely deployed LED display technology. Individual red, green, and blue LED chips are packaged into a single surface-mount component, then soldered onto a PCB. SMD has been the industry standard for over 15 years and remains the most cost-effective option for pixel pitches above 1.5mm.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Individual RGB LEDs in plastic packages soldered onto PCB", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Mature supply chain, lowest cost per sqm for pitches > 1.5mm", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Easy single-LED repair in field (technician can replace one LED)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Contrast ratio typically 3,000:1 to 5,000:1", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Susceptible to moisture and dust ingress at LED level", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Best for: outdoor displays, rental/events, large-pitch indoor (P2.5+)", styles['BLX_Bullet']))

    story.append(Paragraph("COB (Chip-on-Board)", styles['BLX_H2']))
    story.append(Paragraph("COB eliminates individual LED packaging entirely. Bare LED chips are mounted directly onto the PCB substrate and encapsulated with a resin/epoxy layer. This produces a smooth, seamless surface with dramatically better contrast and protection. COB is the premium choice for fine-pitch applications where image quality is paramount.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Bare LED chips bonded directly to PCB, covered by protective resin", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Superior contrast ratio: 15,000:1 to 20,000:1+", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Inherently dust-proof and moisture-resistant (IP40+ at panel level)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> 30-40% lower power consumption vs equivalent SMD", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> 160+ degree wide viewing angle with no colour shift", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Repair is module-level (not single LED) - higher repair cost", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Best for: control rooms, broadcast, boardrooms, home cinema, medical", styles['BLX_Bullet']))

    story.append(Paragraph("MiP (Mini LED in Package)", styles['BLX_H2']))
    story.append(Paragraph("MiP represents the newest generation, combining advantages of both SMD and COB. Mini LED chips are individually packaged (like SMD) but at a much smaller scale, achieving COB-like contrast while maintaining field serviceability. MiP is the fastest-growing LED technology in 2025-2026.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Mini LED chips in ultra-compact individual packages", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Contrast ratio: 8,000:1 to 12,000:1 (approaching COB)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Single-LED field repair possible (unlike COB)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> 25-35% power savings vs traditional SMD", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Compatible with active-matrix driving (smoother gradients)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Mass production scaling rapidly - costs decreasing", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Best for: retail flagships, broadcast, medical imaging, defence", styles['BLX_Bullet']))
    story.append(PageBreak())

    # Section 2
    story.append(Paragraph("2. HEAD-TO-HEAD COMPARISON", styles['BLX_H1']))
    story.append(_make_table(
        ['Specification', 'SMD', 'COB', 'MiP'],
        [
            ['Min Pixel Pitch', '0.9mm', '0.4mm', '0.4mm'],
            ['Contrast Ratio', '3,000-5,000:1', '15,000-20,000:1', '8,000-12,000:1'],
            ['Black Uniformity', 'Fair (LED caps visible)', 'Excellent (smooth surface)', 'Very Good'],
            ['Power Consumption', 'Baseline (100%)', '60-70% of SMD', '65-75% of SMD'],
            ['Viewing Angle', '140-160 degrees', '160+ degrees', '160+ degrees'],
            ['Moisture Protection', 'Low (exposed LEDs)', 'High (resin coating)', 'Medium-High'],
            ['Dust Resistance', 'Low', 'Excellent', 'Good'],
            ['Field Repair', 'Single LED', 'Module replacement', 'Single LED'],
            ['Repair Cost', 'Low', 'Medium-High', 'Low-Medium'],
            ['Lifespan', '50,000-80,000 hrs', '100,000+ hrs', '80,000-100,000 hrs'],
            ['Cost per sqm (P1.2)', 'AED 7,500-12,000', 'AED 15,000-25,000', 'AED 10,000-18,000'],
            ['Colour Accuracy', 'Good (DCI-P3 80%+)', 'Excellent (DCI-P3 95%+)', 'Very Good (DCI-P3 90%+)'],
            ['Refresh Rate', '1,920-3,840 Hz', '3,840-7,680 Hz', '3,840-7,680 Hz'],
            ['UAE Suitability', 'Good for outdoor', 'Best for indoor premium', 'Versatile indoor'],
        ],
        [42*mm, 36*mm, 36*mm, 36*mm],
    ))
    story.append(PageBreak())

    # Section 3
    story.append(Paragraph("3. WHEN TO SPECIFY EACH TECHNOLOGY", styles['BLX_H1']))
    story.append(Paragraph("Choose SMD when:", styles['BLX_H3']))
    story.append(Paragraph("<bullet>&bull;</bullet> Budget is the primary constraint", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Pixel pitch is 1.5mm or larger", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Application is outdoor or rental/events", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> On-site single-LED repair is required", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Content is mostly text, simple graphics, or from a distance", styles['BLX_Bullet']))

    story.append(Paragraph("Choose COB when:", styles['BLX_H3']))
    story.append(Paragraph("<bullet>&bull;</bullet> Image quality and contrast are paramount", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Pixel pitch is sub-1.2mm (control rooms, boardrooms)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Environment is dusty or humid (warehouse, industrial)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Display will be on 16+ hours/day (lifespan matters)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Content includes fine detail, medical imaging, or broadcast", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Budget allows for premium specification", styles['BLX_Bullet']))

    story.append(Paragraph("Choose MiP when:", styles['BLX_H3']))
    story.append(Paragraph("<bullet>&bull;</bullet> You want COB-level quality with SMD-level serviceability", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Fine pitch (0.7-1.5mm) with field repair requirement", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Retail flagship or brand experience environment", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Camera-friendly applications (broadcast, streaming)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Mid-high budget with long-term total cost optimization", styles['BLX_Bullet']))
    story.append(PageBreak())

    # Section 4
    story.append(Paragraph("4. UAE &amp; GCC CLIMATE CONSIDERATIONS", styles['BLX_H1']))
    story.append(Paragraph("The Gulf region presents unique challenges for LED display specification:", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Ambient temperatures regularly exceed 45C in summer - ensure operating range covers -10C to +55C", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Fine sand and dust require IP54+ rating for semi-outdoor; IP65+ for outdoor", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Direct sunlight intensity in Dubai exceeds 100,000 lux - outdoor displays need 5,000+ nits minimum", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Air-conditioned interiors can create condensation on external-facing glass - consider anti-condensation heating for transparent LED", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Power supply must handle 220V/50Hz with surge protection (common power fluctuations)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Front-service access is critical for high-rise installations common in Dubai/Abu Dhabi", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Salt-air corrosion near coastal areas (JBR, Palm, Saadiyat) - specify marine-grade connectors", styles['BLX_Bullet']))
    story.append(_gold_hr())

    # Section 5
    story.append(Paragraph("5. VIEWING DISTANCE &amp; PIXEL PITCH MATRIX", styles['BLX_H1']))
    story.append(Paragraph("Minimum comfortable viewing distance = Pixel Pitch (mm) x 1.5 metres", styles['BLX_Highlight']))
    story.append(_make_table(
        ['Application', 'Viewing Distance', 'Recommended Pitch', 'Technology'],
        [
            ['Control Room (24/7)', '1.5 - 3m', 'P0.7 - P1.2', 'COB / MiP'],
            ['Boardroom / Meeting', '2 - 5m', 'P1.2 - P1.8', 'COB / MiP'],
            ['Retail Close-up', '1 - 3m', 'P0.9 - P1.5', 'MiP / COB'],
            ['Lobby Feature Wall', '3 - 8m', 'P1.5 - P2.5', 'MiP / SMD'],
            ['Auditorium / Ballroom', '5 - 15m', 'P2.5 - P3.9', 'SMD / MiP'],
            ['Outdoor Billboard', '10 - 50m', 'P4 - P10', 'SMD'],
            ['Stadium / Arena', '20 - 100m', 'P6 - P16', 'SMD'],
        ],
        [40*mm, 30*mm, 35*mm, 35*mm],
    ))
    story.append(PageBreak())

    # Section 6
    story.append(Paragraph("6. WHAT TO ASK THE VENDOR", styles['BLX_H1']))
    story.append(Paragraph("Use this checklist when evaluating LED display proposals:", styles['BLX_Body']))
    questions = [
        "What is the actual measured contrast ratio (ANSI, not sequential)?",
        "What LED chip brand is used? (Nationstar, Cree, Epistar, etc.)",
        "What is the driver IC? (MBI, Chipone, etc.) - affects grayscale and refresh",
        "Is front-service available without removing the entire module?",
        "What is the actual power consumption at 60% white (not max)?",
        "What redundancy is built in? (dual power, dual data, hot-swap)",
        "What is the warranty period and what does it cover?",
        "Can you provide on-site spare modules (5-10% of total)?",
        "What control system is included? (Novastar, Colorlight, Brompton)",
        "Is calibration included at install? What about re-calibration schedule?",
        "What is the module/cabinet size? Does it fit my structural grid?",
        "What are the heat dissipation requirements? (HVAC impact)",
        "What certifications do you hold? (CE, FCC, UL, EMC, RoHS)",
        "Do you provide BIM/CAD files for architectural coordination?",
        "What is the lead time for this specific configuration?",
    ]
    for i, q in enumerate(questions, 1):
        story.append(Paragraph(f"<bullet>{i:02d}.</bullet> {q}", styles['BLX_Bullet']))
    story.append(PageBreak())

    # Section 7
    story.append(Paragraph("7. SPECIFICATION CHECKLIST", styles['BLX_H1']))
    story.append(Paragraph("Include these items in your LED display specification:", styles['BLX_Body']))
    checklist = [
        ("Display Type", "SMD / COB / MiP / Transparent"),
        ("Pixel Pitch", "e.g., P1.2, P2.5, P4"),
        ("Active Area", "Width x Height in mm"),
        ("Resolution", "Pixels horizontal x vertical"),
        ("Brightness", "Nits (cd/m2) - specify calibrated value"),
        ("Contrast Ratio", "ANSI contrast, not dynamic/sequential"),
        ("Refresh Rate", "Hz - specify for camera-friendly if needed"),
        ("Colour Temp", "Default and adjustable range (e.g., 3200K-9300K)"),
        ("IP Rating", "Front and rear separately"),
        ("Operating Temp", "Range in Celsius"),
        ("Power", "Max and typical W/sqm"),
        ("Service Access", "Front / Rear / Both"),
        ("Redundancy", "Power, data, receiving card"),
        ("Control System", "Brand and model"),
        ("Cabinet / Module", "Dimensions, material, weight"),
        ("Mounting", "Method, structural requirements"),
        ("Content Input", "HDMI, DVI, SDI, IP/streaming"),
        ("Certifications", "CE, FCC, UL, RoHS, EMC"),
        ("Warranty", "Period, coverage, SLA"),
        ("Spare Parts", "% included, availability commitment"),
    ]
    story.append(_make_table(
        ['Item', 'Specify'],
        [[c[0], c[1]] for c in checklist],
        [45*mm, 105*mm],
    ))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))
    story.append(Paragraph("For custom specification assistance, contact our technical team for a design-assist consultation.", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


def _generate_pixel_pitch(path):
    """Pixel Pitch Specification Guide."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph("Pixel Pitch Guide", styles['BLX_Title']))
    story.append(Paragraph("Specification Guide for LED Display Resolution &amp; Viewing Distance", styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("A practical reference for architects, consultants, and AV designers to correctly specify pixel pitch based on viewing distance, content type, and application requirements.", styles['BLX_Body']))
    story.append(PageBreak())

    story.append(Paragraph("WHAT IS PIXEL PITCH?", styles['BLX_H1']))
    story.append(Paragraph("Pixel pitch is the distance (in millimeters) between the center of one LED pixel and the center of the adjacent pixel. It is the single most important specification that determines image resolution, optimal viewing distance, and cost.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Smaller pixel pitch = higher resolution = closer viewing distance = higher cost", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Larger pixel pitch = lower resolution = farther viewing distance = lower cost", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Over-specifying pitch wastes budget; under-specifying creates visible pixelation", styles['BLX_Bullet']))
    story.append(_gold_hr())

    story.append(Paragraph("THE VIEWING DISTANCE FORMULA", styles['BLX_H1']))
    story.append(Paragraph("Minimum Viewing Distance (metres) = Pixel Pitch (mm) x 1.5", styles['BLX_Highlight']))
    story.append(Paragraph("Comfortable Viewing Distance (metres) = Pixel Pitch (mm) x 2.5", styles['BLX_Highlight']))
    story.append(Paragraph("For content with fine text or detail, use the minimum. For video/graphics content viewed casually, the comfortable distance applies.", styles['BLX_Body']))
    story.append(_gold_hr())

    story.append(Paragraph("PIXEL PITCH BY APPLICATION", styles['BLX_H1']))
    story.append(_make_table(
        ['Application', 'Typical Distance', 'Pitch Range', 'Resolution Need'],
        [
            ['Control/Command Room', '1-3m', 'P0.7 - P1.2', 'Ultra-high (data/text)'],
            ['Executive Boardroom', '2-4m', 'P0.9 - P1.5', 'Very high (presentations)'],
            ['Retail Close-up Display', '1-3m', 'P0.9 - P1.5', 'Very high (product detail)'],
            ['Hotel/Corp Lobby', '3-8m', 'P1.5 - P2.5', 'High (branding/video)'],
            ['Conference/Ballroom', '5-12m', 'P2.5 - P3.9', 'Medium (presentation)'],
            ['Mall Atrium/Signage', '5-15m', 'P2.5 - P4', 'Medium (video/promo)'],
            ['Outdoor Street Level', '5-20m', 'P3.9 - P6', 'Standard (video)'],
            ['Highway Billboard', '20-80m', 'P6 - P10', 'Basic (large graphics)'],
            ['Stadium Perimeter', '30-100m', 'P8 - P16', 'Basic (scores/video)'],
        ],
        [40*mm, 28*mm, 28*mm, 42*mm],
    ))
    story.append(PageBreak())

    story.append(Paragraph("RESOLUTION CALCULATOR", styles['BLX_H1']))
    story.append(Paragraph("To calculate the resolution of your LED wall:", styles['BLX_Body']))
    story.append(Paragraph("Horizontal Pixels = Screen Width (mm) / Pixel Pitch (mm)", styles['BLX_Highlight']))
    story.append(Paragraph("Vertical Pixels = Screen Height (mm) / Pixel Pitch (mm)", styles['BLX_Highlight']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Example: A 4m wide x 2.25m tall wall at P1.5:", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Horizontal: 4000mm / 1.5mm = 2,667 pixels", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Vertical: 2250mm / 1.5mm = 1,500 pixels", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Total resolution: 2667 x 1500 = 4 million pixels (approx. 4K)", styles['BLX_Bullet']))
    story.append(_gold_hr())

    story.append(Paragraph("CONTENT TYPE CONSIDERATIONS", styles['BLX_H1']))
    story.append(_make_table(
        ['Content Type', 'Min Resolution', 'Pitch Guidance'],
        [
            ['Text-heavy (data dashboards)', 'Full HD (1920x1080)', 'Use pitch formula strictly'],
            ['Video playback', '720p acceptable', 'Can use larger pitch'],
            ['Mixed (presentations)', 'Full HD recommended', 'Use pitch formula'],
            ['Medical/technical imaging', '4K+ preferred', 'Smallest pitch in budget'],
            ['Architectural/branding', '720p-1080p', 'Prioritise size over resolution'],
        ],
        [45*mm, 40*mm, 55*mm],
    ))
    story.append(PageBreak())

    story.append(Paragraph("COST vs PITCH TRADE-OFF", styles['BLX_H1']))
    story.append(Paragraph("Approximate cost relationship (2026 market):", styles['BLX_Body']))
    story.append(_make_table(
        ['Pixel Pitch', 'Cost/sqm (AED)', 'Typical Technology'],
        [
            ['P0.7', 'AED 30,000 - 55,000', 'COB / MiP'],
            ['P0.9', 'AED 22,000 - 40,000', 'COB / MiP'],
            ['P1.2', 'AED 10,000 - 22,000', 'COB / MiP / SMD'],
            ['P1.5', 'AED 6,500 - 14,000', 'MiP / SMD'],
            ['P2.5', 'AED 3,000 - 7,000', 'SMD'],
            ['P3.9', 'AED 2,000 - 5,000', 'SMD'],
            ['P4-P6', 'AED 1,500 - 4,000', 'SMD (outdoor)'],
            ['P8-P10', 'AED 900 - 2,200', 'SMD (outdoor)'],
        ],
        [35*mm, 40*mm, 65*mm],
    ))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


def _generate_brightness_nits(path):
    """Brightness & Nits Guide for GCC Climate."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph("Brightness &amp; Nits Guide", styles['BLX_Title']))
    story.append(Paragraph("LED Display Brightness Specification for UAE &amp; GCC Environments", styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("How to correctly specify LED display brightness for indoor, semi-outdoor, and full outdoor installations in the Gulf region's extreme light conditions.", styles['BLX_Body']))
    story.append(PageBreak())

    story.append(Paragraph("UNDERSTANDING NITS (cd/m2)", styles['BLX_H1']))
    story.append(Paragraph("A 'nit' (candela per square metre, cd/m2) measures luminance - how bright a display appears to the human eye. In the GCC region, extreme ambient light demands significantly higher brightness than temperate climates.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> 1 nit = 1 candela per square metre (cd/m2)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> A laptop screen is typically 300-500 nits", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> A premium indoor LED wall is 600-1,200 nits", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> A Dubai outdoor billboard needs 5,000-8,000+ nits", styles['BLX_Bullet']))
    story.append(_gold_hr())

    story.append(Paragraph("BRIGHTNESS BY ENVIRONMENT (GCC SPECIFIC)", styles['BLX_H1']))
    story.append(_make_table(
        ['Environment', 'Ambient Light', 'Min Nits', 'Recommended', 'Notes'],
        [
            ['Dark room / cinema', '< 50 lux', '200', '400-600', 'Lower = better contrast'],
            ['Office / conference', '300-500 lux', '400', '600-800', 'Anti-glare coating helps'],
            ['Retail (indoor)', '500-1,000 lux', '800', '1,000-1,500', 'Bright retail lighting'],
            ['Mall atrium', '1,000-2,000 lux', '1,200', '1,500-2,500', 'Skylights add ambient'],
            ['Lobby (glass facade)', '2,000-5,000 lux', '2,000', '2,500-3,500', 'Direct sun through glass'],
            ['Semi-outdoor canopy', '5,000-20,000 lux', '3,000', '4,000-5,000', 'Shaded but open air'],
            ['Outdoor (shaded)', '10,000-30,000 lux', '4,000', '5,000-6,000', 'Under overhang'],
            ['Full outdoor Dubai', '60,000-120,000 lux', '5,500', '7,000-10,000', 'Direct Gulf sun'],
        ],
        [32*mm, 25*mm, 18*mm, 25*mm, 38*mm],
    ))
    story.append(PageBreak())

    story.append(Paragraph("GCC CLIMATE FACTORS", styles['BLX_H1']))
    story.append(Paragraph("Heat Impact on Brightness", styles['BLX_H2']))
    story.append(Paragraph("LED brightness degrades at high temperatures. In the GCC where ambient can reach 50C and panel surface temperatures can exceed 70C:", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Specify 20-30% higher brightness than minimum to account for thermal derating", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Ensure the display has active thermal management (fans or convection)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Operating temperature range must cover -10C to +55C minimum", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Request brightness at 40C ambient, not just at 25C lab conditions", styles['BLX_Bullet']))

    story.append(Paragraph("Sand and Dust", styles['BLX_H2']))
    story.append(Paragraph("<bullet>&bull;</bullet> Fine desert sand can block airflow and coat surfaces, reducing apparent brightness", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Specify IP54+ minimum for any semi-outdoor location", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Include maintenance cleaning schedule in specification", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> COB technology is inherently better in dusty environments", styles['BLX_Bullet']))

    story.append(Paragraph("Solar Orientation", styles['BLX_H2']))
    story.append(Paragraph("<bullet>&bull;</bullet> West and south-facing outdoor displays in UAE receive the most intense sunlight", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Add 30% to brightness spec for west-facing installations", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> North-facing displays can use lower brightness (significant cost saving)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Consider auto-brightness sensors to reduce power during evening/night", styles['BLX_Bullet']))
    story.append(PageBreak())

    story.append(Paragraph("POWER &amp; HEAT CONSIDERATIONS", styles['BLX_H1']))
    story.append(Paragraph("Higher brightness = more power = more heat. Plan HVAC and electrical accordingly:", styles['BLX_Body']))
    story.append(_make_table(
        ['Brightness Range', 'Typical Power', 'Heat Output', 'HVAC Impact'],
        [
            ['600-1,200 nits', '200-400 W/sqm', '~300 BTU/sqm/hr', 'Minimal'],
            ['1,200-2,500 nits', '400-600 W/sqm', '~500 BTU/sqm/hr', 'Moderate'],
            ['2,500-5,000 nits', '600-900 W/sqm', '~800 BTU/sqm/hr', 'Significant'],
            ['5,000-10,000 nits', '900-1,500 W/sqm', '~1,200 BTU/sqm/hr', 'Major planning needed'],
        ],
        [35*mm, 30*mm, 32*mm, 40*mm],
    ))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


def _generate_ip_rating(path):
    """IP Rating & Front Serviceability Guide."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph("IP Rating &amp; Serviceability", styles['BLX_Title']))
    story.append(Paragraph("Protection Ratings &amp; Service Access Guide for LED Displays", styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Understanding IP (Ingress Protection) ratings and service access requirements for LED displays in UAE and GCC environments.", styles['BLX_Body']))
    story.append(PageBreak())

    story.append(Paragraph("IP RATING EXPLAINED", styles['BLX_H1']))
    story.append(Paragraph("IP ratings follow the format IPXY where X = solid particle protection (0-6) and Y = liquid protection (0-9).", styles['BLX_Body']))
    story.append(_make_table(
        ['Rating', 'Solids Protection', 'Liquids Protection'],
        [
            ['IP20', 'Fingers (>12.5mm)', 'None'],
            ['IP30', 'Tools (>2.5mm)', 'None'],
            ['IP40', 'Wires (>1mm)', 'None'],
            ['IP43', 'Wires (>1mm)', 'Spraying water (60 deg)'],
            ['IP54', 'Dust-protected', 'Splashing water'],
            ['IP65', 'Dust-tight', 'Water jets'],
            ['IP67', 'Dust-tight', 'Temporary immersion'],
            ['IP68', 'Dust-tight', 'Prolonged immersion'],
        ],
        [30*mm, 50*mm, 55*mm],
    ))
    story.append(PageBreak())

    story.append(Paragraph("IP RATING BY APPLICATION (UAE/GCC)", styles['BLX_H1']))
    story.append(_make_table(
        ['Application', 'Min Front IP', 'Min Rear IP', 'Notes'],
        [
            ['Indoor (A/C room)', 'IP20', 'IP20', 'Standard indoor panels'],
            ['Indoor (lobby/atrium)', 'IP30', 'IP20', 'Public area, splash risk'],
            ['Indoor (F&B / kitchen)', 'IP43', 'IP20', 'Steam and grease'],
            ['Semi-outdoor (canopy)', 'IP54', 'IP43', 'Dubai dust + occasional rain'],
            ['Outdoor (permanent)', 'IP65', 'IP54', 'Full weather exposure'],
            ['Outdoor (coastal)', 'IP65', 'IP65', 'Salt air corrosion risk'],
            ['Outdoor (ground level)', 'IP65', 'IP54', 'Cleaning water exposure'],
            ['Pool/water feature', 'IP67', 'IP65', 'Splash zone proximity'],
        ],
        [38*mm, 25*mm, 25*mm, 45*mm],
    ))
    story.append(_gold_hr())

    story.append(Paragraph("FRONT vs REAR SERVICE ACCESS", styles['BLX_H1']))
    story.append(Paragraph("Front-service displays allow module replacement from the viewing side. This is critical when rear access is impossible.", styles['BLX_Body']))
    story.append(Paragraph("Specify FRONT SERVICE when:", styles['BLX_H3']))
    story.append(Paragraph("<bullet>&bull;</bullet> Display is flush-mounted against a wall (no rear access corridor)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> High-rise building facade installation", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Ceiling-hung installation over public areas", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Architectural integration where rear void is sealed", styles['BLX_Bullet']))
    story.append(Paragraph("Specify REAR SERVICE when:", styles['BLX_H3']))
    story.append(Paragraph("<bullet>&bull;</bullet> A service corridor (min 600mm deep) exists behind the display", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Indoor stadium/arena perimeter boards", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Free-standing or double-sided totems", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Budget is constrained (rear-service panels cost less)", styles['BLX_Bullet']))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


def _generate_refresh_rate(path):
    """Refresh Rate & Camera-Friendly Guide."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph("Refresh Rate &amp; Camera Guide", styles['BLX_Title']))
    story.append(Paragraph("Eliminating Flicker, Banding &amp; Moire in LED Displays", styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("A guide for specifying LED displays that look perfect on camera - critical for broadcast, social media content, and any space where visitors photograph or film.", styles['BLX_Body']))
    story.append(PageBreak())

    story.append(Paragraph("WHY REFRESH RATE MATTERS", styles['BLX_H1']))
    story.append(Paragraph("Refresh rate (measured in Hz) determines how many times per second the display redraws. Low refresh rates cause visible flicker and horizontal scan lines when viewed through cameras.", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Human eye: flicker visible below ~60Hz", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Phone cameras: banding visible below ~1,920Hz", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Professional cameras: artefacts visible below ~3,840Hz", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Slow-motion cameras: require 7,680Hz+", styles['BLX_Bullet']))
    story.append(_gold_hr())

    story.append(Paragraph("REFRESH RATE BY APPLICATION", styles['BLX_H1']))
    story.append(_make_table(
        ['Application', 'Min Refresh', 'Recommended', 'Why'],
        [
            ['Office / internal use', '1,920 Hz', '3,840 Hz', 'Staff may photograph'],
            ['Retail / public', '3,840 Hz', '3,840 Hz', 'Customers film constantly'],
            ['Hotel lobby / F&B', '3,840 Hz', '3,840 Hz', 'Social media photos'],
            ['Broadcast studio', '3,840 Hz', '7,680 Hz', 'Professional cameras'],
            ['Event/stage (live)', '3,840 Hz', '7,680 Hz', 'Broadcast + phones'],
            ['Museum / gallery', '3,840 Hz', '3,840 Hz', 'Visitor photography'],
            ['Outdoor advertising', '1,920 Hz', '3,840 Hz', 'Camera distance helps'],
        ],
        [35*mm, 25*mm, 28*mm, 42*mm],
    ))
    story.append(PageBreak())

    story.append(Paragraph("MOIRE PATTERN PREVENTION", styles['BLX_H1']))
    story.append(Paragraph("Moire patterns (wavy interference lines) appear when a camera's sensor grid interferes with the LED pixel grid. Prevention strategies:", styles['BLX_Body']))
    story.append(Paragraph("<bullet>&bull;</bullet> Higher refresh rate is the primary solution", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> COB/MiP panels with smooth surfaces produce less moire than SMD", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Smaller pixel pitch reduces moire visibility on camera", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Anti-moire diffuser films can be applied (slight brightness reduction)", styles['BLX_Bullet']))
    story.append(Paragraph("<bullet>&bull;</bullet> Processing systems like Novastar and Brompton have anti-moire settings", styles['BLX_Bullet']))
    story.append(_gold_hr())

    story.append(Paragraph("GREYSCALE &amp; BIT DEPTH", styles['BLX_H1']))
    story.append(Paragraph("Bit depth determines how many brightness levels each colour channel can display. Higher bit depth = smoother gradients, no banding.", styles['BLX_Body']))
    story.append(_make_table(
        ['Bit Depth', 'Greyscale Levels', 'Colours', 'Use Case'],
        [
            ['14-bit', '16,384 per channel', '4.4 trillion', 'Standard indoor'],
            ['16-bit', '65,536 per channel', '281 trillion', 'Premium / broadcast'],
            ['18-bit', '262,144 per channel', '~18 quadrillion', 'Ultra-premium / medical'],
        ],
        [25*mm, 35*mm, 35*mm, 42*mm],
    ))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


# Additional spec packs for applications
def _generate_application_pack(pack_id, path):
    """Generate application-specific spec pack."""
    styles = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    configs = {
        "retail-hospitality": {
            "title": "Retail &amp; Hospitality",
            "subtitle": "LED Display Specification for Shops, Hotels, Restaurants &amp; Malls",
            "sections": [
                ("SHOPFRONT WINDOW DISPLAY", [
                    ("Type", "Transparent LED Film or GOB Panel"),
                    ("Pixel Pitch", "P2.5 - P3.9 (transparent), P1.5 - P2.5 (standard)"),
                    ("Brightness", "3,000 - 5,000 nits (must compete with daylight)"),
                    ("Transparency", "60-90% for transparent; N/A for standard"),
                    ("IP Rating", "IP43 front minimum (cleaning spray)"),
                    ("Refresh Rate", "3,840 Hz (customers photograph constantly)"),
                    ("Content", "Portrait orientation, 16:9 or 9:16 aspect"),
                    ("Control", "Cloud CMS for multi-store scheduling"),
                ]),
                ("HOTEL LOBBY FEATURE WALL", [
                    ("Type", "COB or MiP (premium visual quality)"),
                    ("Pixel Pitch", "P1.2 - P2.5 (depending on lobby size)"),
                    ("Brightness", "800 - 1,500 nits (controlled lighting)"),
                    ("Aspect", "Custom - match architectural design"),
                    ("Refresh Rate", "3,840 Hz minimum (guest photos/videos)"),
                    ("Service", "Front-service if flush-mounted"),
                    ("Integration", "HDMI + IP streaming for content flexibility"),
                    ("Special", "HDR support for cinematic content"),
                ]),
                ("IN-STORE DIGITAL SIGNAGE", [
                    ("Type", "SMD or MiP indoor panels"),
                    ("Pixel Pitch", "P2.5 - P4 (viewing distance 3-10m)"),
                    ("Brightness", "1,000 - 1,500 nits (bright retail lighting)"),
                    ("Size", "Standard 16:9 sections or custom"),
                    ("Mounting", "Wall, ceiling-hung, or free-standing totem"),
                    ("Content", "Scheduled promotional content via CMS"),
                    ("Network", "Ethernet + WiFi backup for content delivery"),
                ]),
                ("RESTAURANT / BAR", [
                    ("Type", "Flexible LED or standard indoor panel"),
                    ("Pixel Pitch", "P2.5 - P4 (ambient, not close-viewing)"),
                    ("Brightness", "600 - 1,000 nits (dim ambient lighting)"),
                    ("IP Rating", "IP43+ if near kitchen/bar (grease/steam)"),
                    ("Content", "Menu boards, ambience video, live sports"),
                    ("Audio", "Integrate with venue AV system"),
                ]),
            ],
        },
        "outdoor-dooh": {
            "title": "Outdoor &amp; DOOH",
            "subtitle": "Digital Out-of-Home LED Billboard Specification for UAE",
            "sections": [
                ("HIGHWAY BILLBOARD", [
                    ("Type", "SMD outdoor cabinet"),
                    ("Pixel Pitch", "P6 - P10 (viewing 20-80m)"),
                    ("Brightness", "7,000 - 10,000 nits (direct UAE sun)"),
                    ("IP Rating", "IP65 front, IP54 rear minimum"),
                    ("Operating Temp", "-10C to +60C (Dubai summer critical)"),
                    ("Structure", "Steel frame, wind-rated for local codes"),
                    ("Power", "Dual redundant PSU, auto-brightness sensor"),
                    ("Compliance", "Dubai Municipality / RTA approval required"),
                ]),
                ("BUILDING FACADE", [
                    ("Type", "Transparent LED or mesh LED"),
                    ("Pixel Pitch", "P15 - P40 (long distance viewing)"),
                    ("Brightness", "5,000 - 8,000 nits"),
                    ("Weight", "< 15 kg/sqm (structural constraint)"),
                    ("Wind Load", "Rated for local wind speeds"),
                    ("Transparency", "50-80% to preserve building aesthetics"),
                    ("Maintenance", "Rope-access or BMU compatible"),
                ]),
                ("STREET-LEVEL DIGITAL SIGN", [
                    ("Type", "Outdoor SMD cabinet"),
                    ("Pixel Pitch", "P3.9 - P6 (close + medium viewing)"),
                    ("Brightness", "5,500 - 7,000 nits"),
                    ("IP Rating", "IP65 all-round"),
                    ("Service", "Front-service mandatory (wall-mounted)"),
                    ("Vandal", "Tempered glass or polycarbonate cover"),
                    ("Cooling", "Forced air, filtered intake"),
                ]),
            ],
        },
        "corporate-control": {
            "title": "Corporate &amp; Control Room",
            "subtitle": "Fine-Pitch LED Wall Specification for Command Centres &amp; Boardrooms",
            "sections": [
                ("COMMAND / CONTROL ROOM (24/7)", [
                    ("Type", "COB (best contrast + lifespan for 24/7)"),
                    ("Pixel Pitch", "P0.7 - P1.2 (close viewing, data-dense)"),
                    ("Brightness", "400 - 600 nits (dark room, prevent eye strain)"),
                    ("Contrast", "15,000:1+ ANSI (critical for data readability)"),
                    ("Refresh Rate", "3,840 Hz+ (operators photograph screens)"),
                    ("Redundancy", "Dual PSU, dual data, hot-swap modules"),
                    ("Operation", "24/7 rated, 100,000+ hour lifespan"),
                    ("Calibration", "Factory + on-site, annual re-calibration"),
                    ("Processing", "Novastar or Brompton with windowing"),
                ]),
                ("EXECUTIVE BOARDROOM", [
                    ("Type", "COB or MiP (premium quality)"),
                    ("Pixel Pitch", "P0.9 - P1.5"),
                    ("Brightness", "600 - 800 nits (mixed lighting)"),
                    ("Size", "Typically 3-6m wide, 16:9 aspect"),
                    ("Input", "HDMI 2.0, USB-C, wireless casting"),
                    ("Audio", "Integrate with room DSP"),
                    ("Service", "Front-service (typically wall-mounted)"),
                ]),
            ],
        },
        "healthcare-wayfinding": {
            "title": "Healthcare",
            "subtitle": "Digital Signage Specification for Hospitals &amp; Clinics",
            "sections": [
                ("WAYFINDING DISPLAY", [
                    ("Type", "Indoor SMD or MiP panel"),
                    ("Pixel Pitch", "P2.5 - P4 (corridor viewing 2-8m)"),
                    ("Brightness", "800 - 1,200 nits (bright hospital lighting)"),
                    ("Mounting", "Wall-recessed or totem (ADA compliant)"),
                    ("Content", "Interactive wayfinding + static maps"),
                    ("Hygiene", "Smooth surface, easy to clean"),
                    ("EMC", "Medical-grade EMC compliance required"),
                ]),
                ("PATIENT INFORMATION DISPLAY", [
                    ("Type", "Indoor panel (SMD sufficient)"),
                    ("Pixel Pitch", "P2.5 (waiting areas, 3-6m viewing)"),
                    ("Brightness", "600 - 1,000 nits"),
                    ("Content", "Queue numbers, doctor info, health tips"),
                    ("Integration", "Hospital management system API"),
                    ("Privacy", "HIPAA/data privacy considerations"),
                ]),
            ],
        },
        "education-campus": {
            "title": "Education",
            "subtitle": "LED Display Specification for Schools, Universities &amp; Campuses",
            "sections": [
                ("AUDITORIUM / LECTURE HALL", [
                    ("Type", "SMD or MiP indoor panels"),
                    ("Pixel Pitch", "P2.5 - P3.9 (viewing 5-20m)"),
                    ("Brightness", "800 - 1,200 nits (mixed room lighting)"),
                    ("Size", "Minimum 4m wide for large halls"),
                    ("Input", "HDMI, USB-C, wireless casting for lecturers"),
                    ("Audio", "Integrate with hall PA system"),
                    ("Content", "Presentations, video playback, live streams"),
                ]),
                ("CAMPUS DIGITAL SIGNAGE NETWORK", [
                    ("Type", "Indoor SMD panels (cost-effective)"),
                    ("Pixel Pitch", "P2.5 - P4 (corridor/common area)"),
                    ("Brightness", "1,000 - 1,500 nits"),
                    ("Network", "Cloud CMS for centralized content management"),
                    ("Content", "Announcements, schedules, emergency alerts"),
                    ("Quantity", "Multiple screens managed from one platform"),
                    ("Emergency", "Override capability for emergency broadcasts"),
                ]),
            ],
        },
        "supermarket-promotions": {
            "title": "Supermarket Digital Signage",
            "subtitle": "LED Display Specification for Grocery &amp; Supermarket Promotions",
            "sections": [
                ("ENTRANCE FEATURE DISPLAY", [
                    ("Type", "SMD or MiP indoor panel"),
                    ("Pixel Pitch", "P2.5 - P4 (viewing 3-10m)"),
                    ("Brightness", "1,000 - 1,500 nits (bright retail lighting)"),
                    ("Size", "2m x 1.5m typical for store entrance"),
                    ("Content", "Welcome messages, daily deals, promotions"),
                    ("Orientation", "Landscape 16:9"),
                    ("Mounting", "Wall or ceiling suspended"),
                ]),
                ("AISLE END CAPS", [
                    ("Type", "Slim indoor LED panel"),
                    ("Pixel Pitch", "P2.5 - P3.9 (close viewing)"),
                    ("Brightness", "800 - 1,200 nits"),
                    ("Size", "Portrait 0.5m x 1m typical"),
                    ("Content", "Category promotions, product highlights"),
                    ("Integration", "POS system for dynamic pricing"),
                    ("Durability", "IP20 minimum for indoor retail"),
                ]),
                ("CHECKOUT ZONE DISPLAYS", [
                    ("Type", "Indoor SMD panels"),
                    ("Pixel Pitch", "P2.5 - P4"),
                    ("Brightness", "1,000 - 1,500 nits"),
                    ("Content", "Last-minute deals, loyalty programs, queue entertainment"),
                    ("Mounting", "Above checkout lanes, visible from queue"),
                    ("CMS", "Dayparting for time-based content"),
                ]),
                ("DELI / FRESH SECTION", [
                    ("Type", "Indoor panel with IP43+ protection"),
                    ("Pixel Pitch", "P2.5 - P4"),
                    ("Brightness", "800 - 1,200 nits"),
                    ("IP Rating", "IP43 minimum (food service area)"),
                    ("Content", "Menu boards, pricing, freshness messaging"),
                    ("Special", "Easy-clean surface for hygiene compliance"),
                ]),
            ],
        },
        "residential-cinema": {
            "title": "Residential Cinema Wall",
            "subtitle": "Home Theatre LED Wall Specification for Luxury Residences",
            "sections": [
                ("DEDICATED HOME CINEMA ROOM", [
                    ("Type", "COB (best-in-class contrast for cinema)"),
                    ("Pixel Pitch", "P0.9 - P1.5 (close viewing 2-4m)"),
                    ("Brightness", "300 - 600 nits (dark room, HDR content)"),
                    ("Contrast", "15,000:1+ ANSI (cinema-grade black levels)"),
                    ("Aspect", "2.35:1 CinemaScope or 16:9"),
                    ("Size", "3-6m diagonal typical for villa cinema"),
                    ("HDR", "HDR10, Dolby Vision support essential"),
                    ("Processing", "Premium processor (Novastar A10s or equivalent)"),
                ]),
                ("LIVING ROOM FEATURE WALL", [
                    ("Type", "MiP or COB (lifestyle aesthetics)"),
                    ("Pixel Pitch", "P1.2 - P2.5"),
                    ("Brightness", "600 - 1,000 nits (mixed lighting)"),
                    ("Size", "2-4m wide typical"),
                    ("Content", "TV, streaming, art display mode"),
                    ("Integration", "Smart home automation (Control4, Crestron)"),
                    ("Ambient", "Auto-brightness for day/night modes"),
                ]),
                ("OUTDOOR ENTERTAINMENT AREA", [
                    ("Type", "Outdoor-rated SMD or MiP"),
                    ("Pixel Pitch", "P2.5 - P4"),
                    ("Brightness", "3,000 - 5,000 nits (evening/night use)"),
                    ("IP Rating", "IP65 minimum (pool, garden exposure)"),
                    ("Content", "Sports, movies, ambient video"),
                    ("Weather", "Rated for UAE climate (-10C to +55C)"),
                    ("Audio", "Integrate with outdoor speaker system"),
                ]),
                ("INSTALLATION CONSIDERATIONS", [
                    ("Power", "Dedicated circuit, whole-house UPS recommended"),
                    ("Cooling", "Silent operation essential (< 30dB)"),
                    ("Control", "Integration with home automation"),
                    ("Calibration", "ISF/THX calibration for cinema grade"),
                    ("Service", "Front-service essential (flush wall mount)"),
                    ("Support", "Local service contract for residential"),
                ]),
            ],
        },
    }

    cfg = configs.get(pack_id)
    if not cfg:
        return

    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("BRIGHTLUXX", styles['BLX_Subtitle']))
    story.append(Paragraph(cfg['title'], styles['BLX_Title']))
    story.append(Paragraph(cfg['subtitle'], styles['BLX_Subtitle']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Application-specific LED display specifications for architects, AV consultants, and project managers in the UAE and GCC.", styles['BLX_Body']))
    story.append(PageBreak())

    for i, (section_title, specs) in enumerate(cfg['sections'], 1):
        story.append(Paragraph(f"{i}. {section_title}", styles['BLX_H1']))
        story.append(_make_table(
            ['Parameter', 'Specification'],
            [[s[0], s[1]] for s in specs],
            [40*mm, 110*mm],
        ))
        story.append(Spacer(1, 6*mm))

    story.append(PageBreak())
    story.append(Paragraph("VENDOR CHECKLIST", styles['BLX_H1']))
    story.append(Paragraph("Before signing off on any LED display specification, confirm:", styles['BLX_Body']))
    checklist = [
        "Technology type matches application requirements",
        "Pixel pitch appropriate for actual viewing distance",
        "Brightness specified at operating temperature (not lab 25C)",
        "IP rating covers actual installation environment",
        "Front or rear service matches physical access constraints",
        "Redundancy level appropriate for criticality",
        "Control system and content management platform confirmed",
        "Structural and electrical requirements documented",
        "Warranty terms and SLA clearly defined",
        "Spare parts provision agreed",
        "Installation and commissioning scope defined",
        "Training for operators included",
    ]
    for i, item in enumerate(checklist, 1):
        story.append(Paragraph(f"<bullet>{i:02d}.</bullet> {item}", styles['BLX_Bullet']))

    story.append(Spacer(1, 10*mm))
    story.append(_gold_hr())
    story.append(Paragraph("BRIGHTLUXX  |  Premium LED Display Solutions", styles['BLX_H3']))
    story.append(Paragraph("Jebel Ali Industrial Area 1, Dubai, UAE  |  +971 4 258 5754  |  info@brightluxx.com  |  brightluxx.com", styles['BLX_Body']))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_draw_bg)


def generate_spec_pack(pack_id, path):
    """Main entry point - generates the requested spec pack PDF."""
    generators = {
        "cob-mip-smd": _generate_cob_mip_smd,
        "pixel-pitch": _generate_pixel_pitch,
        "brightness-nits": _generate_brightness_nits,
        "ip-rating": _generate_ip_rating,
        "refresh-rate": _generate_refresh_rate,
        "retail-hospitality": _generate_application_pack,
        "outdoor-dooh": _generate_application_pack,
        "corporate-control": _generate_application_pack,
        "healthcare-wayfinding": _generate_application_pack,
        "education-campus": _generate_application_pack,
        "supermarket-promotions": _generate_application_pack,
        "residential-cinema": _generate_application_pack,
    }
    gen = generators.get(pack_id)
    if gen:
        if gen == _generate_application_pack:
            gen(pack_id, path)
        else:
            gen(path)
