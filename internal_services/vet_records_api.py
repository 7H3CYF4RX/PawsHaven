"""
Internal Vet Records API — SSRF Target (port 8080)
Contains sensitive veterinary records, prescriptions, and flags.
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return '''<html><head><title>PawsHaven Vet Records — Internal</title>
    <style>body{font-family:monospace;background:#1a1a2e;color:#e0e0e0;padding:40px;max-width:800px;margin:0 auto}
    h1{color:#52b788}a{color:#52b788}pre{background:#16213e;padding:16px;border-radius:8px;overflow-x:auto}</style></head>
    <body><h1>🩺 PawsHaven Internal Vet Records API</h1>
    <p>⚠️ INTERNAL USE ONLY — NOT for public access</p>
    <h3>Available Endpoints:</h3>
    <ul><li><a href="/records">/records</a> — All medical records</li>
    <li><a href="/records/1">/records/:id</a> — Specific record</li>
    <li><a href="/prescriptions">/prescriptions</a> — Active prescriptions</li>
    <li><a href="/staff">/staff</a> — Staff directory</li>
    <li><a href="/config">/config</a> — Service configuration</li></ul></body></html>'''

@app.route('/records')
def all_records():
    return jsonify({'records': [
        {'id': 1, 'patient': 'Luna (Golden Retriever)', 'diagnosis': 'Routine vaccination', 'vet': 'Dr. Mitchell', 'date': '2024-03-15', 'internal_notes': 'Owner payment: Visa ending 4242'},
        {'id': 2, 'patient': 'Rocky (German Shepherd)', 'diagnosis': 'Fractured right hind leg', 'vet': 'Dr. Mitchell', 'date': '2024-02-20', 'internal_notes': 'Surgery cost: $4,200 — insurance claim #INS-2024-0847'},
        {'id': 3, 'patient': 'Buddy (Mixed Breed)', 'diagnosis': 'Heart murmur — Grade III', 'vet': 'Dr. Mitchell', 'date': '2024-01-10', 'internal_notes': 'Enalapril 5mg daily. Monthly monitoring required. Owner SSN on file: 482-XX-7291'},
        {'id': 4, 'patient': 'Max (Labrador)', 'diagnosis': 'Puppy vaccination series — Dose 2/3', 'vet': 'Dr. Wilson', 'date': '2024-04-01', 'internal_notes': 'Breeder contract: Sunshine Kennels LLC, EIN: 47-1234567'},
        {'id': 5, 'patient': 'Bella (Poodle)', 'diagnosis': 'Dental cleaning', 'vet': 'Dr. Wilson', 'date': '2024-04-05', 'internal_notes': 'Anesthesia applied. Owner alert on billing.'},
        {'id': 6, 'patient': 'Charlie (Beagle)', 'diagnosis': 'Ear infection', 'vet': 'Dr. Mitchell', 'date': '2024-04-08', 'internal_notes': 'Prescribed antibiotics. Follow-up in 2 weeks.'},
        {'id': 7, 'patient': 'Daisy (Bulldog)', 'diagnosis': 'Skin allergy', 'vet': 'Dr. Wilson', 'date': '2024-04-10', 'internal_notes': 'Allergy panel recommended. Corticosteroids given.'},
        {'id': 8, 'patient': 'Cooper (Boxer)', 'diagnosis': 'Annual checkup', 'vet': 'Dr. Mitchell', 'date': '2024-04-12', 'internal_notes': 'Healthy. Weight 65 lbs.'},
        {'id': 9, 'patient': 'Milo (Dachshund)', 'diagnosis': 'Back pain assessment', 'vet': 'Dr. Wilson', 'date': '2024-04-14', 'internal_notes': 'Strict cage rest. X-rays pending.'},
        {'id': 10, 'patient': 'Sadie (Shih Tzu)', 'diagnosis': 'Eye irritation', 'vet': 'Dr. Mitchell', 'date': '2024-04-16', 'internal_notes': 'Fluorescein stain negative. Prescribed drops.'},
    ]})

@app.route('/records/<int:rid>')
def get_record(rid):
    records = {
        1: {'patient': 'Luna', 'full_history': 'Complete vaccination history, microchip #985141004567892, owner: Jennifer Smith, DOB: 1985-03-22, address: 742 Evergreen Terrace'},
        2: {'patient': 'Rocky', 'full_history': 'Fracture repair right hind leg. Plates and screws inserted. Microchip #4561237890, owner: Tom Baker, address: 101 Maple St'},
        3: {'patient': 'Buddy', 'full_history': 'Ongoing management for Grade III heart murmur. Echocardiogram results attached. Microchip #1234567890'},
        4: {'patient': 'Max', 'full_history': 'Puppy shots schedule. Microchip pending. Owner: Sarah Jones, address: 42 Pine Ave'},
        5: {'patient': 'Bella', 'full_history': 'Routine scaling and polishing. 2 extractions. Microchip #555111222, owner: Alice Wonderland'},
        6: {'patient': 'Charlie', 'full_history': 'Chronic ear infections left ear. Cytology showed yeast. microchip #999888777'},
        7: {'patient': 'Daisy', 'full_history': 'Atopic dermatitis. Started immunotherapy. Microchip #111222333, owner: John Doe, address: 99 Elm St'},
        8: {'patient': 'Cooper', 'full_history': 'Routine checkup. Up to date on all preventatives. Microchip #444555666'},
        9: {'patient': 'Milo', 'full_history': 'IVDD suspected. Referred to neurology. Microchip #777888999, owner: Jane Smith, address: 88 Oak Ln'},
        10: {'patient': 'Sadie', 'full_history': 'Conjunctivitis right eye. No ulceration. Microchip #222333444, owner: Bob Builder, address: 77 Birch Rd'},
    }
    return jsonify(records.get(rid, {'error': 'Record not found'}))

@app.route('/prescriptions')
def prescriptions():
    return jsonify({'prescriptions': [
        {'drug': 'Enalapril 5mg', 'patient': 'Buddy', 'dea_number': 'FM3456781', 'refills_remaining': 3, 'prescriber': 'Dr. Sarah Mitchell, DVM', 'license': 'VET-2019-04821'},
        {'drug': 'Carprofen 75mg', 'patient': 'Rocky', 'dea_number': 'FM3456781', 'refills_remaining': 1, 'prescriber': 'Dr. Sarah Mitchell, DVM'},
        {'drug': 'Amoxicillin 250mg', 'patient': 'Shadow', 'dea_number': 'FM3456781', 'refills_remaining': 0, 'prescriber': 'Dr. James Wilson, DVM'},
    ]})

@app.route('/staff')
def staff():
    return jsonify({'staff': [
        {'name': 'Dr. Sarah Mitchell', 'role': 'Lead Veterinarian', 'email': 'dr.mitchell@pawshaven-internal.org', 'phone': '555-0101', 'salary': '$145,000', 'ssn_last4': '7291'},
        {'name': 'James Cooper', 'role': 'Operations Manager', 'email': 'j.cooper@pawshaven-internal.org', 'phone': '555-0102', 'salary': '$78,000'},
        {'name': 'Maria Garcia', 'role': 'Rescue Coordinator', 'email': 'm.garcia@pawshaven-internal.org', 'phone': '555-0103', 'salary': '$62,000'},
    ]})

@app.route('/config')
def config():
    return jsonify({
        'service': 'vet-records-api',
        'version': '3.2.1',
        'database_url': 'postgresql://vetrecords_rw:V3tR3c0rds_Pr0d!@pawshaven-db.c9ak27s.us-east-1.rds.amazonaws.com:5432/vet_records',
        'redis_url': 'redis://:paws_r3d1s_s3cret@pawshaven-cache.abc123.use1.cache.amazonaws.com:6379/0',
        'api_key': 'vr_live_sk_paws_9f8e7d6c5b4a3210',
        'flag': 'PAWSHAVEN{v3t_r3c0rds_1nt3rn4l_4cc3ss}'
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
