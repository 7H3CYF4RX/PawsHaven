"""
Adoptions Blueprint — Adoption applications, certificates
Vulnerabilities: CSRF (#19), Forced browsing (#7)
"""
from flask import Blueprint, request, jsonify, g, send_file
from middleware.auth_middleware import require_auth, require_admin
from utils.id_encoder import encode_id, decode_id
from utils import database as db
import os
from config import Config
from utils.certificate_gen import generate_adoption_certificate

adoptions_bp = Blueprint('adoptions', __name__)


@adoptions_bp.route('/api/animals/<encoded_id>/adopt', methods=['POST'])
@require_auth
def adopt_animal(encoded_id):
    """
    VULN #19: CSRF — no CSRF token validation on this sensitive endpoint.
    Any external site can trigger adoption application via hidden form.
    """
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'animal' or res_id is None:
        return jsonify({'error': 'Invalid animal ID.'}), 400

    data = request.get_json() or {}
    reason = data.get('reason', 'I would love to give this animal a forever home.')

    # No CSRF token check!
    adoption_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO adoptions (user_id, animal_id, reason, status) VALUES (?, ?, ?, 'pending')",
        [g.current_user['user_id'], res_id, reason])

    return jsonify({
        'message': 'Adoption application submitted! We will review it within 48 hours.',
        'adoption_id': encode_id('adoption', adoption_id)
    }), 201


@adoptions_bp.route('/api/adoptions', methods=['GET'])
@require_auth
def list_adoptions():
    """List adoptions. Users see their own, admins see all."""
    if g.current_user.get('role') == 'admin':
        adoptions = db.query_all(g.sandbox_id,
            "SELECT a.*, an.name as animal_name, u.name as user_name FROM adoptions a "
            "LEFT JOIN animals an ON a.animal_id = an.id "
            "LEFT JOIN users u ON a.user_id = u.id ORDER BY a.applied_at DESC")
    else:
        adoptions = db.query_all(g.sandbox_id,
            "SELECT a.*, an.name as animal_name FROM adoptions a "
            "LEFT JOIN animals an ON a.animal_id = an.id WHERE a.user_id = ? ORDER BY a.applied_at DESC",
            [g.current_user['user_id']])
            
    for a in adoptions:
        a['encoded_id'] = encode_id('adoption', a['id'])
    return jsonify({'adoptions': adoptions})


@adoptions_bp.route('/api/admin/adoptions/<encoded_id>/respond', methods=['POST'])
@require_admin
def respond_to_adoption(encoded_id):
    """
    Admin responds to an adoption request (approve/decline).
    """
    res_type, res_id = decode_id(encoded_id)
    if res_id is None:
        return jsonify({'error': 'Invalid adoption ID.'}), 400

    data = request.get_json() or {}
    status = data.get('status') # 'approved' or 'declined'
    notes = data.get('notes', '')

    if status not in ['approved', 'declined']:
        return jsonify({'error': 'Status must be approved or declined.'}), 400

    # Get adoption details
    adoption = db.query_one(g.sandbox_id, "SELECT * FROM adoptions WHERE id = ?", [res_id])
    if not adoption:
        return jsonify({'error': 'Adoption request not found.'}), 404

    from datetime import datetime
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Update adoption
        db.execute(g.sandbox_id,
            "UPDATE adoptions SET status = ?, admin_notes = ?, reviewed_at = ?, approved_at = ? WHERE id = ?",
            [status, notes, now, now if status == 'approved' else None, res_id])

        # If approved, update animal status and generate certificate
        if status == 'approved':
            db.execute(g.sandbox_id,
                "UPDATE animals SET status = 'adopted' WHERE id = ?",
                [adoption['animal_id']])
            
            # Fetch full details for certificate
            user = db.query_one(g.sandbox_id, "SELECT name FROM users WHERE id = ?", [adoption['user_id']])
            animal = db.query_one(g.sandbox_id, "SELECT name, breed, species FROM animals WHERE id = ?", [adoption['animal_id']])
            
            if user and animal:
                cert_filename = f"receipt_{res_id:03d}.pdf"
                cert_dir = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'receipts')
                cert_path = os.path.join(cert_dir, cert_filename)
                
                generate_adoption_certificate(
                    output_path=cert_path,
                    user_name=user['name'],
                    animal_name=animal['name'],
                    breed=animal['breed'],
                    species=animal['species'],
                    adoption_date=now,
                    cert_id=f"PH-{res_id:05d}"
                )
                
                # Update certificate path in DB
                db.execute(g.sandbox_id, "UPDATE adoptions SET certificate_path = ? WHERE id = ?", [cert_filename, res_id])

        return jsonify({
            'message': f'Adoption request {status} successfully.',
            'status': status
        })
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


@adoptions_bp.route('/api/adoptions/<encoded_id>/certificate', methods=['GET'])
@require_auth
def get_certificate(encoded_id):
    """
    VULN #7: Forced browsing — certificates have predictable filenames.
    Can access receipt_003.pdf even though user only has receipt_001 and receipt_002.
    """
    res_type, res_id = decode_id(encoded_id)
    if res_type != 'adoption' or res_id is None:
        return jsonify({'error': 'Invalid adoption ID.'}), 400

    # Predictable path
    cert_path = os.path.join(Config.SANDBOX_DIR, g.sandbox_id, 'receipts', f'receipt_{res_id:03d}.pdf')

    if os.path.exists(cert_path):
        return send_file(cert_path, as_attachment=True, download_name=f'certificate_{res_id}.pdf')

    return jsonify({'error': 'Certificate not found or adoption not yet approved.'}), 404
