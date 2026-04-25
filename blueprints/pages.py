"""
Pages Blueprint — Serves all HTML page routes.
"""
from flask import Blueprint, render_template, g, request
from middleware.auth_middleware import optional_auth, require_auth, require_admin
from utils import database as db

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
@optional_auth
def index():
    return render_template('index.html', user=g.current_user)


@pages_bp.route('/about')
@optional_auth
def about():
    return render_template('about.html', user=g.current_user)


@pages_bp.route('/login')
def login_page():
    return render_template('auth/login.html')


@pages_bp.route('/register')
def register_page():
    return render_template('auth/register.html')


@pages_bp.route('/forgot-password')
def forgot_password_page():
    return render_template('auth/forgot_password.html')


@pages_bp.route('/reset-password')
def reset_password_page():
    return render_template('auth/reset_password.html')


@pages_bp.route('/animals')
@optional_auth
def animals_page():
    return render_template('animals/browse.html', user=g.current_user)


@pages_bp.route('/animals/<encoded_id>')
@optional_auth
def animal_detail_page(encoded_id):
    return render_template('animals/detail.html', user=g.current_user, animal_id=encoded_id)


@pages_bp.route('/animals/<encoded_id>/adopt')
@require_auth
def adopt_page(encoded_id):
    return render_template('animals/adopt_form.html', user=g.current_user, animal_id=encoded_id)


@pages_bp.route('/donate')
@optional_auth
def donate_page():
    latest_receipt = None
    if g.current_user and g.sandbox_id:
        donation = db.query_one(g.sandbox_id, "SELECT receipt_path FROM donations WHERE user_id = ? ORDER BY id DESC LIMIT 1", [g.current_user['user_id']])
        if donation:
            latest_receipt = donation['receipt_path']
    return render_template('donations/donate.html', user=g.current_user, latest_receipt=latest_receipt)

@pages_bp.route('/store')
@optional_auth
def store_page():
    return render_template('store/index.html', user=g.current_user)


@pages_bp.route('/contact')
@optional_auth
def contact_page():
    return render_template('community/contact.html', user=g.current_user)


@pages_bp.route('/community')
@require_auth
def community_page():
    return render_template('community/comments.html', user=g.current_user)


@pages_bp.route('/reports/stray')
@require_auth
def stray_reports_page():
    return render_template('community/reports.html', user=g.current_user)


@pages_bp.route('/dashboard')
@require_auth
def dashboard_page():
    return render_template('dashboard/overview.html', user=g.current_user)


@pages_bp.route('/dashboard/profile')
@require_auth
def profile_page():
    return render_template('dashboard/profile.html', user=g.current_user)


@pages_bp.route('/dashboard/appointments')
@require_auth
def appointments_page():
    return render_template('services/appointments.html', user=g.current_user)


@pages_bp.route('/dashboard/adoptions')
@require_auth
def adoptions_page():
    return render_template('dashboard/adoptions.html', user=g.current_user)


@pages_bp.route('/appointments/new')
@require_auth
def new_appointment_page():
    return render_template('services/appointments.html', user=g.current_user)


@pages_bp.route('/newsletter')
@optional_auth
def newsletter_page():
    return render_template('newsletter/subscribe.html', user=g.current_user)


@pages_bp.route('/vet/diagnose')
@require_auth
def vet_diagnose_page():
    return render_template('services/vet_tools.html', user=g.current_user)


@pages_bp.route('/animals/import')
@require_auth
def import_page():
    return render_template('animals/import.html', user=g.current_user)


@pages_bp.route('/export')
@require_auth
def export_page():
    return render_template('dashboard/export.html', user=g.current_user)


@pages_bp.route('/integrations')
@require_auth
def integrations_page():
    return render_template('dashboard/integrations.html', user=g.current_user)


@pages_bp.route('/admin')
@require_admin
def admin_page():
    return render_template('admin/panel.html', user=g.current_user)


@pages_bp.route('/admin/review')
@require_admin
def admin_review_page():
    return render_template('admin/review_queue.html', user=g.current_user)


@pages_bp.route('/admin/adoptions')
@require_admin
def admin_adoptions_page():
    return render_template('admin/adoptions.html', user=g.current_user)
