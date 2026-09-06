import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils.translations import get_translation

# ── Config ────────────────────────────────────────────────────
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'shr.par.hs25@dypatil.edu')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'ozhc gymw mvzu nsly')
MAIL_SERVER   = 'smtp.gmail.com'
MAIL_PORT     = 587
PLATFORM_NAME = 'LokBandhu'
SUPPORT_EMAIL = MAIL_USERNAME


# ── Base HTML Email Template ──────────────────────────────────
def _base_template(title: str, body_html: str, lang: str = 'en') -> str:
    t = get_translation(lang)
    year = datetime.now().year
    return f"""
<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&display=swap');
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#f0f4f8; font-family:'Noto Sans',Arial,sans-serif; padding:30px 15px; }}
    .wrapper {{ max-width:600px; margin:0 auto; }}
    .header {{ background:#000080; border-radius:12px 12px 0 0; padding:0; overflow:hidden; }}
    .tricolor {{ display:flex; height:5px; }}
    .t-saffron {{ background:#FF9933; flex:1; }}
    .t-white   {{ background:#ffffff; flex:1; }}
    .t-green   {{ background:#138808; flex:1; }}
    .header-body {{ padding:28px 32px; }}
    .logo {{ font-size:26px; font-weight:700; color:#fff; letter-spacing:0.5px; }}
    .logo-sub {{ font-size:12px; color:rgba(255,255,255,0.6); margin-top:2px; }}
    .card {{ background:#ffffff; padding:36px 32px; border-left:1px solid #e2e8f0; border-right:1px solid #e2e8f0; }}
    .title {{ font-size:22px; font-weight:700; color:#1e293b; margin-bottom:16px; }}
    .body-text {{ font-size:15px; color:#475569; line-height:1.7; }}
    .info-box {{ background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid #000080; border-radius:8px; padding:18px 20px; margin:20px 0; }}
    .info-row {{ display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f1f5f9; font-size:14px; }}
    .info-row:last-child {{ border-bottom:none; }}
    .info-label {{ color:#64748b; font-weight:600; }}
    .info-value {{ color:#1e293b; font-weight:600; text-align:right; }}
    .status-badge {{ display:inline-block; padding:5px 14px; border-radius:20px; font-size:13px; font-weight:700; }}
    .status-submitted {{ background:#fef3c7; color:#92400e; }}
    .status-progress  {{ background:#dbeafe; color:#1e40af; }}
    .status-resolved  {{ background:#dcfce7; color:#166534; }}
    .status-closed    {{ background:#f1f5f9; color:#475569; }}
    .btn {{ display:inline-block; background:#FF9933; color:#fff; padding:13px 28px; border-radius:8px; text-decoration:none; font-weight:700; font-size:15px; margin:20px 0; }}
    .alert-box {{ background:#fef2f2; border:1px solid #fecaca; border-left:4px solid #ef4444; border-radius:8px; padding:16px 20px; margin:20px 0; }}
    .success-box {{ background:#f0fdf4; border:1px solid #bbf7d0; border-left:4px solid #138808; border-radius:8px; padding:16px 20px; margin:20px 0; }}
    .footer {{ background:#f8fafc; border:1px solid #e2e8f0; border-top:none; border-radius:0 0 12px 12px; padding:20px 32px; text-align:center; }}
    .footer p {{ font-size:12px; color:#94a3b8; line-height:1.6; }}
    .footer a {{ color:#000080; text-decoration:none; }}
    .divider {{ border:none; border-top:1px solid #f1f5f9; margin:20px 0; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="tricolor">
        <div class="t-saffron"></div>
        <div class="t-white"></div>
        <div class="t-green"></div>
      </div>
      <div class="header-body">
        <div class="logo">🇮🇳 {PLATFORM_NAME}</div>
        <div class="logo-sub">{t.get('email_tagline', 'A Citizen Services Initiative')}</div>
      </div>
    </div>
    <div class="card">
      {body_html}
    </div>
    <div class="footer">
      <p>{t.get('email_footer_1', 'This is an automated email from LokBandhu. Please do not reply.')}<br>
      {t.get('email_footer_2', 'For support, contact')} <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
      <p style="margin-top:8px;">© {year} {PLATFORM_NAME}. {t.get('email_rights', 'All rights reserved.')}</p>
    </div>
  </div>
</body>
</html>"""


