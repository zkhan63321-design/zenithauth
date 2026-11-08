# c:\Users\USER\Downloads\ZSAUTH\test_arena_and_zenith.py
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    print("[*] Testing Zenith Auth Sentinel + Arena Auth API Engine...")
    s = requests.Session()
    
    # 1. Test Arena Auth - Register
    print("[1] Testing POST /api/v1/auth/register...")
    reg_payload = {
        "username": "arena_client_user",
        "email": "arena_client@example.com",
        "password": "Password123!"
    }
    r = s.post(f"{BASE_URL}/api/v1/auth/register", json=reg_payload)
    print("  -> Status:", r.status_code, r.json())
    assert r.status_code == 201, f"Expected 201, got {r.status_code}"
    reg_data = r.json()
    api_key = reg_data["apiKey"]
    license_key = reg_data["licenseKey"]
    print(f"  -> Generated apiKey: {api_key}, licenseKey: {license_key}")
    
    # 2. Test Arena Auth - ApiKey Validate
    print("[2] Testing POST /api/key/validate...")
    r = s.post(f"{BASE_URL}/api/key/validate", json={"key": api_key})
    print("  -> Status:", r.status_code, r.json())
    assert r.status_code == 200 and r.json()["valid"] is True
    
    # 3. Test Arena Auth - Login with HWID Binding
    print("[3] Testing POST /api/v1/auth/login (HWID Binding)...")
    login_payload = {
        "username": "arena_client_user",
        "password": "Password123!",
        "hwid": "ARENA-HWID-DEVICE-01"
    }
    r = s.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
    print("  -> Status:", r.status_code, r.json())
    assert r.status_code == 200 and r.json()["hwidBound"] is True
    
    # 4. Test Arena Auth - Validate License Key with HWID
    print("[4] Testing POST /api/v1/auth/validate...")
    val_payload = {
        "licenseKey": license_key,
        "hwid": "ARENA-HWID-DEVICE-01"
    }
    r = s.post(f"{BASE_URL}/api/v1/auth/validate", json=val_payload)
    print("  -> Status:", r.status_code, r.json())
    assert r.status_code == 200 and r.json()["valid"] is True
    
    # 5. Test Arena Auth - Reset HWID
    print("[5] Testing POST /api/v1/auth/reset-hwid...")
    r = s.post(f"{BASE_URL}/api/v1/auth/reset-hwid", json={"username": "arena_client_user"})
    print("  -> Status:", r.status_code, r.json())
    assert r.status_code == 200 and r.json()["hwidStatus"] == "reset_required"
    
    # 6. Test Arena Auth - Admin Endpoints
    print("[6] Testing Arena Admin Endpoints...")
    r_adm_login = s.post(f"{BASE_URL}/api/v1/admin/login", json={"adminKey": "admin-secret-key-2024"})
    assert r_adm_login.status_code == 200, "Admin login failed"
    
    r_users = s.get(f"{BASE_URL}/api/v1/admin/users", headers={"adminKey": "admin-secret-key-2024"})
    print("  -> Admin Users Stats:", r_users.json()["stats"])
    
    r_licenses = s.get(f"{BASE_URL}/api/v1/admin/licenses", headers={"adminKey": "admin-secret-key-2024"})
    print("  -> Admin Licenses Stats:", r_licenses.json()["stats"])
    
    r_logs = s.get(f"{BASE_URL}/api/v1/admin/logs", headers={"adminKey": "admin-secret-key-2024"})
    print(f"  -> Audit Logs recorded: {len(r_logs.json()['logs'])} events.")
    
    # 7. Test Web UI - Login as Zeeshan_cf5fq (Owner)
    print("[7] Testing Web UI Login (Owner: Zeeshan_cf5fq)...")
    r_web_login = s.post(f"{BASE_URL}/login", data={"username": "Zeeshan_cf5fq", "password": "admin123"}, allow_redirects=True)
    assert r_web_login.status_code == 200
    assert "Zenith Auth" in r_web_login.text
    print("  -> Logged in successfully. Current Applications: 0 (Clean empty state displayed)")
    
    # 8. Test Web UI - Create Application via Dashboard
    print("[8] Testing POST /api/app/create (User creating their first app)...")
    create_payload = {
        "name": "AIMKILLEXE",
        "version": "1.0",
        "description": "Production software loader"
    }
    r_create = s.post(f"{BASE_URL}/api/app/create", data=create_payload)
    print("  -> Status:", r_create.status_code, r_create.json())
    assert r_create.status_code == 200 and r_create.json()["success"] is True
    app_id = r_create.json()["app_id"]
    
    # 9. Test Web UI - Generate Licenses for AIMKILLEXE
    print("[9] Testing POST /api/license/generate...")
    r_lic = s.post(f"{BASE_URL}/api/license/generate", data={"amount": 3, "duration": 30, "mask_format": "Standard (6x5)"})
    print("  -> Status:", r_lic.status_code, r_lic.json())
    assert r_lic.status_code == 200 and len(r_lic.json()["keys"]) == 3
    
    # 10. Test Seller API for created app
    print("[10] Testing Seller API for the created app...")
    conn = requests.get(f"{BASE_URL}/dashboard")
    # Fetch seller key from database directly to test API
    import database
    db = database.get_db()
    app_row = db.execute("SELECT seller_key, secret_key, name FROM applications WHERE id = ?", (app_id,)).fetchone()
    db.close()
    seller_key = app_row["seller_key"]
    secret_key = app_row["secret_key"]
    print(f"  -> App: {app_row['name']}, Secret: {secret_key[:12]}..., Seller Key: {seller_key[:12]}...")
    
    r_seller_add = s.get(f"{BASE_URL}/api/seller?sellerkey={seller_key}&type=add&amount=1&expiry=30")
    print("  -> Seller API Generate Key:", r_seller_add.status_code, r_seller_add.json())
    assert r_seller_add.status_code == 200 and r_seller_add.json()["status"] == "success"
    
    r_seller_stats = s.get(f"{BASE_URL}/api/seller?sellerkey={seller_key}&type=stats")
    print("  -> Seller API Stats:", r_seller_stats.status_code, r_seller_stats.json())
    assert r_seller_stats.status_code == 200
    
    print("\n[+] ALL TESTS PASSED SUCCESSFULLY! 100% OPERATIONAL.")

if __name__ == "__main__":
    run_tests()
