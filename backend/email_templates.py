"""
Enhanced email templates with Brightluxx branding.
All emails use a consistent, professional design with the company logo.
"""

# Brightluxx logo as base64 SVG (gold text on transparent)
BRIGHTLUXX_LOGO = """
<svg width="180" height="36" viewBox="0 0 180 36" xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="26" font-family="Arial Black, Arial, sans-serif" font-size="24" font-weight="900" fill="#E5C574" letter-spacing="2">BRIGHTLUXX</text>
</svg>
"""

def get_email_header(title: str, subtitle: str = "", accent_color: str = "#E5C574") -> str:
    """Generate consistent email header with logo."""
    subtitle_html = f'<div style="font-size:13px;color:#999;margin-top:4px;">{subtitle}</div>' if subtitle else ''
    return f"""
    <div style="padding:24px 28px;background:linear-gradient(135deg,#141414 0%,#0B0B0B 100%);border-bottom:1px solid #2a2a2a;">
      <div style="margin-bottom:16px;">
        <span style="font-family:'Arial Black',Arial,sans-serif;font-size:22px;font-weight:900;color:#E5C574;letter-spacing:3px;">BRIGHTLUXX</span>
      </div>
      <div style="font-size:10px;letter-spacing:2px;color:{accent_color};text-transform:uppercase;margin-bottom:4px;">{title}</div>
      {subtitle_html}
    </div>
    """

def get_email_footer() -> str:
    """Generate consistent email footer."""
    return """
    <div style="padding:20px 28px;background:#0a0a0a;border-top:1px solid #222;text-align:center;">
      <div style="font-size:11px;color:#666;margin-bottom:8px;">
        This is an automated notification from the Brightluxx website.
      </div>
      <div style="font-size:10px;color:#555;">
        <a href="https://brightluxx.com" style="color:#E5C574;text-decoration:none;">brightluxx.com</a>
        &nbsp;|&nbsp;
        <a href="tel:+971559954274" style="color:#888;text-decoration:none;">+971 55 995 4274</a>
        &nbsp;|&nbsp;
        <a href="mailto:sales@brightluxx.com" style="color:#888;text-decoration:none;">sales@brightluxx.com</a>
      </div>
    </div>
    """

def get_info_row(label: str, value: str, is_email: bool = False, is_link: bool = False) -> str:
    """Generate a single info row."""
    if not value or value == "Not provided":
        return ""
    
    if is_email:
        value_html = f'<a href="mailto:{value}" style="color:#E5C574;text-decoration:none;font-weight:500;">{value}</a>'
    elif is_link:
        value_html = f'<a href="{value}" target="_blank" style="color:#E5C574;text-decoration:none;">{value}</a>'
    else:
        value_html = f'<span style="color:#fff;">{value}</span>'
    
    return f"""
    <tr>
      <td style="padding:10px 0;color:#888;font-size:13px;width:120px;vertical-align:top;border-bottom:1px solid #1a1a1a;">{label}</td>
      <td style="padding:10px 0;font-size:13px;border-bottom:1px solid #1a1a1a;">{value_html}</td>
    </tr>
    """

def get_message_row(message: str) -> str:
    """Generate a message/notes row spanning full width."""
    if not message:
        return ""
    return f"""
    <tr>
      <td colspan="2" style="padding:16px 0;border-bottom:1px solid #1a1a1a;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Message</div>
        <div style="color:#ccc;font-size:13px;line-height:1.6;background:#111;padding:12px 16px;border-radius:8px;border-left:3px solid #E5C574;">{message}</div>
      </td>
    </tr>
    """

def build_email(header_title: str, header_subtitle: str, rows: list, message: str = "", accent_color: str = "#E5C574") -> str:
    """Build complete email HTML."""
    rows_html = "".join(rows)
    message_html = get_message_row(message) if message else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:20px;background:#000;font-family:Arial,Helvetica,sans-serif;">
      <div style="max-width:560px;margin:0 auto;background:#0B0B0B;border:1px solid #333;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.5);">
        {get_email_header(header_title, header_subtitle, accent_color)}
        <div style="padding:20px 28px;">
          <table style="width:100%;border-collapse:collapse;">
            {rows_html}
            {message_html}
          </table>
        </div>
        {get_email_footer()}
      </div>
    </body>
    </html>
    """


# Pre-built templates for specific form types

def contact_form_email(data: dict) -> tuple:
    """Generate email for contact form submission."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    application = data.get("application", "General Inquiry")
    message = data.get("message", "")
    
    subject = f"New Enquiry: {name} — {application}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Application", application),
    ]
    
    html = build_email("New Lead Enquiry", name, rows, message)
    return subject, html


