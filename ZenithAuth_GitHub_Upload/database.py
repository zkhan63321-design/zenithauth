# c:\Users\USER\Downloads\ZSAUTH\database.py
import sqlite3
import hashlib
import uuid
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "zenithauth.db")

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Developers / Master Platform Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        owner_code TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'Tester', -- 'Owner', 'Seller', 'Developer', 'Tester'
        plan TEXT DEFAULT 'Tester',
        plan_expires TEXT DEFAULT 'Lifetime',
        created_at TEXT NOT NULL,
        avatar_letter TEXT DEFAULT 'Z',
        status TEXT DEFAULT 'ONLINE',
        balance REAL DEFAULT 0.0,
        login_count INTEGER DEFAULT 1,
        last_login TEXT NOT NULL,
        api_key TEXT UNIQUE,
        failed_login_attempts INTEGER DEFAULT 0,
        lock_until TEXT DEFAULT NULL
    )
    """)

    # 2. Applications Table (STARTS COMPLETELY CLEAN / 0 APPS BY DEFAULT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        owner_code TEXT NOT NULL,
        name TEXT NOT NULL,
        version TEXT DEFAULT '1.0',
        secret_key TEXT NOT NULL,
        seller_key TEXT NOT NULL,
        app_id TEXT NOT NULL,
        status TEXT DEFAULT 'Active', -- 'Active', 'Maintenance', 'Paused'
        is_active INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        description TEXT DEFAULT '',
        webhook_url TEXT DEFAULT '',
        download_url TEXT DEFAULT '',
        hwid_lock INTEGER DEFAULT 1,
        force_hwid INTEGER DEFAULT 1,
        block_vpn INTEGER DEFAULT 0,
        hash_check INTEGER DEFAULT 0,
        block_leaked INTEGER DEFAULT 0,
        log_ip INTEGER DEFAULT 1,
        seller_ip_whitelist TEXT DEFAULT '*',
        FOREIGN KEY (owner_id) REFERENCES users (id)
    )
    """)

    # 3. End Users (App Clients) - Enhanced with Arena Auth attributes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER DEFAULT NULL,
        username TEXT NOT NULL,
        email TEXT DEFAULT '',
        password_hash TEXT NOT NULL,
        hwid TEXT DEFAULT '',
        hwid_status TEXT DEFAULT 'unbound', -- 'unbound', 'bound', 'reset_required'
        ip TEXT DEFAULT '',
        license_key TEXT DEFAULT '',
        license_type TEXT DEFAULT '30 Days',
        license_expires_at TEXT DEFAULT '',
        rank TEXT DEFAULT 'Standard',
        expiry_date TEXT NOT NULL,
        account_status TEXT DEFAULT 'active', -- 'active', 'banned', 'disabled'
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT DEFAULT '',
        api_key TEXT UNIQUE,
        failed_login_attempts INTEGER DEFAULT 0,
        lock_until TEXT DEFAULT NULL,
        last_login TEXT DEFAULT '',
        last_validation_at TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 4. Licenses Table - Enhanced with Arena Auth attributes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER DEFAULT NULL,
        license_key TEXT UNIQUE NOT NULL,
        username TEXT DEFAULT '',
        user_id INTEGER DEFAULT NULL,
        type TEXT DEFAULT '30 Days', -- '1 Day', '7 Days', '30 Days', '90 Days', 'Lifetime'
        duration_days INTEGER DEFAULT 30,
        level INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active', -- 'active', 'expired', 'revoked', 'suspended', 'Used', 'Unused'
        used_by TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        expires_at TEXT DEFAULT '',
        used_at TEXT DEFAULT '',
        revoked_at TEXT DEFAULT '',
        revoke_reason TEXT DEFAULT '',
        hwid_hash TEXT DEFAULT '',
        max_devices INTEGER DEFAULT 1,
        current_devices INTEGER DEFAULT 0,
        last_validation_at TEXT DEFAULT '',
        note TEXT DEFAULT '',
        mask_format TEXT DEFAULT 'Standard (6x5)',
        FOREIGN KEY (app_id) REFERENCES applications (id),
        FOREIGN KEY (user_id) REFERENCES app_users (id)
    )
    """)

    # 5. API Keys Table (From Arena Auth ApiKey model)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER DEFAULT NULL,
        key TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 6. Audit & Security Logs (From Arena Auth AuditLog model)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER DEFAULT NULL,
        event TEXT NOT NULL, -- e.g. USER_REGISTERED, LOGIN_SUCCESS, HWID_BOUND, HWID_RESET, LICENSE_VALIDATED
        user_id INTEGER DEFAULT NULL,
        license_id INTEGER DEFAULT NULL,
        ip TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        metadata TEXT DEFAULT '{}',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 7. Cloud Global Variables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS global_vars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        var_name TEXT NOT NULL,
        var_value TEXT NOT NULL,
        is_secret INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 8. Hosted Files
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_size TEXT NOT NULL,
        uploader TEXT DEFAULT 'Admin',
        download_token TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 9. Security Blacklist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        value TEXT NOT NULL,
        reason TEXT DEFAULT 'Unauthorized security breach',
        created_at TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 10. Event Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        ip TEXT NOT NULL,
        hwid TEXT DEFAULT '',
        status TEXT DEFAULT 'Success',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 11. Tamper Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tamper_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        detection_type TEXT NOT NULL,
        details TEXT NOT NULL,
        ip TEXT NOT NULL,
        hwid TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        severity TEXT DEFAULT 'HIGH',
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 12. Active Live Client Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        ip TEXT NOT NULL,
        hwid TEXT NOT NULL,
        last_heartbeat TEXT NOT NULL,
        started_at TEXT NOT NULL,
        FOREIGN KEY (app_id) REFERENCES applications (id)
    )
    """)

    # 13. Payments & UPI Transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        plan TEXT NOT NULL,
        billing_cycle TEXT NOT NULL, -- 'monthly', 'yearly'
        amount REAL NOT NULL,
        upi_id TEXT DEFAULT 'zeeshan1710@fam',
        utr_ref TEXT NOT NULL,
        status TEXT DEFAULT 'Approved',
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()

    # Pre-seed ONLY Master Developer Accounts (ZERO PRE-SEEDED APPLICATIONS AS REQUESTED!)
    cursor.execute("SELECT id FROM users WHERE username = 'ZEESHANHERE'")
    existing_owner = cursor.fetchone()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not existing_owner:
        owner_api_key = f"key_{uuid.uuid4().hex[:16]}"
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, owner_code, role, plan, plan_expires, created_at, avatar_letter, status, balance, login_count, last_login, api_key)
            VALUES (?, ?, ?, 'Z1VFgCySYE', 'Owner', 'Owner', 'Lifetime Access', ?, 'Z', 'ONLINE', 9999.0, 18, ?, ?)
        """, (
            "ZEESHANHERE",
            hash_pw("ZEESHAN1017"),
            "zeeshan@zenithauth.io",
            now_str,
            now_str,
            owner_api_key
        ))

        # Seed Tester User (10-char Owner ID matching KeyAuth style)
        tester_api_key = f"key_{uuid.uuid4().hex[:16]}"
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, owner_code, role, plan, plan_expires, created_at, avatar_letter, status, balance, login_count, last_login, api_key)
            VALUES (?, ?, ?, 'Z1TX82kP9m', 'Tester', 'Tester', 'Free Tier', ?, 'T', 'ONLINE', 0.0, 4, ?, ?)
        """, (
            "normal_tester_user",
            hash_pw("123456"),
            "tester@zenithauth.io",
            now_str,
            now_str,
            tester_api_key
        ))

        # IMPORTANT: NO applications are seeded! "APPLICATION KOI BH NAH RKAHO"
        # The applications table starts completely empty (0 applications registered).
        conn.commit()

    conn.close()

def log_audit(event: str, user_id=None, license_id=None, ip="", user_agent="", metadata="", app_id=None):
    try:
        conn = get_db()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO audit_logs (app_id, event, user_id, license_id, ip, user_agent, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (app_id, event, user_id, license_id, ip, user_agent, str(metadata), now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Audit log error: {e}")

if __name__ == "__main__":
    init_db()
    print("[+] Zenith Auth Database initialized with 0 applications (clean slate) and Owner Code Z1VFgCySYE.")
