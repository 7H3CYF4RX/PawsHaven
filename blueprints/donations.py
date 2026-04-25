"""
Donations Blueprint
Vulnerabilities: Business logic coupon reuse (#14), Race condition (#30), Forced browsing (#7)
"""
import time
import os
from flask import Blueprint, request, jsonify, g, send_file
from middleware.auth_middleware import require_auth, optional_auth
from utils import database as db
from config import Config
from fpdf import FPDF

donations_bp = Blueprint('donations', __name__)

@donations_bp.route('/api/donations', methods=['GET'])
@require_auth
def get_donations_summary():
    """Returns a summary of the current user's donations for the dashboard."""
    rows = db.query_all(g.sandbox_id,
        "SELECT amount, final_amount, created_at FROM donations WHERE user_id = ? ORDER BY created_at DESC",
        [g.current_user['user_id']])
    total_amount = sum(r['final_amount'] for r in rows)
    return jsonify({
        'count': len(rows),
        'total': total_amount,
        'last_donation': rows[0]['created_at'] if rows else None
    })


@donations_bp.route('/api/donations', methods=['POST'])
@require_auth
def make_donation():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    card_number = data.get('card_number', '').replace(' ', '')
    expiry = data.get('expiry', '').strip()
    cvc = data.get('cvc', '').strip()

    if amount <= 0:
        return jsonify({'error': 'Donation amount must be greater than $0.'}), 400
    if amount > 50000:
        return jsonify({'error': 'Maximum donation amount is $50,000 per transaction.'}), 400

    # Payment validation
    if not card_number or len(card_number) < 16:
        return jsonify({'error': 'Invalid card number. Must be at least 16 digits.'}), 400
    if not expiry or not cvc:
        return jsonify({'error': 'Card expiry and CVC are required.'}), 400
    if len(cvc) < 3:
        return jsonify({'error': 'Invalid CVC. Must be 3 or 4 digits.'}), 400

    receipt_filename = f'receipt_new.pdf'
    donation_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO donations (user_id, amount, coupon_code, discount, final_amount, receipt_path) VALUES (?, ?, ?, ?, ?, ?)",
        [g.current_user['user_id'], amount, '', 0, amount, receipt_filename])
    
    receipt_filename = f'receipt_{(donation_id+3):03d}.pdf'
    db.execute(g.sandbox_id, "UPDATE donations SET receipt_path = ? WHERE id = ?", [receipt_filename, donation_id])

    # Build metadata
    txn_id = f"TXN-{donation_id+1000}"
    receipt_no = f"PH-{donation_id:05d}"
    issue_date = time.strftime("%B %d, %Y")
    issue_time = time.strftime("%I:%M %p")
    donor_name = g.current_user.get('name', 'Anonymous Donor')
    donor_email = g.current_user['email']
    donor_id = g.current_user.get('user_id', 'N/A')

    # ═══════════════════════════════════════════════
    # Premium Receipt PDF Generation
    # ═══════════════════════════════════════════════
    pdf = FPDF()
    pdf.add_page()
    pw = 190  # usable page width (210 - margins)
    lm = 10   # left margin

    # ── 1. HEADER BAR ──────────────────────────────
    pdf.set_fill_color(30, 81, 60)
    pdf.rect(0, 0, 210, 48, 'F')
    # Accent strip
    pdf.set_fill_color(52, 168, 83)
    pdf.rect(0, 48, 210, 3, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 26)
    pdf.set_y(10)
    pdf.cell(0, 12, 'PAWSHAVEN', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 9)
    pdf.cell(0, 5, 'Animal Rescue & Veterinary Pharmacy', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 10, 'DONATION RECEIPT', align='C', new_x="LMARGIN", new_y="NEXT")

    # ── 2. ORG INFO (left) + RECEIPT INFO (right) ──
    pdf.set_text_color(50, 50, 50)
    y_info = 58

    # Left: Organization
    pdf.set_y(y_info)
    pdf.set_x(lm)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(30, 81, 60)
    pdf.cell(95, 5, 'ORGANIZATION', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(60, 60, 60)
    pdf.set_font('helvetica', '', 9)
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'PawsHaven Rescue & Pharmacy Inc.', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, '123 Rescue Way, San Francisco, CA 94103', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'Phone: +1 (415) 555-PAWS (7297)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'Email: donations@pawshaven.org', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'Web: www.pawshaven.org', new_x="LMARGIN", new_y="NEXT")

    # Right: Receipt details box
    pdf.set_y(y_info)
    rx = 120
    pdf.set_fill_color(245, 248, 246)
    pdf.set_draw_color(200, 215, 205)
    pdf.rect(rx, y_info, 80, 32, 'DF')

    pdf.set_x(rx + 3)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(30, 81, 60)
    pdf.cell(74, 5, 'RECEIPT DETAILS', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('helvetica', '', 9)
    for label, val in [('Receipt No:', receipt_no), ('Transaction ID:', txn_id), ('Date:', issue_date), ('Time:', issue_time)]:
        pdf.set_x(rx + 3)
        pdf.set_font('helvetica', 'B', 8)
        pdf.cell(28, 5, label)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(46, 5, val, new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.set_draw_color(200, 215, 205)
    pdf.line(lm, 95, 200, 95)

    # ── 3. REGISTRATION & TAX DETAILS ──────────────
    pdf.set_y(98)
    pdf.set_fill_color(245, 248, 246)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(30, 81, 60)
    pdf.set_x(lm)
    pdf.cell(pw, 6, '  REGISTRATION & TAX IDENTIFIERS', fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(50, 50, 50)
    pdf.set_font('helvetica', '', 8)
    reg_y = pdf.get_y() + 2
    pdf.set_y(reg_y)

    reg_items = [
        ('EIN (Tax ID):', '84-1234567'),
        ('GST No:', '24AAAPH1234A1Z0'),
        ('Charity Reg:', 'REG-2024-PH-001'),
        ('Tax Status:', '501(c)(3) Nonprofit'),
    ]
    col_w = pw / 2
    for i, (lab, val) in enumerate(reg_items):
        col = i % 2
        if col == 0 and i > 0:
            reg_y += 5
        pdf.set_y(reg_y)
        pdf.set_x(lm + col * col_w)
        pdf.set_font('helvetica', 'B', 8)
        pdf.cell(25, 5, lab)
        pdf.set_font('helvetica', '', 8)
        pdf.cell(col_w - 25, 5, val)

    # ── 4. DONOR INFORMATION ───────────────────────
    donor_y = reg_y + 12
    pdf.set_y(donor_y)
    pdf.set_fill_color(245, 248, 246)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(30, 81, 60)
    pdf.set_x(lm)
    pdf.cell(pw, 6, '  DONOR INFORMATION', fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(50, 50, 50)
    dy = pdf.get_y() + 2
    donor_fields = [
        ('Full Name:', donor_name),
        ('Account ID:', str(donor_id)),
        ('Email:', donor_email),
        ('Contribution Type:', 'Voluntary Donation'),
    ]
    for i, (lab, val) in enumerate(donor_fields):
        col = i % 2
        if col == 0 and i > 0:
            dy += 5
        pdf.set_y(dy)
        pdf.set_x(lm + col * col_w)
        pdf.set_font('helvetica', 'B', 8)
        pdf.cell(28, 5, lab)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(col_w - 28, 5, val)

    # ── 5. ITEMIZED TABLE ──────────────────────────
    tbl_y = dy + 14
    pdf.set_y(tbl_y)
    pdf.set_fill_color(30, 81, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(30, 81, 60)
    pdf.set_font('helvetica', 'B', 9)

    # Table Header
    pdf.set_x(lm)
    pdf.cell(15, 8, ' #', border=1, fill=True)
    pdf.cell(95, 8, ' Description', border=1, fill=True)
    pdf.cell(30, 8, ' Category', border=1, fill=True, align='C')
    pdf.cell(50, 8, ' Amount (USD)', border=1, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")

    # Table Row 1
    pdf.set_text_color(50, 50, 50)
    pdf.set_draw_color(210, 210, 210)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font('helvetica', '', 9)
    pdf.set_x(lm)
    pdf.cell(15, 10, ' 1', border=1)
    pdf.cell(95, 10, ' Charitable Donation - General Fund', border=1)
    pdf.cell(30, 10, 'Donation', border=1, align='C')
    pdf.set_font('helvetica', '', 10)
    pdf.cell(50, 10, f'${amount:.2f}', border=1, align='C', new_x="LMARGIN", new_y="NEXT")

    # Summary rows (right-aligned)
    summary_x = lm + 110
    summary_w1 = 30
    summary_w2 = 50
    pdf.set_font('helvetica', '', 9)

    for label, value in [('Subtotal:', f'${amount:.2f}'), ('Tax (0%):', '$0.00'), ('Processing Fee:', '$0.00')]:
        pdf.set_x(summary_x)
        pdf.cell(summary_w1, 7, label, border='LB', align='R')
        pdf.cell(summary_w2, 7, value, border='RB', align='C', new_x="LMARGIN", new_y="NEXT")

    # Grand Total
    pdf.set_fill_color(30, 81, 60)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_x(summary_x)
    pdf.cell(summary_w1, 10, 'TOTAL:', border=1, fill=True, align='R')
    pdf.cell(summary_w2, 10, f'${amount:.2f}', border=1, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")

    # ── 6. PAYMENT & METHOD ────────────────────────
    pay_y = pdf.get_y() + 5
    pdf.set_y(pay_y)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(30, 81, 60)
    pdf.set_x(lm)
    pdf.cell(95, 5, 'PAYMENT METHOD', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('helvetica', '', 8)
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'Method: Online Payment (Stripe Gateway)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, f'Status: PAID | Confirmation: {txn_id}', new_x="LMARGIN", new_y="NEXT")

    # ── 7. TERMS & CERTIFICATION ───────────────────
    pdf.set_y(pay_y + 18)
    pdf.set_draw_color(200, 215, 205)
    pdf.line(lm, pdf.get_y(), 200, pdf.get_y())

    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(30, 81, 60)
    pdf.set_x(lm)
    pdf.cell(pw, 4, 'TERMS & CERTIFICATION', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(120, 120, 120)
    pdf.set_font('helvetica', '', 7)
    pdf.set_x(lm)
    pdf.multi_cell(pw, 3.5,
        "1. This receipt certifies that the above-named donor has made a voluntary contribution to PawsHaven Rescue & Pharmacy Inc.\n"
        "2. No goods or services were provided in exchange for this donation. The full amount is tax-deductible under Section 170 of the Internal Revenue Code.\n"
        "3. PawsHaven Rescue & Pharmacy Inc. is a registered 501(c)(3) tax-exempt organization (EIN: 84-1234567).\n"
        "4. Donors are advised to consult a tax professional regarding the deductibility of their contribution.\n"
        "5. This receipt is system-generated and is valid without a physical signature.",
        align='L')

    # ── 8. SIGNATURE BLOCK ─────────────────────────
    sig_y = 272
    pdf.set_draw_color(30, 81, 60)
    pdf.line(15, sig_y, 75, sig_y)
    pdf.line(130, sig_y, 195, sig_y)

    pdf.set_font('helvetica', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.set_y(sig_y + 1)
    pdf.set_x(15)
    pdf.cell(60, 4, 'Authorized Representative', align='C')
    pdf.set_x(130)
    pdf.cell(65, 4, f'Date: {issue_date}', align='C')

    # ── 9. FOOTER BAR ──────────────────────────────
    pdf.set_fill_color(30, 81, 60)
    pdf.rect(0, 287, 210, 10, 'F')
    pdf.set_text_color(200, 230, 210)
    pdf.set_font('helvetica', '', 7)
    pdf.set_y(288)
    pdf.cell(0, 4, 'PawsHaven Rescue & Pharmacy Inc. | www.pawshaven.org | donations@pawshaven.org | +1 (415) 555-PAWS', align='C')

    # ── SAVE ───────────────────────────────────────
    receipt_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'receipts')
    os.makedirs(receipt_dir, exist_ok=True)
    pdf.output(os.path.join(receipt_dir, receipt_filename))

    global_dir = os.path.join(Config.DOCUMENTS_DIR, 'receipts')
    os.makedirs(global_dir, exist_ok=True)
    pdf.output(os.path.join(global_dir, receipt_filename))

    return jsonify({
        'message': f'Thank you! Your donation was successfully processed.',
        'donation': {
            'id': donation_id,
            'original_amount': amount,
            'receipt': receipt_filename
        }
    })



@donations_bp.route('/api/donations/receipt/<filename>', methods=['GET'])
@optional_auth
def get_receipt(filename):
    """
    VULN #7: Forced browsing — receipt files have predictable names, NO AUTHENTICATION REQUIRED.
    /api/donations/receipt/receipt_001.pdf, receipt_002.pdf, receipt_003.pdf ...
    """
    # 1. Check personal sandbox (if logged in)
    if g.sandbox_id:
        sandbox_path = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'receipts', filename)
        if os.path.exists(sandbox_path):
            return send_file(sandbox_path, as_attachment=True, download_name=filename)

    # 2. Check global receipts directory for unauthenticated forced browsing 
    global_path = os.path.join(Config.DOCUMENTS_DIR, 'receipts', filename)
    if os.path.exists(global_path):
        return send_file(global_path, as_attachment=True, download_name=filename)

    return jsonify({'error': 'Receipt not found.'}), 404