def signage_inquiry_email(data: dict) -> tuple:
    """Generate email for signage quote request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    signage_type = data.get("signage_type", "").replace("-", " ").title()
    quantity = data.get("quantity", "")
    letter_height = data.get("letter_height", "")
    illumination = data.get("illumination", "").replace("-", " ").title()
    material = data.get("material", "").replace("-", " ").title()
    location = data.get("location", "").title()
    timeline = data.get("timeline", "").replace("-", " ").title()
    budget = data.get("budget_range", "").replace("-", " ")
    brief = data.get("project_brief", "")
    
    subject = f"Signage Quote: {signage_type} — {name}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Signage Type", signage_type),
        get_info_row("Quantity", quantity),
        get_info_row("Letter Height", letter_height),
        get_info_row("Illumination", illumination),
        get_info_row("Material", material),
        get_info_row("Location", location),
        get_info_row("Timeline", timeline),
        get_info_row("Budget", budget),
    ]
    
    html = build_email("Signage Quote Request", f"{signage_type} — {company or name}", rows, brief, accent_color="#f59e0b")
    return subject, html


def site_visit_email(data: dict) -> tuple:
    """Generate email for site visit request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    project_type = data.get("project_type", "")
    preferred_date = data.get("preferred_date", "")
    location = data.get("location", "")
    notes = data.get("notes", "")
    
    subject = f"Site Visit Request: {company or name} — {location}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Project Type", project_type),
        get_info_row("Preferred Date", preferred_date),
        get_info_row("Location", location),
    ]
    
    html = build_email("Site Visit Request", f"{location} — {preferred_date}", rows, notes, accent_color="#10b981")
    return subject, html


def cpd_request_email(data: dict) -> tuple:
    """Generate email for CPD/Lunch & Learn booking."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    role = data.get("role", "")
    attendees = data.get("attendees", "")
    preferred_date = data.get("preferred_date", "")
    topic = data.get("preferred_topic", "")
    notes = data.get("notes", "")
    
    subject = f"CPD Session Booking: {company} — {attendees} attendees"
    
    rows = [
        get_info_row("Organizer", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Role", role),
        get_info_row("Attendees", str(attendees)),
        get_info_row("Preferred Date", preferred_date),
        get_info_row("Topic", topic),
    ]
    
    html = build_email("CPD Session Booking", f"{company} — {attendees} attendees", rows, notes, accent_color="#8b5cf6")
    return subject, html


def franchise_email(data: dict) -> tuple:
    """Generate email for franchise/distribution request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    country = data.get("country", "")
    city = data.get("city", "")
    business_type = data.get("business_type", "")
    experience = data.get("experience", "")
    message = data.get("message", "")
    
    subject = f"Franchise Request: {company} — {country}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Location", f"{city}, {country}"),
        get_info_row("Business Type", business_type),
        get_info_row("Experience", experience),
    ]
    
    html = build_email("Franchise / Distribution Request", f"{company} — {country}", rows, message, accent_color="#ec4899")
    return subject, html


def supplier_email(data: dict) -> tuple:
    """Generate email for supplier registration."""
    company = data.get("company_name", "Unknown")
    contact = data.get("contact_person", "")
    email = data.get("email", "")
    phone = data.get("phone", "")
    country = data.get("country", "")
    category = data.get("product_category", "")
    certs = data.get("certifications", "")
    website = data.get("website", "")
    message = data.get("message", "")
    
    subject = f"Supplier Registration: {company} — {category}"
    
    rows = [
        get_info_row("Company", company),
        get_info_row("Contact", contact),
        get_info_row("Email", email, is_email=True),
        get_info_row("Phone", phone),
        get_info_row("Country", country),
        get_info_row("Category", category),
        get_info_row("Certifications", certs),
        get_info_row("Website", website, is_link=True),
    ]
    
    html = build_email("Supplier Registration", f"{company} — {category}", rows, message, accent_color="#06b6d4")
    return subject, html


