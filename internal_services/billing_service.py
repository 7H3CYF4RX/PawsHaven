"""
Internal Billing Service — SSRF Target (port 9090)
Contains financial data, donor info, and Stripe keys.
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return '''<html><head><title>PawsHaven Billing — Internal</title>
    <style>body{font-family:monospace;background:#1a1a2e;color:#e0e0e0;padding:40px}h1{color:#e07a2f}a{color:#e07a2f}</style></head>
    <body><h1>💰 PawsHaven Billing Service</h1><p>⚠️ INTERNAL — Restricted Access</p>
    <ul><li><a href="/api/transactions">/api/transactions</a></li>
    <li><a href="/api/donors">/api/donors</a></li>
    <li><a href="/api/config">/api/config</a></li></ul></body></html>'''

@app.route('/api/transactions')
def transactions():
    return jsonify({'transactions': [
        {'id': 'txn_2024_001', 'donor': 'Emily Watson', 'amount': 100.00, 'date': '2024-03-01', 'method': 'Visa *4242', 'status': 'completed'},
        {'id': 'txn_2024_002', 'donor': 'James Cooper', 'amount': 45.00, 'date': '2024-03-15', 'method': 'Mastercard *8888', 'status': 'completed', 'coupon': 'PAWSFRIEND10'},
        {'id': 'txn_2024_003', 'donor': 'Anonymous', 'amount': 5000.00, 'date': '2024-04-01', 'method': 'Wire Transfer', 'status': 'completed', 'note': 'Major donor — Grant #GR-2024-0042'},
        {'id': 'txn_2024_004', 'donor': 'Robert Davis', 'amount': 250.00, 'date': '2024-04-10', 'method': 'Amex *1234', 'status': 'pending'},
    ]})

@app.route('/api/donors')
def donors():
    return jsonify({'donors': [
        {'name': 'Emily Watson', 'email': 'e.watson@email.com', 'total_donated': 2400.00, 'card_last4': '4242', 'address': '456 Oak Avenue, Springfield'},
        {'name': 'Robert Davis', 'email': 'r.davis@email.com', 'total_donated': 6500.00, 'card_last4': '1234', 'address': '789 Maple Dr, Shelbyville'},
        {'name': 'Jennifer Smith', 'email': 'j.smith@email.com', 'total_donated': 1200.00, 'card_last4': '5678', 'address': '321 Pine St, Capital City'},
    ]})

@app.route('/api/config')
def config():
    return jsonify({
        'service': 'billing-service',
        'version': '1.8.0',
        'stripe_publishable_key': 'pk_live_paws_51H3K9JDkf9LkPQm',
        'stripe_secret_key': 'sk_live_paws_4eC39HqLyjWDarjtT1zdp7dc',
        'stripe_webhook_secret': 'whsec_paws_7mK3xR9qYvN2cP5jL8wT4sA6',
        'paypal_client_id': 'AZDxjDScFpQtjWTOUtWKbyN_bDt4OgqaF4eYXlewfBP4-8aaOCOk',
        'bank_routing': '021000021',
        'bank_account': '9876543210',
        'flag': 'PAWSHAVEN{b1ll1ng_d4t4_3xp0s3d_v14_ssrf}'
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9090)
