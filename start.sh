#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# PawsHaven — Platform Startup Script
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║   🐾  PawsHaven Platform — Starting Up...           ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# ── Cleanup ──────────────────────────────────────────────────
echo "[*] Cleaning up existing processes..."
pkill -f "vet_records_api.py" 2>/dev/null || true
pkill -f "billing_service.py" 2>/dev/null || true
pkill -f "metadata_service.py" 2>/dev/null || true
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "next dev -p 3001" 2>/dev/null || true
sleep 1

# ── Create Data Directories ─────────────────────────────────
mkdir -p data/sandboxes
mkdir -p documents

# ── Install Dependencies ─────────────────────────────────────
echo "[*] Checking Python dependencies..."
pip3 install -q --break-system-packages flask requests beautifulsoup4 PyJWT lxml fpdf2 2>/dev/null || \
pip3 install -q flask requests beautifulsoup4 PyJWT lxml fpdf2 2>/dev/null || \
echo "    ⚠ Some dependencies may need manual installation"

# ── Start Internal Services ──────────────────────────────────
echo "[+] Starting Internal Vet Records API (port 8080)..."
python3 internal_services/vet_records_api.py &>/dev/null &

echo "[+] Starting Internal Billing Service (port 9090)..."
python3 internal_services/billing_service.py &>/dev/null &

echo "[+] Starting Cloud Metadata Service (port 1337)..."
python3 internal_services/metadata_service.py &>/dev/null &

sleep 2

# ── Verify Services ──────────────────────────────────────────
echo "[*] Verifying internal services..."
for port in 8080 9090 1337; do
    if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/" | grep -qE "200|404"; then
        echo "    ✓ Service on port $port is running"
    else
        echo "    ⚠ Service on port $port may not be ready yet"
    fi
done

# ── Start React2Shell (optional — requires Node.js) ─────────
if command -v node &>/dev/null && command -v npm &>/dev/null; then
    if [ -d "react2shell/node_modules" ]; then
        echo "[+] Starting React2Shell Gallery (port 3001)..."
        cd react2shell && npm run dev &>/dev/null &
        cd "$SCRIPT_DIR"
        echo "    ✓ React2Shell running on http://localhost:3001"
    else
        echo "[*] React2Shell: Run 'cd react2shell && npm install && npm run dev' to enable"
    fi
else
    echo "[*] React2Shell: Node.js not found. Install Node.js to enable the gallery widget."
fi

# ── Start Main Application ───────────────────────────────────
echo ""
echo "[+] Starting PawsHaven Main Application (port 5000)..."
echo ""
echo "  ════════════════════════════════════════════════════════"
echo ""
echo "  ✅  PawsHaven is running!"
echo ""
echo "    🌐  Website:          http://localhost:5000"
echo "    📧  Register:         http://localhost:5000/register"
echo "    🩺  Vet Records:      http://127.0.0.1:8080 (internal)"
echo "    💰  Billing:          http://127.0.0.1:9090 (internal)"
echo "    ☁️   Metadata:         http://127.0.0.1:1337 (internal)"
echo "    🎨  Gallery:          http://localhost:3001 (if enabled)"
echo ""
echo "  ════════════════════════════════════════════════════════"
echo ""

python3 app.py