def support_email(data: dict) -> tuple:
    """Generate email for technical support request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    product = data.get("product", "")
    issue_type = data.get("issue_type", "")
    urgency = data.get("urgency", "normal")
    description = data.get("description", "")
    
    urgency_label = "URGENT" if urgency == "urgent" else "Normal Priority"
    accent = "#ef4444" if urgency == "urgent" else "#E5C574"
    
    subject = f"[{urgency_label}] Support: {issue_type} — {company}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Product", product),
        get_info_row("Issue Type", issue_type),
        get_info_row("Urgency", urgency_label),
    ]
    
    html = build_email(f"Technical Support — {urgency_label}", f"{issue_type} — {company}", rows, description, accent_color=accent)
    return subject, html


def quick_inquiry_email(data: dict) -> tuple:
    """Generate email for quick inquiry popup."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    phone = data.get("phone", "")
    product = data.get("product_interest", "")
    page = data.get("page_context", "")
    
    subject = f"Quick Inquiry: {name} — {product or 'General'}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Phone", phone),
        get_info_row("Product Interest", product),
        get_info_row("Page", page),
    ]
    
    html = build_email("Quick Inquiry", product or "General Interest", rows)
    return subject, html


def design_assist_email(data: dict) -> tuple:
    """Generate email for design assistance request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    project_type = data.get("project_type", "")
    requirements = data.get("requirements", "")
    deadline = data.get("deadline", "")
    
    subject = f"Design Assistance: {project_type} — {company or name}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Project Type", project_type),
        get_info_row("Deadline", deadline),
    ]
    
    html = build_email("Design Assistance Request", f"{project_type}", rows, requirements, accent_color="#f97316")
    return subject, html


def spec_substitution_email(data: dict) -> tuple:
    """Generate email for spec substitution request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    phone = data.get("phone", "")
    current_spec = data.get("current_spec", "")
    project_name = data.get("project_name", "")
    reason = data.get("reason", "")
    
    subject = f"Spec Substitution: {current_spec} — {project_name}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Phone", phone),
        get_info_row("Current Spec", current_spec),
        get_info_row("Project", project_name),
    ]
    
    html = build_email("Spec Substitution Request", f"Replace: {current_spec}", rows, reason, accent_color="#14b8a6")
    return subject, html


def chat_lead_email(data: dict) -> tuple:
    """Generate email for AURA chat lead capture."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    phone = data.get("phone", "")
    interest = data.get("interest", "")
    conversation = data.get("conversation_summary", "")
    
    subject = f"AURA Chat Lead: {name} — {interest or 'General'}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Phone", phone),
        get_info_row("Interest", interest),
    ]
    
    html = build_email("AURA Chat Lead Capture", f"Interest: {interest}", rows, conversation, accent_color="#a855f7")
    return subject, html


def download_request_email(data: dict) -> tuple:
    """Generate email for document download request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    role = data.get("role", "")
    doc_title = data.get("document_title", "")
    doc_type = data.get("document_type", "")
    
    subject = f"Download: {doc_title} — {name}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Role", role),
        get_info_row("Document", doc_title),
        get_info_row("Type", doc_type),
    ]
    
    html = build_email("Document Download", doc_title, rows, accent_color="#64748b")
    return subject, html



def specpack_download_email(data: dict) -> tuple:
    """Generate email for spec pack download request."""
    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    role = data.get("role", "")
    pack_title = data.get("spec_pack_title", "")
    
    subject = f"Spec Pack Download: {pack_title} — {name}"
    
    rows = [
        get_info_row("Name", name),
        get_info_row("Email", email, is_email=True),
        get_info_row("Company", company),
        get_info_row("Role", role),
        get_info_row("Spec Pack", pack_title),
    ]
    
    html = build_email("Spec Pack Download", pack_title, rows, accent_color="#3b82f6")
    return subject, html
