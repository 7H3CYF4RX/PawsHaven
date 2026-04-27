import requests
import json
import base64
import os
import time

BASE_URL = "http://127.0.0.1:5000"
TOKEN = ""
ENCODED_ANIMAL_ID = ""
ENCODED_ADOPTION_ID = ""
ENCODED_APPOINTMENT_ID = ""

def log_test(name, response):
    status = "PASS" if response.status_code < 400 or (response.status_code == 404 and "not found" in response.text.lower()) else "FAIL"
    # Special case: 403 for subscribe is expected in the code
    if "/api/premium/subscribe" in response.url and response.status_code == 403:
        status = "PASS (Expected Block)"
    
    print(f"[{status}] {name} - {response.status_code} {response.reason}")
    if status == "FAIL":
        try:
            print(f"      Response: {response.json()}")
        except:
            print(f"      Response: {response.text[:200]}")

def test_all():
    global TOKEN, ENCODED_ANIMAL_ID, ENCODED_ADOPTION_ID, ENCODED_APPOINTMENT_ID
    
    print("--- STARTING FULL API TEST ---")

    # 1. Auth & Registration (Use @pawshaven.org to get ADMIN role)
    print("\n[Section: Auth]")
    reg_data = {"name": "Admin Auditor", "email": "admin_audit@pawshaven.org", "password": "adminpassword"}
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=reg_data)
    # If already exists, just login
    login_data = {"email": "admin_audit@pawshaven.org", "password": "adminpassword"}
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    log_test("POST /api/auth/login (Admin)", resp)
    if resp.status_code == 200:
        TOKEN = resp.json().get('token')
        print(f"      Admin Token Acquired")

    headers = {"Authorization": f"Bearer {TOKEN}"}

    # 2. Users
    print("\n[Section: Users]")
    resp = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
    log_test("GET /api/users/me", resp)
    
    resp = requests.put(f"{BASE_URL}/api/users/me", headers=headers, json={"name": "Master Auditor"})
    log_test("PUT /api/users/me", resp)

    # 3. Animals
    print("\n[Section: Animals]")
    resp = requests.get(f"{BASE_URL}/api/animals", headers=headers)
    log_test("GET /api/animals", resp)

    resp = requests.post(f"{BASE_URL}/api/animals", headers=headers, json={
        "name": "AuditPet", "species": "Dog", "breed": "Beagle"
    })
    log_test("POST /api/animals", resp)
    if resp.status_code == 201:
        ENCODED_ANIMAL_ID = resp.json().get('id')

    if ENCODED_ANIMAL_ID:
        resp = requests.get(f"{BASE_URL}/api/animals/{ENCODED_ANIMAL_ID}", headers=headers)
        log_test("GET /api/animals/{id}", resp)
        
        resp = requests.put(f"{BASE_URL}/api/animals/{ENCODED_ANIMAL_ID}", headers=headers, json={"age": "5 years"})
        log_test("PUT /api/animals/{id}", resp)
        
        resp = requests.get(f"{BASE_URL}/api/animals/{ENCODED_ANIMAL_ID}/medical", headers=headers)
        log_test("GET /api/animals/{id}/medical", resp)

    # 4. Adoptions
    print("\n[Section: Adoptions]")
    if ENCODED_ANIMAL_ID:
        resp = requests.post(f"{BASE_URL}/api/animals/{ENCODED_ANIMAL_ID}/adopt", headers=headers, json={"reason": "Audit Test"})
        log_test("POST /api/animals/{id}/adopt", resp)
        if resp.status_code == 201:
            ENCODED_ADOPTION_ID = resp.json().get('adoption_id')

    resp = requests.get(f"{BASE_URL}/api/adoptions", headers=headers)
    log_test("GET /api/adoptions", resp)

    if ENCODED_ADOPTION_ID:
        resp = requests.post(f"{BASE_URL}/api/admin/adoptions/{ENCODED_ADOPTION_ID}/respond", headers=headers, json={"status": "approved", "notes": "Tested by Auditor"})
        log_test("POST /api/admin/adoptions/{id}/respond", resp)
        
        resp = requests.get(f"{BASE_URL}/api/adoptions/{ENCODED_ADOPTION_ID}/certificate", headers=headers)
        log_test("GET /api/adoptions/{id}/certificate", resp)

    # 5. Appointments
    print("\n[Section: Appointments]")
    resp = requests.post(f"{BASE_URL}/api/appointments", headers=headers, json={"animal_id": 1, "date": "2024-05-01", "time": "10:00"})
    log_test("POST /api/appointments", resp)
    
    resp = requests.get(f"{BASE_URL}/api/appointments", headers=headers)
    log_test("GET /api/appointments", resp)

    # 6. Community & Reports
    print("\n[Section: Community & Reports]")
    resp = requests.post(f"{BASE_URL}/api/comments", headers=headers, json={"content": "Audit comment", "animal_id": 1})
    log_test("POST /api/comments", resp)
    
    resp = requests.get(f"{BASE_URL}/api/comments", headers=headers)
    log_test("GET /api/comments", resp)
    
    resp = requests.post(f"{BASE_URL}/api/reports/stray", headers=headers, json={"location": "Sector 7", "description": "Audit Report"})
    log_test("POST /api/reports/stray", resp)
    
    resp = requests.get(f"{BASE_URL}/api/reports/stray", headers=headers)
    log_test("GET /api/reports/stray", resp)

    # 7. Store & Donations
    print("\n[Section: Store & Donations]")
    resp = requests.get(f"{BASE_URL}/api/donations", headers=headers)
    log_test("GET /api/donations", resp)
    
    resp = requests.post(f"{BASE_URL}/api/donations", headers=headers, json={"amount": 50, "card_number": "1111222233334444", "expiry": "12/26", "cvc": "123"})
    log_test("POST /api/donations", resp)
    
    resp = requests.post(f"{BASE_URL}/api/store/coupon", headers=headers, json={"code": "RESCUE25"})
    log_test("POST /api/store/coupon", resp)
    
    resp = requests.post(f"{BASE_URL}/api/store/checkout", headers=headers, json={"amount": 100, "coupon_code": "RESCUE25", "card_number": "1111222233334444", "expiry": "12/26", "cvc": "123"})
    log_test("POST /api/store/checkout", resp)
    
    resp = requests.get(f"{BASE_URL}/api/store/latest-invoice", headers=headers)
    log_test("GET /api/store/latest-invoice", resp)

    # 8. Premium & Misc
    print("\n[Section: Premium & Misc]")
    resp = requests.get(f"{BASE_URL}/api/premium/status", headers=headers)
    log_test("GET /api/premium/status", resp)
    
    resp = requests.post(f"{BASE_URL}/api/premium/apply-theme", headers=headers, json={"theme": "galaxy"})
    log_test("POST /api/premium/apply-theme", resp)
    
    resp = requests.get(f"{BASE_URL}/api/health")
    log_test("GET /api/health", resp)
    
    resp = requests.get(f"{BASE_URL}/api/broadcast/check", headers=headers)
    log_test("GET /api/broadcast/check", resp)

    print("\n--- API TEST COMPLETE ---")

if __name__ == "__main__":
    test_all()
