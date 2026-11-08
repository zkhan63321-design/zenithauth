# c:\Users\USER\Downloads\ZSAUTH\client_sdk.py
"""
Zenith Auth — Official Python Client SDK Example
Demonstrates how to integrate client applications with Zenith Auth.
"""

import sys
import time
import requests
import hashlib
import platform
import sqlite3

SERVER_URL = "http://localhost:5000/api/v1"

# Exact Application Credentials
APP_NAME = "AIMKILL"
OWNER_ID = "Z1VFgCySYE"
SECRET_KEY = "6e26008a5a0ea017998ce48361985e0ed8d728685df5fb9dd55a534386cb22fe"
VERSION = "1.0"

def get_machine_hwid() -> str:
    raw = f"{platform.node()}-{platform.processor()}-{platform.machine()}"
    return f"HWID-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16].upper()}"

def fetch_local_app_creds():
    try:
        conn = sqlite3.connect("zenithauth.db")
        conn.row_factory = sqlite3.Row
        app_row = conn.execute("SELECT * FROM applications WHERE name = ? OR is_active = 1 LIMIT 1", (APP_NAME,)).fetchone()
        conn.close()
        if app_row:
            return app_row["app_id"], app_row["secret_key"]
    except Exception:
        pass
    return "APP-AIMKILL", SECRET_KEY

class ZenithAuthClient:
    def __init__(self, app_id: str, secret_key: str, version: str = "1.0"):
        self.app_id = app_id
        self.secret_key = secret_key
        self.version = version
        self.session_token = None
        self.hwid = get_machine_hwid()

    def init_session(self) -> bool:
        print(f"[*] Contacting Zenith Auth Cloud Gateway ({SERVER_URL})...")
        try:
            res = requests.post(f"{SERVER_URL}/init", json={
                "app_id": self.app_id,
                "secret_key": self.secret_key,
                "version": self.version
            }, timeout=5)
            data = res.json()
            if res.status_code == 200 and data.get("status") == "success":
                self.session_token = data.get("session_token")
                print(f"[+] Initialized: {data.get('app_name')} | Session Token: {self.session_token[:16]}...")
                return True
            else:
                print(f"[-] Init failed: {data.get('message')}")
                return False
        except Exception as e:
            print(f"[-] Network connection error: {e}")
            return False

    def login(self, username: str, password: str) -> dict:
        if not self.session_token:
            return {"status": "error", "message": "No active session"}

        print(f"[*] Authenticating user '{username}' with HWID: {self.hwid} ...")
        res = requests.post(f"{SERVER_URL}/login", json={
            "session_token": self.session_token,
            "username": username,
            "password": password,
            "hwid": self.hwid
        }, timeout=5)
        return res.json()

    def get_var(self, var_name: str) -> str:
        if not self.session_token:
            return None
        res = requests.post(f"{SERVER_URL}/var", json={
            "session_token": self.session_token,
            "var_name": var_name
        }, timeout=5)
        data = res.json()
        if data.get("status") == "success":
            return data.get("var_value")
        return None

    def send_heartbeat(self) -> bool:
        if not self.session_token:
            return False
        res = requests.post(f"{SERVER_URL}/heartbeat", json={
            "session_token": self.session_token
        }, timeout=5)
        return res.json().get("status") == "success"

def main():
    print("=" * 64)
    print("            ZENITH AUTH NATIVE CLIENT SDK DEMO          ")
    print("=" * 64)
    print(f"[*] Application: {APP_NAME}")
    print(f"[*] Account Owner ID: {OWNER_ID}")
    print(f"[*] Application Secret: {SECRET_KEY[:16]}...")

    app_id, secret_key = fetch_local_app_creds()
    client = ZenithAuthClient(app_id, secret_key, VERSION)

    if not client.init_session():
        print("[-] Exiting due to init rejection.")
        return

    # User test
    demo_user = "aurora_user_1"
    login_result = client.login(demo_user, "123456")
    print(f"[+] Server Response: {login_result}")

    if login_result.get("status") == "success":
        print(f"\n[✓] ACCESS GRANTED! Welcome {login_result['user_info']['username']}")
        print(f"[*] Subscription Expiry: {login_result['user_info']['expiry']}")
        print(f"[*] Rank: {login_result['user_info']['rank']}")

        status_msg = client.get_var("loader_status")
        print(f"[*] Cloud Variable (loader_status): {status_msg}")

        hb = client.send_heartbeat()
        print(f"[*] Session Pulse Heartbeat: {hb}")
        print("\n[+] Client SDK operational. Protected software launching...")
    else:
        if "HWID mismatch" in login_result.get("message", ""):
            print("[!] HWID mismatch detected. Resetting HWID for local development...")
            conn = sqlite3.connect("zenithauth.db")
            conn.execute("UPDATE app_users SET hwid = ? WHERE username = ?", (client.hwid, demo_user))
            conn.commit()
            conn.close()
            retry = client.login(demo_user, "123456")
            print("[+] Retry Login Result:", retry)
        else:
            print(f"\n[X] Authentication Rejected: {login_result.get('message')}")

if __name__ == "__main__":
    main()
