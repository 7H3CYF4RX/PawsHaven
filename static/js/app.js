/* ═══════════════════════════════════════════════════════════════
   PawsHaven — Global JavaScript
   ═══════════════════════════════════════════════════════════════ */

// ── Auth State ──────────────────────────────────────────────────
function getToken() {
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith('token=')) return c.substring(6);
    }
    return null;
}

function isLoggedIn() { return !!getToken(); }

function getCurrentUser() {
    const token = getToken();
    if (!token) return null;
    try {
        const payload = token.split('.')[1];
        return JSON.parse(atob(payload));
    } catch { return null; }
}

// ── API Helper ──────────────────────────────────────────────────
async function apiRequest(url, options = {}) {
    const defaults = { headers: { 'Content-Type': 'application/json' } };
    const token = getToken();
    if (token) defaults.headers['Authorization'] = `Bearer ${token}`;
    const config = { ...defaults, ...options, headers: { ...defaults.headers, ...options.headers } };
    try {
        const resp = await fetch(url, config);
        let data;
        const ct = resp.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
            data = await resp.json();
        } else {
            data = await resp.text();
        }
        return { ok: resp.ok, status: resp.status, data };
    } catch (e) {
        return { ok: false, status: 0, data: { error: e.message } };
    }
}

// ── Toast Notifications ─────────────────────────────────────────
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${icons[type] || '🐾'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('removing'); setTimeout(() => toast.remove(), 300); }, 4000);
}

// ── Button Loading ──────────────────────────────────────────────
function setLoading(btn, loading) {
    if (loading) {
        btn.dataset.origText = btn.textContent;
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.textContent = btn.dataset.origText || btn.textContent;
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ── HTML Escape ─────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── User Dropdown ───────────────────────────────────────────────
document.addEventListener('click', (e) => {
    const dropdown = document.querySelector('.user-dropdown');
    const avatar = document.querySelector('.navbar-avatar');
    if (dropdown && avatar) {
        if (avatar.contains(e.target)) {
            dropdown.classList.toggle('active');
        } else if (!dropdown.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    }
});

// ── Confirmation Modal ──────────────────────────────────────────
function confirmAction(title, message, confirmText = 'Confirm', type = 'danger') {
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirmModalOverlay');
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const msgEl = document.getElementById('confirmMessage');
        const confirmBtn = document.getElementById('confirmConfirmBtn');
        const cancelBtn = document.getElementById('confirmCancelBtn');

        titleEl.textContent = title;
        msgEl.textContent = message;
        confirmBtn.textContent = confirmText;
        confirmBtn.className = `btn btn-${type}`;

        overlay.classList.remove('hidden');
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            modal.style.transform = 'translateY(0)';
        });

        const cleanup = () => {
            overlay.style.opacity = '0';
            modal.style.transform = 'translateY(20px)';
            setTimeout(() => overlay.classList.add('hidden'), 300);
            confirmBtn.onclick = null;
            cancelBtn.onclick = null;
        };

        confirmBtn.onclick = () => { cleanup(); resolve(true); };
        cancelBtn.onclick = () => { cleanup(); resolve(false); };
    });
}

// ── Logout ──────────────────────────────────────────────────────
async function logout() {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    document.cookie = 'token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    window.location.href = '/';
}

// ── Broadcast System ────────────────────────────────────────────
async function checkBroadcast() {
    const resp = await fetch('/api/broadcast/check');
    if (resp.status === 200) {
        const data = await resp.json();
        const lastSeen = localStorage.getItem('lastBroadcastId');
        
        if (data.id && data.id !== lastSeen) {
            showBroadcastModal(data);
        }
    }
}

function showBroadcastModal(data) {
    const overlay = document.getElementById('broadcastModalOverlay');
    const modal = document.getElementById('broadcastModal');
    const title = document.getElementById('bcModalTitle');
    const msg = document.getElementById('bcModalMessage');

    if (!overlay || !modal) return;

    title.textContent = data.title;
    msg.innerHTML = data.message;
    window.currentBroadcastId = data.id;

    overlay.classList.remove('hidden');
    requestAnimationFrame(() => {
        overlay.style.opacity = '1';
        modal.style.transform = 'scale(1)';
    });
}

function closeBroadcast() {
    const overlay = document.getElementById('broadcastModalOverlay');
    const modal = document.getElementById('broadcastModal');
    
    if (window.currentBroadcastId) {
        localStorage.setItem('lastBroadcastId', window.currentBroadcastId);
    }

    overlay.style.opacity = '0';
    modal.style.transform = 'scale(0.9)';
    setTimeout(() => overlay.classList.add('hidden'), 500);
}

// ── Page Transition & Init ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('fade-in');
    checkBroadcast();
    setInterval(checkBroadcast, 10000); // Check every 10 seconds
});
