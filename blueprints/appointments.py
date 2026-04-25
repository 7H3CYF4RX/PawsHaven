"""
Appointments Blueprint
Vulnerability: Broken object-level auth (#35)
"""
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from utils.id_encoder import encode_id
from utils import database as db

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/api/appointments', methods=['GET'])
@require_auth
def list_appointments():
    """
    VULN #35: Broken Object-Level Auth — returns ALL appointments in sandbox.
    Optional user_id filter but defaults to showing everyone's data.
    """
    user_id = request.args.get('user_id', None)

    if user_id:
        appointments = db.query_all(g.sandbox_id,
            "SELECT a.*, an.name as animal_name, u.name as user_name FROM appointments a LEFT JOIN animals an ON a.animal_id = an.id LEFT JOIN users u ON a.user_id = u.id WHERE a.user_id = ?",
            [user_id])
    else:
        # VULN: Returns ALL appointments, not just current user's
        appointments = db.query_all(g.sandbox_id,
            "SELECT a.*, an.name as animal_name, u.name as user_name FROM appointments a LEFT JOIN animals an ON a.animal_id = an.id LEFT JOIN users u ON a.user_id = u.id")

    for a in appointments:
        a['encoded_id'] = encode_id('appointment', a['id'])
    return jsonify({'appointments': appointments, 'total': len(appointments)})


@appointments_bp.route('/api/appointments', methods=['POST'])
@require_auth
def create_appointment():
    data = request.get_json()
    apt_id = db.execute_returning_id(g.sandbox_id,
        "INSERT INTO appointments (user_id, animal_id, date, time, type, notes, status) VALUES (?, ?, ?, ?, ?, ?, 'scheduled')",
        [g.current_user['user_id'], data.get('animal_id', 1),
         data.get('date', ''), data.get('time', ''),
         data.get('type', 'checkup'), data.get('notes', '')])

    return jsonify({'message': 'Appointment scheduled!', 'id': encode_id('appointment', apt_id)}), 201


@appointments_bp.route('/api/appointments/<int:apt_id>', methods=['DELETE'])
@require_auth
def delete_appointment(apt_id):
    """VULN: No ownership check — any user can delete any appointment."""
    db.execute(g.sandbox_id, "DELETE FROM appointments WHERE id = ?", [apt_id])
    return jsonify({'message': 'Appointment cancelled.'})
