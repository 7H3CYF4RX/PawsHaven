import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os

SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'alvirusff@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'ekav romt pnqe wpgu')
RESEND_API_KEY = "re_NS8zN3BN_Czm31qSadiuZ12588sZyqVyk"

# Global flag to track if Resend reached its quota
resend_exhausted = False

def send_via_gmail(to_email, subject, body_html):
    print(f"[MAIL_FALLBACK] Attempting to send via Gmail...")
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[MAIL_ERROR] Cannot fallback to Gmail, credentials missing.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[MAIL_SUCCESS] Successfully sent email to {to_email} via Gmail")
        return True
        
    except Exception as e:
        print(f"[MAIL_ERROR] Gmail fallback failed: {str(e)}")
        return False

def increment_email_count(sandbox_id):
    if not sandbox_id: return
    try:
        from utils import database as db
        db.execute(sandbox_id, "UPDATE users SET sent_emails = sent_emails + 1 WHERE id = 1")
    except: pass

def send_real_email(to_email, subject, body_html, sandbox_id=None):
    """
    Sends email via Resend API first. If it fails due to quota limits, 
    it falls back to Gmail SMTP.
    If sandbox_id is provided, increments the email count for the main user.
    """
    global resend_exhausted

    if resend_exhausted:
        print("[MAIL_INFO] Resend is exhausted. Defaulting directly to Gmail...")
        success = send_via_gmail(to_email, subject, body_html)
        if success: increment_email_count(sandbox_id)
        return success

    try:
        headers = {
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            # Since the domain cylabsec.store is verified, we use it here to escape the sandbox!
            "from": "PawsHaven <noreply@cylabsec.store>",
            "to": [to_email],
            "subject": subject,
            "html": body_html
        }
        resp = requests.post("https://api.resend.com/emails", headers=headers, json=data)
        
        if resp.status_code in [200, 201]:
            print(f"[MAIL_SUCCESS] Sent email via Resend to {to_email}")
            increment_email_count(sandbox_id)
            return True
        elif resp.status_code == 429 or "quota" in resp.text.lower() or "limit" in resp.text.lower():
            print(f"[MAIL_LIMIT] Resend hit sending limit! Marking as exhausted.")
            resend_exhausted = True
            success = send_via_gmail(to_email, subject, body_html)
            if success: increment_email_count(sandbox_id)
            return success
        else:
            print(f"[MAIL_ERROR] Resend API failed: {resp.status_code} {resp.text}")
            print("[MAIL_FALLBACK] Falling back to Gmail...")
            success = send_via_gmail(to_email, subject, body_html)
            if success: increment_email_count(sandbox_id)
            return success
            
    except Exception as e:
        print(f"[MAIL_ERROR] Unknown error with Resend: {str(e)}")
        print("[MAIL_FALLBACK] Falling back to Gmail...")
        success = send_via_gmail(to_email, subject, body_html)
        if success: increment_email_count(sandbox_id)
        return success
