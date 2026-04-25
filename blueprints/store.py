"""
Store Blueprint — PawsHaven Pharmacy & Supplies
Vulnerabilities: Business logic coupon reuse (#14), Race condition (#30)
"""
import time
import os
from flask import Blueprint, request, jsonify, g, send_file
from middleware.auth_middleware import require_auth
from utils import database as db
from config import Config
from fpdf import FPDF

store_bp = Blueprint('store', __name__)


def generate_store_invoice(order_id, buyer, amount, final_amount, discount, coupon_code, items_desc):
    """Generate a premium A4 invoice PDF for a store purchase."""
    txn_id    = f"ORD-{order_id:05d}"
    inv_no    = f"INV-{order_id:05d}"
    issue_date = time.strftime("%B %d, %Y")
    issue_time = time.strftime("%I:%M %p")
    buyer_name  = buyer.get('name', 'Valued Customer')
    buyer_email = buyer['email']
    buyer_id    = buyer.get('user_id', 'N/A')

    pdf = FPDF()
    pdf.add_page()
    pw = 190  # usable width
    lm = 10   # left margin

    # ── 1. HEADER ──────────────────────────────────
    pdf.set_fill_color(20, 60, 100)        # Deep blue for store
    pdf.rect(0, 0, 210, 48, 'F')
    pdf.set_fill_color(52, 152, 219)       # Accent strip
    pdf.rect(0, 48, 210, 3, 'F')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 26)
    pdf.set_y(10)
    pdf.cell(0, 12, 'PAWSHAVEN', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 9)
    pdf.cell(0, 5, 'Pharmacy & Supplies - Order Invoice', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 10, 'PURCHASE INVOICE', align='C', new_x="LMARGIN", new_y="NEXT")

    # ── 2. ORG (left) + INVOICE DETAILS (right) ────
    pdf.set_text_color(50, 50, 50)
    y_info = 58

    pdf.set_y(y_info)
    pdf.set_x(lm)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(20, 60, 100)
    pdf.cell(95, 5, 'SOLD BY', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(60, 60, 60)
    pdf.set_font('helvetica', '', 9)
    for line in ['PawsHaven Rescue & Pharmacy Inc.',
                 '123 Rescue Way, San Francisco, CA 94103',
                 'Phone: +1 (415) 555-PAWS (7297)',
                 'Email: store@pawshaven.org',
                 'Web: www.pawshaven.org/store']:
        pdf.set_x(lm)
        pdf.cell(95, 4.5, line, new_x="LMARGIN", new_y="NEXT")

    # Right: Invoice details box
    rx = 120
    pdf.set_y(y_info)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(180, 200, 230)
    pdf.rect(rx, y_info, 80, 34, 'DF')
    pdf.set_x(rx + 3)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(20, 60, 100)
    pdf.cell(74, 5, 'INVOICE DETAILS', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    for label, val in [('Invoice No:', inv_no), ('Order ID:', txn_id),
                       ('Date:', issue_date), ('Time:', issue_time)]:
        pdf.set_x(rx + 3)
        pdf.set_font('helvetica', 'B', 8)
        pdf.cell(28, 5, label)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(46, 5, val, new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.set_draw_color(180, 200, 230)
    pdf.line(lm, 97, 200, 97)

    # ── 3. TAX / REG IDENTIFIERS ───────────────────
    pdf.set_y(100)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(20, 60, 100)
    pdf.set_x(lm)
    pdf.cell(pw, 6, '  REGISTRATION & TAX IDENTIFIERS', fill=True, new_x="LMARGIN", new_y="NEXT")

    col_w = pw / 2
    reg_y = pdf.get_y() + 2
    for i, (lab, val) in enumerate([('GST No:', '24AAAPH1234A1Z0'),
                                     ('EIN (Tax ID):', '84-1234567'),
                                     ('Store Reg:', 'STR-2024-PH-002'),
                                     ('Tax Status:', '501(c)(3) Nonprofit')]):
        col = i % 2
        if col == 0 and i > 0:
            reg_y += 5
        pdf.set_y(reg_y)
        pdf.set_x(lm + col * col_w)
        pdf.set_font('helvetica', 'B', 8)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(25, 5, lab)
        pdf.set_font('helvetica', '', 8)
        pdf.cell(col_w - 25, 5, val)

    # ── 4. BUYER INFO ──────────────────────────────
    buyer_y = reg_y + 12
    pdf.set_y(buyer_y)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(20, 60, 100)
    pdf.set_x(lm)
    pdf.cell(pw, 6, '  BUYER INFORMATION', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    dy = pdf.get_y() + 2
    for i, (lab, val) in enumerate([('Full Name:', buyer_name), ('Account ID:', str(buyer_id)),
                                     ('Email:', buyer_email), ('Payment Method:', 'Credit Card (Stripe)')]):
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
    pdf.set_fill_color(20, 60, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(20, 60, 100)
    pdf.set_font('helvetica', 'B', 9)
    pdf.set_x(lm)
    pdf.cell(15, 8, ' #', border=1, fill=True)
    pdf.cell(105, 8, ' Item Description', border=1, fill=True)
    pdf.cell(20, 8, ' Qty', border=1, fill=True, align='C')
    pdf.cell(50, 8, ' Amount (USD)', border=1, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(50, 50, 50)
    pdf.set_draw_color(210, 210, 210)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font('helvetica', '', 9)
    pdf.set_x(lm)
    pdf.cell(15, 12, ' 1', border=1)
    pdf.cell(105, 12, f' {items_desc}', border=1)
    pdf.cell(20, 12, '1', border=1, align='C')
    pdf.set_font('helvetica', '', 10)
    pdf.cell(50, 12, f'${amount:.2f}', border=1, align='C', new_x="LMARGIN", new_y="NEXT")

    # Summary rows
    sx = lm + 110
    sw1, sw2 = 30, 50
    rows = [('Subtotal:', f'${amount:.2f}'), ('GST (0%):', '$0.00')]
    if discount > 0:
        rows.append((f'Discount ({discount}%):', f'-${amount - final_amount:.2f}'))
    if coupon_code:
        rows.append(('Coupon Applied:', coupon_code))

    pdf.set_font('helvetica', '', 9)
    for label, value in rows:
        pdf.set_x(sx)
        pdf.cell(sw1, 7, label, border='LB', align='R')
        pdf.cell(sw2, 7, value, border='RB', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(20, 60, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_x(sx)
    pdf.cell(sw1, 10, 'TOTAL:', border=1, fill=True, align='R')
    pdf.cell(sw2, 10, f'${final_amount:.2f}', border=1, fill=True, align='C', new_x="LMARGIN", new_y="NEXT")

    # ── 6. PAYMENT STATUS ──────────────────────────
    pay_y = pdf.get_y() + 5
    pdf.set_y(pay_y)
    pdf.set_font('helvetica', 'B', 8)
    pdf.set_text_color(20, 60, 100)
    pdf.set_x(lm)
    pdf.cell(95, 5, 'PAYMENT STATUS', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)
    pdf.set_font('helvetica', '', 8)
    pdf.set_x(lm)
    pdf.cell(95, 4.5, f'Status: PAID  |  Confirmation: {txn_id}', new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(lm)
    pdf.cell(95, 4.5, 'Gateway: Stripe Online Payment', new_x="LMARGIN", new_y="NEXT")

    # ── 7. TERMS ───────────────────────────────────
    pdf.set_y(pay_y + 18)
    pdf.set_draw_color(180, 200, 230)
    pdf.line(lm, pdf.get_y(), 200, pdf.get_y())
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font('helvetica', 'B', 7)
    pdf.set_text_color(20, 60, 100)
    pdf.set_x(lm)
    pdf.cell(pw, 4, 'TERMS & CONDITIONS', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(120, 120, 120)
    pdf.set_font('helvetica', '', 7)
    pdf.set_x(lm)
    pdf.multi_cell(pw, 3.5,
        "1. All sales are final. Refunds are processed only for damaged or incorrect items within 7 days of delivery.\n"
        "2. PawsHaven Pharmacy products are intended for animal use only under veterinarian guidance.\n"
        "3. Promotional codes are single-use and cannot be combined with other offers.\n"
        "4. This invoice is system-generated and serves as official proof of purchase.\n"
        "5. For support, contact store@pawshaven.org or call +1 (415) 555-PAWS.", align='L')

    # ── 8. SIGNATURE ───────────────────────────────
    sig_y = 272
    pdf.set_draw_color(20, 60, 100)
    pdf.line(15, sig_y, 75, sig_y)
    pdf.line(130, sig_y, 195, sig_y)
    pdf.set_y(sig_y + 1)
    pdf.set_font('helvetica', '', 7)
    pdf.set_text_color(100, 100, 100)
    pdf.set_x(15)
    pdf.cell(60, 4, 'Authorized Seller', align='C')
    pdf.set_x(130)
    pdf.cell(65, 4, f'Date: {issue_date}', align='C')

    # ── 9. FOOTER ──────────────────────────────────
    pdf.set_fill_color(20, 60, 100)
    pdf.rect(0, 287, 210, 10, 'F')
    pdf.set_text_color(180, 210, 240)
    pdf.set_font('helvetica', '', 7)
    pdf.set_y(288)
    pdf.cell(0, 4, 'PawsHaven Rescue & Pharmacy Inc. | www.pawshaven.org | store@pawshaven.org | +1 (415) 555-PAWS', align='C')

    return pdf


@store_bp.route('/api/store/checkout', methods=['POST'])
@require_auth
def checkout():
    """
    VULN #30: Race condition — coupon check and increment are not atomic.
    Sending concurrent requests can apply a single-use coupon multiple times.
    """
    data = request.get_json()
    amount = float(data.get('amount', 0))
    coupon_code = data.get('coupon_code', '').strip().upper()
    card_number = data.get('card_number', '').replace(' ', '')
    expiry = data.get('expiry', '')
    cvc = data.get('cvc', '')

    if amount <= 0:
        return jsonify({'error': 'Your cart is empty.'}), 400

    # Payment Validation Logic
    if not card_number or len(card_number) < 16:
        return jsonify({'error': 'Invalid card number. Please check your payment details.'}), 400
    if not expiry or not cvc:
        return jsonify({'error': 'Expiry date and CVC are required for payment.'}), 400

    discount = 0
    final_amount = amount

    if coupon_code:
        coupon = db.query_one(g.sandbox_id,
            "SELECT * FROM coupons WHERE code = ? AND active = 1", [coupon_code])

        if not coupon:
            return jsonify({'error': 'Invalid promotion code.'}), 400

        if coupon['times_used'] >= coupon['max_uses']:
            return jsonify({'error': 'This promotional code has exceeded its usage limit.'}), 400

        discount = coupon['discount_percent']
        final_amount = amount * (1 - discount / 100)

        # VULN: Delay before increment — race window!
        time.sleep(0.1)

        db.execute(g.sandbox_id,
            "UPDATE coupons SET times_used = times_used + 1 WHERE code = ?", [coupon_code])

    # Generate unique order ID and invoice filename
    order_id = int(time.time()) % 100000
    invoice_filename = f'invoice_{order_id:05d}.pdf'
    items_desc = 'PawsHaven Pharmacy & Supplies - Mixed Cart Order'

    # Build and save the invoice
    try:
        pdf = generate_store_invoice(order_id, g.current_user, amount, final_amount, discount, coupon_code, items_desc)
        inv_dir = os.path.join(Config.DOCUMENTS_DIR, 'invoices')
        os.makedirs(inv_dir, exist_ok=True)
        pdf.output(os.path.join(inv_dir, invoice_filename))
        # Also save in sandbox for per-user access
        sb_inv_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'invoices')
        os.makedirs(sb_inv_dir, exist_ok=True)
        pdf.output(os.path.join(sb_inv_dir, invoice_filename))
    except Exception:
        invoice_filename = None

    resp = {
        'message': f'Thank you for your purchase! Your order of ${final_amount:.2f} is being prepared.',
        'order': {
            'original_amount': amount,
            'discount': f'{discount}%',
            'final_amount': final_amount,
            'coupon': coupon_code or 'none',
        }
    }
    if invoice_filename:
        resp['invoice'] = invoice_filename

    return jsonify(resp)


@store_bp.route('/api/store/invoice/<filename>', methods=['GET'])
@require_auth
def get_invoice(filename):
    """Serve a store purchase invoice. Checks sandbox first, then global invoices dir."""
    # Sanitize
    filename = os.path.basename(filename)

    if g.sandbox_id:
        sb_path = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'invoices', filename)
        if os.path.exists(sb_path):
            return send_file(sb_path, as_attachment=True, download_name=filename)

    global_path = os.path.join(Config.DOCUMENTS_DIR, 'invoices', filename)
    if os.path.exists(global_path):
        return send_file(global_path, as_attachment=True, download_name=filename)

    return jsonify({'error': 'Invoice not found.'}), 404


@store_bp.route('/api/store/latest-invoice', methods=['GET'])
@require_auth
def get_latest_invoice():
    """Returns the filename of the most recent invoice for the current user."""
    inv_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'invoices')
    if not os.path.isdir(inv_dir):
        return jsonify({'invoice': None})
    files = sorted(
        [f for f in os.listdir(inv_dir) if f.endswith('.pdf')],
        key=lambda f: os.path.getmtime(os.path.join(inv_dir, f)),
        reverse=True
    )
    return jsonify({'invoice': files[0] if files else None})


@store_bp.route('/api/store/coupon', methods=['POST'])
@require_auth
def validate_coupon():
    """
    VULN #14: Business Logic — Coupon reuse. The coupon can be validated and applied
    multiple times because the check is not atomic with the usage in this preview endpoint.
    """
    data = request.get_json()
    code = data.get('code', '').strip().upper()

    if not code:
        return jsonify({'error': 'Please enter a coupon code.'}), 400

    coupon = db.query_one(g.sandbox_id,
        "SELECT * FROM coupons WHERE code = ? AND active = 1", [code])

    if not coupon:
        return jsonify({'error': 'Invalid coupon code.'}), 400

    # Check times_used without incrementing (logic flaw — can be exploited)
    if coupon['times_used'] >= coupon['max_uses']:
        return jsonify({'error': 'This coupon has already been fully redeemed.'}), 400

    return jsonify({
        'valid': True,
        'discount': coupon['discount_percent'],
        'message': f'{coupon["discount_percent"]}% discount successfully applied!'
    })



