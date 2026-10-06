"""Gmail SMTP email service for lead notifications."""
import os
import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("email_service")

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL")


def _send_email_sync(to_email: str, subject: str, html_body: str):
    """Synchronous email send via Gmail SMTP."""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        logger.warning("SMTP not configured, skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Brightluxx Website <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False


async def send_email(to_email: str, subject: str, html_body: str):
    """Non-blocking async email send."""
    return await asyncio.to_thread(_send_email_sync, to_email, subject, html_body)


async def notify_new_lead(lead_data: dict):
    """Send notification email for a new lead to the sales team using enhanced templates."""
    if not NOTIFICATION_EMAIL:
        return

    from email_templates import contact_form_email
    
    source = lead_data.get("source", "website")
    
    # Use enhanced template for contact form
    if source in ["contact_form", "website"]:
        subject, html = contact_form_email(lead_data)
        await send_email(NOTIFICATION_EMAIL, subject, html)
        return
    
    # Fallback for other sources - use basic template
    name = lead_data.get("name", "Unknown")
    email = lead_data.get("email", "Not provided")
    company = lead_data.get("company", "Not provided")
    role = lead_data.get("role", "Not specified")
    phone = lead_data.get("phone", "")
    message = lead_data.get("message", "")
    application = lead_data.get("application", "")
    spec_pack = lead_data.get("spec_pack_title", "")

    if source == "spec_pack_download":
        subject = f"Spec Pack Download: {spec_pack} — {name}"
        source_label = "Spec Pack Download"
    else:
        subject = f"New Lead: {name}"
        source_label = source.replace("_", " ").title()

    extra_rows = ""
    if company and company != "Not provided":
        extra_rows += f'<tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Company</td><td style="padding:8px 12px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{company}</td></tr>'
    if role and role != "Not specified":
        extra_rows += f'<tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Role</td><td style="padding:8px 12px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{role}</td></tr>'
    if phone:
        extra_rows += f'<tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Phone</td><td style="padding:8px 12px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{phone}</td></tr>'
    if application:
        extra_rows += f'<tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Application</td><td style="padding:8px 12px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{application}</td></tr>'
    if spec_pack:
        extra_rows += f'<tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Spec Pack</td><td style="padding:8px 12px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{spec_pack}</td></tr>'
    if message:
        extra_rows += f'<tr><td colspan="2" style="padding:12px;color:#ccc;font-size:13px;border-bottom:1px solid #222;"><strong style="color:#999;">Message:</strong><br>{message}</td></tr>'

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#0B0B0B;border:1px solid #333;border-radius:12px;overflow:hidden;">
      <div style="padding:20px 24px;background:linear-gradient(135deg,#1a1a1a,#111);border-bottom:1px solid #333;">
        <div style="font-size:22px;font-weight:900;color:#E5C574;letter-spacing:3px;margin-bottom:12px;">BRIGHTLUXX</div>
        <div style="font-size:11px;letter-spacing:2px;color:#E5C574;margin-bottom:4px;">{source_label.upper()}</div>
        <div style="font-size:18px;font-weight:bold;color:#fff;">{name}</div>
      </div>
      <div style="padding:4px 12px;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Name</td><td style="padding:8px 12px;color:#fff;font-size:13px;font-weight:bold;border-bottom:1px solid #222;">{name}</td></tr>
          <tr><td style="padding:8px 12px;color:#999;font-size:13px;border-bottom:1px solid #222;">Email</td><td style="padding:8px 12px;border-bottom:1px solid #222;"><a href="mailto:{email}" style="color:#E5C574;text-decoration:none;">{email}</a></td></tr>
          {extra_rows}
        </table>
      </div>
      <div style="padding:16px 24px;text-align:center;border-top:1px solid #222;">
        <div style="font-size:11px;color:#666;">Brightluxx Website — Automated Notification</div>
      </div>
    </div>
    """

    await send_email(NOTIFICATION_EMAIL, subject, html)