# ── Core send function ────────────────────────────────────────
def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via Gmail SMTP. Returns True on success."""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("⚠️  Email not configured. Set MAIL_USERNAME and MAIL_PASSWORD env vars.")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f"{PLATFORM_NAME} <{MAIL_USERNAME}>"
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        print(f"✅ Email sent to {to_email}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail auth failed. Check MAIL_USERNAME and MAIL_PASSWORD (use App Password).")
        return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


# ════════════════════════════════════════════════════════════
#  PUBLIC EMAIL FUNCTIONS — call these from your routes
# ════════════════════════════════════════════════════════════

def send_welcome_email(user_email: str, user_name: str, lang: str = 'en') -> bool:
    """Sent after successful registration."""
    t = get_translation(lang)
    subject = f"🎉 {t.get('email_welcome_subject', 'Welcome to LokBandhu!')}"
    body = f"""
      <h2 class="title">{t.get('email_welcome_title', 'Welcome to LokBandhu!')} 🙏</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_welcome_body', 'Your citizen account has been successfully created on LokBandhu — your digital gateway to government services.')}</p>
      <div class="success-box">
        <p style="font-size:14px; color:#166534; font-weight:600;">✅ {t.get('email_account_created', 'Account Successfully Created')}</p>
        <p style="font-size:13px; color:#15803d; margin-top:4px;">{t.get('email_registered_as', 'Registered as')}: <strong>{user_email}</strong></p>
      </div>
      <p class="body-text">{t.get('email_welcome_can_now', 'You can now:')}</p>
      <ul style="margin:12px 0 12px 20px; color:#475569; font-size:14px; line-height:2;">
        <li>{t.get('email_w1', '📋 Submit civic complaints and grievances')}</li>
        <li>{t.get('email_w2', '🔍 Track your complaint status in real-time')}</li>
        <li>{t.get('email_w3', '📚 Browse government services (Rural/Urban/Metro)')}</li>
      </ul>
      <a href="http://127.0.0.1:5000/citizen/dashboard" class="btn">{t.get('email_go_dashboard', 'Go to Dashboard →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_login_email(user_email: str, user_name: str, lang: str = 'en') -> bool:
    """Sent after every successful login."""
    t = get_translation(lang)
    now = datetime.now().strftime('%d %b %Y, %I:%M %p')
    subject = f"🔐 {t.get('email_login_subject', 'New Login to Your LokBandhu Account')}"
    body = f"""
      <h2 class="title">{t.get('email_login_title', 'Login Successful')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_login_body', 'A successful login was detected on your LokBandhu account.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_account', 'Account')}</span>
          <span class="info-value">{user_email}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_time', 'Time')}</span>
          <span class="info-value">{now}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_status', 'Status')}</span>
          <span class="info-value" style="color:#138808;">✅ {t.get('email_success', 'Successful')}</span>
        </div>
      </div>
      <p class="body-text" style="font-size:13px; color:#ef4444;">{t.get('email_login_not_you', 'If this was not you, please contact support immediately.')}</p>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_logout_email(user_email: str, user_name: str, lang: str = 'en') -> bool:
    """Sent after logout."""
    t = get_translation(lang)
    now = datetime.now().strftime('%d %b %Y, %I:%M %p')
    subject = f"👋 {t.get('email_logout_subject', 'You have been logged out of LokBandhu')}"
    body = f"""
      <h2 class="title">{t.get('email_logout_title', 'Logged Out Successfully')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_logout_body', 'You have been successfully logged out of your LokBandhu account.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_logout_time', 'Logout Time')}</span>
          <span class="info-value">{now}</span>
        </div>
      </div>
      <a href="http://127.0.0.1:5000/auth/login" class="btn">{t.get('email_login_again', 'Login Again →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_complaint_submitted_email(user_email: str, user_name: str,
                                    complaint_id: int, category: str,
                                    description: str, lang: str = 'en') -> bool:
    """Sent when a citizen submits a new complaint."""
    t = get_translation(lang)
    subject = f"📋 {t.get('email_complaint_subject', 'Complaint Submitted')} — ID #{complaint_id}"
    snippet = description[:120] + '...' if len(description) > 120 else description
    body = f"""
      <h2 class="title">{t.get('email_complaint_title', 'Complaint Submitted Successfully')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_complaint_body', 'Your complaint has been received and registered. Our team will review it shortly.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_complaint_id', 'Complaint ID')}</span>
          <span class="info-value" style="color:#000080; font-size:16px;">#{complaint_id}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_category', 'Category')}</span>
          <span class="info-value">{category}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_current_status', 'Current Status')}</span>
          <span class="info-value"><span class="status-badge status-submitted">📥 {t.get('status_submitted', 'Submitted')}</span></span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_description', 'Description')}</span>
          <span class="info-value" style="max-width:280px;">{snippet}</span>
        </div>
      </div>
      <p class="body-text">{t.get('email_complaint_track', 'Save your Complaint ID')} <strong>#{complaint_id}</strong> {t.get('email_complaint_track2', 'to track progress anytime.')}</p>
      <a href="http://127.0.0.1:5000/citizen/track_complaints" class="btn">{t.get('email_track_complaint', 'Track My Complaint →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_complaint_status_update_email(user_email: str, user_name: str,
                                        complaint_id: int, category: str,
                                        old_status: str, new_status: str,
                                        lang: str = 'en') -> bool:
    """Sent when admin updates a complaint's status."""
    t = get_translation(lang)
    subject = f"🔄 {t.get('email_status_subject', 'Complaint Status Updated')} — ID #{complaint_id}"

    status_class_map = {
        'Submitted':   'status-submitted',
        'In Progress': 'status-progress',
        'Resolved':    'status-resolved',
        'Closed':      'status-closed',
    }
    status_emoji_map = {
        'Submitted':   '📥',
        'In Progress': '⚙️',
        'Resolved':    '✅',
        'Closed':      '🔒',
    }
    new_cls   = status_class_map.get(new_status, 'status-submitted')
    new_emoji = status_emoji_map.get(new_status, '📋')

    congrats = ""
    if new_status == 'Resolved':
        congrats = f'<div class="success-box"><p style="font-size:15px;color:#166534;font-weight:700;">🎉 {t.get("email_resolved_msg", "Great news! Your issue has been resolved.")}</p></div>'

    body = f"""
      <h2 class="title">{t.get('email_status_title', 'Complaint Status Updated')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_status_body', 'There has been an update to your complaint.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_complaint_id', 'Complaint ID')}</span>
          <span class="info-value" style="color:#000080;">#{complaint_id}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_category', 'Category')}</span>
          <span class="info-value">{category}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_old_status', 'Previous Status')}</span>
          <span class="info-value"><span class="status-badge {status_class_map.get(old_status,'status-submitted')}">{old_status}</span></span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_new_status', 'New Status')}</span>
          <span class="info-value"><span class="status-badge {new_cls}">{new_emoji} {new_status}</span></span>
        </div>
      </div>
      {congrats}
      <a href="http://127.0.0.1:5000/citizen/track_complaints" class="btn">{t.get('email_track_complaint', 'Track My Complaint →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_role_changed_email(user_email: str, user_name: str,
                             old_role: str, new_role: str,
                             lang: str = 'en') -> bool:
    """Sent when admin changes a user's role."""
    t = get_translation(lang)
    subject = f"👤 {t.get('email_role_subject', 'Your LokBandhu Role Has Been Updated')}"
    body = f"""
      <h2 class="title">{t.get('email_role_title', 'Account Role Updated')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_role_body', 'Your account role on LokBandhu has been updated by an administrator.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_old_role', 'Previous Role')}</span>
          <span class="info-value">{old_role}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_new_role', 'New Role')}</span>
          <span class="info-value" style="color:#000080; font-weight:700;">{new_role}</span>
        </div>
      </div>
      <p class="body-text">{t.get('email_role_action', 'Please log out and log back in for the changes to take full effect.')}</p>
      <a href="http://127.0.0.1:5000/auth/login" class="btn">{t.get('email_login_again', 'Login Again →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_service_notification_email(user_email: str, user_name: str,
                                     action: str, service_name: str,
                                     lang: str = 'en') -> bool:
    """Sent to admin when a service is added, edited, or deleted."""
    t = get_translation(lang)
    action_map = {
        'added':   ('✅', t.get('email_service_added',   'New Service Added'),   '#138808'),
        'edited':  ('✏️', t.get('email_service_edited',  'Service Updated'),     '#000080'),
        'deleted': ('🗑️', t.get('email_service_deleted', 'Service Deleted'),     '#ef4444'),
    }
    emoji, action_label, color = action_map.get(action, ('📋', action, '#000080'))
    subject = f"{emoji} {t.get('email_service_subject', 'Service Directory Update')} — {action_label}"
    body = f"""
      <h2 class="title">{t.get('email_service_title', 'Service Directory Updated')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_service_body', 'An action was performed on the LokBandhu Service Directory.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_action', 'Action')}</span>
          <span class="info-value" style="color:{color}; font-weight:700;">{emoji} {action_label}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_service_name', 'Service Name')}</span>
          <span class="info-value">{service_name}</span>
        </div>
      </div>
      <a href="http://127.0.0.1:5000/admin/manage_services" class="btn">{t.get('email_view_services', 'View Service Directory →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))

def send_registration_success_email(user_email: str, user_name: str, lang: str = 'en') -> bool:
    """Triggered immediately after a new user record is created."""
    t = get_translation(lang)
    subject = f"✨ {t.get('email_reg_subject', 'Account Created Successfully')}"
    
    body = f"""
      <h2 class="title">{t.get('email_welcome_title', 'Welcome to the Fold!')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_reg_body', 'Your account with LokBandhu has been created. You can now access citizen services, track grievances, and stay updated.')}</p>
      <div class="success-box">
        <p style="font-size:14px; color:#138808; font-weight:600;">✅ {t.get('email_ready', 'Your profile is active.')}</p>
      </div>
      <a href="http://127.0.0.1:5000/auth/login" class="btn">{t.get('email_login_now', 'Login to Get Started →')}</a>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_login_alert_email(user_email: str, user_name: str, lang: str = 'en') -> bool:
    """Triggered after a successful password verification."""
    t = get_translation(lang)
    now = datetime.now().strftime('%d %b %Y, %I:%M %p')
    subject = f"🔒 {t.get('email_login_alert_subject', 'Security Alert: New Login')}"
    
    body = f"""
      <h2 class="title">{t.get('email_login_title', 'New Login Detected')}</h2>
      <p class="body-text">{t.get('email_dear', 'Dear')} <strong>{user_name}</strong>,</p>
      <br>
      <p class="body-text">{t.get('email_login_alert_body', 'We noticed a new login to your LokBandhu account.')}</p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">{t.get('email_time', 'Time')}</span>
          <span class="info-value">{now}</span>
        </div>
        <div class="info-row">
          <span class="info-label">{t.get('email_status', 'Status')}</span>
          <span class="info-value" style="color:#138808;">{t.get('email_authorized', 'Authorized')}</span>
        </div>
      </div>
      <p class="body-text" style="font-size:13px; color:#64748b;">
        {t.get('email_security_footer', 'If this was you, you can safely ignore this email.')}
      </p>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))


def send_failed_login_email(user_email: str, lang: str = 'en') -> bool:
    """Sent when a failed login attempt is detected for an existing email."""
    t = get_translation(lang)
    now = datetime.now().strftime('%d %b %Y, %I:%M %p')
    subject = f"⚠️ {t.get('email_failed_login_subject', 'Failed Login Attempt on Your LokBandhu Account')}"
    body = f"""
      <h2 class="title" style="color:#ef4444;">{t.get('email_failed_login_title', 'Failed Login Attempt Detected')}</h2>
      <p class="body-text">{t.get('email_failed_login_body', 'A failed login attempt was detected on your LokBandhu account.')}</p>
      <div class="alert-box">
        <p style="font-size:14px; color:#b91c1c; font-weight:600;">⚠️ {t.get('email_failed_login_warn', 'If this was not you, your account may be at risk.')}</p>
        <p style="font-size:13px; color:#dc2626; margin-top:6px;">{t.get('email_time', 'Time')}: {now}</p>
      </div>
      <p class="body-text">{t.get('email_failed_login_action', 'If this was not you, please contact support immediately at')} <a href="mailto:{SUPPORT_EMAIL}" style="color:#000080;">{SUPPORT_EMAIL}</a>.</p>
    """
    return _send_email(user_email, subject, _base_template(subject, body, lang))
