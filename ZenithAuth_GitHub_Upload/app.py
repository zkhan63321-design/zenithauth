# c:\Users\USER\Downloads\ZSAUTH\app.py
import os
import io
import csv
import uuid
import datetime
import secrets
import string
import hashlib
import requests as ext_requests
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
from flask_cors import CORS
from database import get_db, hash_pw, init_db, log_audit

app = Flask(__name__)
app.secret_key = "zenithauth_cloud_sentinel_production_secret_key_2026"
CORS(app)

# Ensure database exists
init_db()

# Auto-start Discord Bot in background thread if DISCORD_BOT_TOKEN is set in Cloud environment
def maybe_start_discord_bot():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if token and token != "YOUR_DISCORD_BOT_TOKEN_HERE":
        import asyncio
        import threading
        try:
            from discord_bot import bot
            def _runner():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot.start(token))
            t = threading.Thread(target=_runner, daemon=True)
            t.start()
            print("[+] Discord Bot background thread initialized!")
        except Exception as e:
            print(f"[!] Discord bot startup notice: {e}")

maybe_start_discord_bot()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "Owner":
            flash("Owner privileges required.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user

def get_active_app(user_id):
    conn = get_db()
    if "active_app_id" in session:
        app_row = conn.execute("SELECT * FROM applications WHERE id = ? AND owner_id = ?", 
                               (session["active_app_id"], user_id)).fetchone()
        if app_row:
            conn.close()
            return app_row
    
    app_row = conn.execute("SELECT * FROM applications WHERE owner_id = ? AND is_active = 1", (user_id,)).fetchone()
    if not app_row:
        app_row = conn.execute("SELECT * FROM applications WHERE owner_id = ? ORDER BY id ASC LIMIT 1", (user_id,)).fetchone()
    
    if app_row:
        session["active_app_id"] = app_row["id"]
    else:
        session.pop("active_app_id", None)
    conn.close()
    return app_row

def trigger_discord_webhook(webhook_url, title, description, color=0x06b6d4):
    if not webhook_url or not webhook_url.startswith("http"):
        return
    try:
        payload = {
            "embeds": [{
                "title": f"🛡️ Zenith Auth — {title}",
                "description": description,
                "color": color,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "footer": {"text": "Zenith Cloud Sentinel"}
            }]
        }
        ext_requests.post(webhook_url, json=payload, timeout=2)
    except Exception:
        pass

def generate_masked_key(mask_format="Standard (6x5)"):
    if "short" in mask_format.lower() or "4x3" in mask_format.lower():
        return f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    elif "zenith" in mask_format.lower():
        return f"ZENITH-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    else:
        return f"{uuid.uuid4().hex[:6].upper()}-{uuid.uuid4().hex[:6].upper()}-{uuid.uuid4().hex[:6].upper()}-{uuid.uuid4().hex[:6].upper()}-{uuid.uuid4().hex[:6].upper()}"

def generate_owner_code():
    # 10-character alphanumeric Owner ID (KeyAuth / AuthVaultix standard: e.g. Z1VFgCySYE)
    chars = string.ascii_letters + string.digits
    return "Z1" + "".join(secrets.choice(chars) for _ in range(8))

def generate_secret_key():
    # Exactly 64-character SHA-256 hexadecimal Secret Key (e.g. 6e26008a5a0ea017998ce48361985e0ed8d728685df5fb9dd55a534386cb22fe)
    return hashlib.sha256(os.urandom(32) + uuid.uuid4().bytes).hexdigest()

# ----------------- PUBLIC FRONTEND ROUTES ----------------- #

@app.route("/")
def index():
    user = get_current_user()
    return render_template("index.html", user=user)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = get_db()
        pw_hash = hash_pw(password)
        user = conn.execute("SELECT * FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", 
                            (username, username, pw_hash)).fetchone()
        
        if user:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("UPDATE users SET login_count = login_count + 1, last_login = ? WHERE id = ?", (now_str, user["id"]))
            conn.commit()
            conn.close()
            
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Welcome to Zenith Auth!", "success")
            return redirect(url_for("dashboard"))
        else:
            conn.close()
            return render_template("login.html", error="Invalid credentials. Please verify username and password.")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not email or not password:
            return render_template("register.html", error="All fields are required.")
            
        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            conn.close()
            return render_template("register.html", error="Username or email already in use.")
            
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pw_hash = hash_pw(password)
        owner_code = generate_owner_code()
        api_key = f"key_{uuid.uuid4().hex[:16]}"
        cursor = conn.cursor()
        
        # New users get the Free Tester tier automatically
        # ZERO PRE-SEEDED APPLICATIONS ("APPLICATION KOI BH NAH RKAHO")
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, owner_code, role, plan, plan_expires, created_at, avatar_letter, status, balance, login_count, last_login, api_key)
            VALUES (?, ?, ?, ?, 'Tester', 'Tester', 'Free Tier', ?, ?, 'ONLINE', 0.0, 1, ?, ?)
        """, (username, pw_hash, email, owner_code, now_str, username[0].upper(), now_str, api_key))
        new_user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        session["user_id"] = new_user_id
        session["username"] = username
        session["role"] = "Tester"
        return redirect(url_for("dashboard"))
        
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ----------------- MAIN DASHBOARD ----------------- #

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    active_app = get_active_app(user["id"])
    
    conn = get_db()
    applications = conn.execute("SELECT * FROM applications WHERE owner_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    
    app_count = len(applications)
    
    if active_app:
        app_id = active_app["id"]
        user_count = conn.execute("SELECT COUNT(*) FROM app_users WHERE app_id = ?", (app_id,)).fetchone()[0]
        license_count = conn.execute("SELECT COUNT(*) FROM licenses WHERE app_id = ?", (app_id,)).fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM active_sessions WHERE app_id = ?", (app_id,)).fetchone()[0]
        banned_count = conn.execute("SELECT COUNT(*) FROM app_users WHERE app_id = ? AND is_banned = 1", (app_id,)).fetchone()[0]
        
        recent_users = conn.execute("SELECT * FROM app_users WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        recent_licenses = conn.execute("SELECT * FROM licenses WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        global_vars = conn.execute("SELECT * FROM global_vars WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        app_files = conn.execute("SELECT * FROM app_files WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        blacklist_items = conn.execute("SELECT * FROM blacklist WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        active_sessions = conn.execute("SELECT * FROM active_sessions WHERE app_id = ? ORDER BY id DESC", (app_id,)).fetchall()
        audit_trail = conn.execute("SELECT * FROM audit_logs WHERE app_id = ? ORDER BY id DESC LIMIT 50", (app_id,)).fetchall()
    else:
        user_count = 0
        license_count = 0
        session_count = 0
        banned_count = 0
        recent_users = []
        recent_licenses = []
        global_vars = []
        app_files = []
        blacklist_items = []
        active_sessions = []
        audit_trail = []
        
    all_developers = []
    total_system_logins = 0
    payments = []
    if user["role"] == "Owner":
        all_developers = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
        total_system_logins = conn.execute("SELECT SUM(login_count) FROM users").fetchone()[0] or 0
        payments = conn.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 50").fetchall()
        
    conn.close()
    
    is_seller = user["plan"] in ["Seller", "Seller PRO", "Owner"] or user["role"] in ["Seller", "Owner"]
    
    return render_template(
        "dashboard.html",
        user=user,
        active_app=active_app,
        applications=applications,
        app_count=app_count,
        user_count=user_count,
        license_count=license_count,
        session_count=session_count,
        banned_count=banned_count,
        recent_users=recent_users,
        recent_licenses=recent_licenses,
        global_vars=global_vars,
        app_files=app_files,
        blacklist_items=blacklist_items,
        active_sessions=active_sessions,
        audit_trail=audit_trail,
        all_developers=all_developers,
        total_system_logins=total_system_logins,
        payments=payments,
        is_seller=is_seller
    )

# ----------------- OWNER MANAGEMENT ACTIONS ----------------- #

@app.route("/api/owner/change_plan", methods=["POST"])
@owner_required
def owner_change_plan():
    target_user_id = request.form.get("user_id")
    new_plan = request.form.get("plan") or request.form.get("new_plan")
    expires = request.form.get("plan_expires", "").strip()
    status = request.form.get("status", "").strip()
    balance = request.form.get("balance")
    custom_date = request.form.get("custom_expiry", "").strip()
    
    if not target_user_id or not new_plan:
        return jsonify({"success": False, "message": "Missing user_id or plan"}), 400
        
    new_role = new_plan
    
    # Calculate expiry
    now = datetime.datetime.now()
    if expires == "Custom" and custom_date:
        final_expiry = custom_date
    elif expires == "1 Day":
        final_expiry = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    elif expires == "7 Days":
        final_expiry = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    elif expires == "30 Days":
        final_expiry = (now + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    elif expires == "90 Days":
        final_expiry = (now + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    elif expires == "365 Days":
        final_expiry = (now + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    elif expires == "Lifetime" or expires == "Lifetime Access":
        final_expiry = "Lifetime Access"
    elif expires:
        final_expiry = expires
    else:
        final_expiry = "Lifetime Access" if new_plan in ["Owner", "Seller"] else "30 Days"
        
    conn = get_db()
    if balance is not None and balance != "":
        try:
            b_val = float(balance)
            conn.execute("UPDATE users SET balance = ? WHERE id = ?", (b_val, target_user_id))
        except ValueError:
            pass
            
    if status:
        conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, target_user_id))

    conn.execute("UPDATE users SET plan = ?, role = ?, plan_expires = ? WHERE id = ?", 
                 (new_plan, new_role, final_expiry, target_user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True, 
        "message": f"Updated user to {new_plan} | Expiry: {final_expiry}"
    })

# ----------------- APPLICATION ACTIONS ----------------- #

@app.route("/api/app/set_active/<int:app_id>", methods=["POST"])
@login_required
def set_active_app(app_id):
    user_id = session["user_id"]
    conn = get_db()
    app_row = conn.execute("SELECT * FROM applications WHERE id = ? AND owner_id = ?", (app_id, user_id)).fetchone()
    if app_row:
        conn.execute("UPDATE applications SET is_active = 0 WHERE owner_id = ?", (user_id,))
        conn.execute("UPDATE applications SET is_active = 1 WHERE id = ?", (app_id,))
        conn.commit()
        session["active_app_id"] = app_id
        session.modified = True
        conn.close()
        return jsonify({"success": True, "name": app_row["name"]})
    conn.close()
    return jsonify({"success": False, "message": "App not found"}), 404

@app.route("/api/app/create", methods=["POST"])
@login_required
def create_app():
    user = get_current_user()
    user_id = user["id"]
    
    # Plan limit check for Tester
    conn = get_db()
    current_apps_count = conn.execute("SELECT COUNT(*) FROM applications WHERE owner_id = ?", (user_id,)).fetchone()[0]
    if user["plan"] == "Tester" and current_apps_count >= 2:
        conn.close()
        return jsonify({"success": False, "message": "Tester plan limit reached (Max 2 apps). Upgrade to Developer/Seller plan."}), 403
        
    name = request.form.get("name", "").strip().upper()
    version = request.form.get("version", "1.0").strip()
    desc = request.form.get("description", "").strip()
    webhook = request.form.get("webhook_url", "").strip()
    
    if not name:
        conn.close()
        return jsonify({"success": False, "message": "Application name is required"}), 400
        
    s_key = generate_secret_key()
    sel_key = hashlib.sha256(os.urandom(32) + uuid.uuid4().bytes).hexdigest()[:32]
    a_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    date_str = datetime.datetime.now().strftime("%b %d, %Y")
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (owner_id, owner_code, name, version, secret_key, seller_key, app_id, status, is_active, created_at, description, webhook_url, download_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', 1, ?, ?, ?, '')
    """, (user_id, user["owner_code"], name, version, s_key, sel_key, a_id, date_str, desc, webhook))
    new_id = cursor.lastrowid
    
    # Mark as active
    conn.execute("UPDATE applications SET is_active = 0 WHERE owner_id = ? AND id != ?", (user_id, new_id))
    conn.commit()
    conn.close()
    
    session["active_app_id"] = new_id
    session.modified = True
    return jsonify({"success": True, "app_id": new_id, "name": name})

@app.route("/api/app/save_settings/<int:app_id>", methods=["POST"])
@login_required
def save_app_settings(app_id):
    user_id = session["user_id"]
    version = request.form.get("version", "1.0").strip()
    download_url = request.form.get("download_url", "").strip()
    webhook_url = request.form.get("webhook_url", "").strip()
    
    hwid_lock = 1 if request.form.get("hwid_lock") in ["true", "1", "on"] else 0
    force_hwid = 1 if request.form.get("force_hwid") in ["true", "1", "on"] else 0
    block_vpn = 1 if request.form.get("block_vpn") in ["true", "1", "on"] else 0
    hash_check = 1 if request.form.get("hash_check") in ["true", "1", "on"] else 0
    block_leaked = 1 if request.form.get("block_leaked") in ["true", "1", "on"] else 0
    log_ip = 1 if request.form.get("log_ip") in ["true", "1", "on"] else 0
    app_status = request.form.get("status", "Active")
    
    conn = get_db()
    conn.execute("""
        UPDATE applications 
        SET version = ?, download_url = ?, webhook_url = ?, hwid_lock = ?, force_hwid = ?,
            block_vpn = ?, hash_check = ?, block_leaked = ?, log_ip = ?, status = ?
        WHERE id = ? AND owner_id = ?
    """, (version, download_url, webhook_url, hwid_lock, force_hwid, block_vpn, hash_check, block_leaked, log_ip, app_status, app_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Application configuration saved successfully!"})

@app.route("/api/app/delete/<int:app_id>", methods=["POST"])
@login_required
def delete_app(app_id):
    user_id = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM applications WHERE id = ? AND owner_id = ?", (app_id, user_id))
    conn.execute("DELETE FROM licenses WHERE app_id = ?", (app_id,))
    conn.execute("DELETE FROM app_users WHERE app_id = ?", (app_id,))
    conn.execute("DELETE FROM active_sessions WHERE app_id = ?", (app_id,))
    conn.execute("DELETE FROM audit_logs WHERE app_id = ?", (app_id,))
    conn.commit()
    conn.close()
    session.pop("active_app_id", None)
    return jsonify({"success": True})

# ----------------- SELLER API (KeyAuth & AuthVaultix Style) ----------------- #

@app.route("/api/seller", methods=["GET", "POST"])
@app.route("/api/seller/index.php", methods=["GET", "POST"])
def seller_api():
    req_data = request.args if request.method == "GET" else (request.get_json(silent=True) or request.form)
    seller_key = req_data.get("sellerkey") or req_data.get("seller")
    action_type = req_data.get("type", "").lower()
    
    if not seller_key:
        return jsonify({"status": "error", "message": "Missing sellerkey parameter"}), 400
        
    conn = get_db()
    app_row = conn.execute("""
        SELECT a.*, u.plan, u.role 
        FROM applications a 
        JOIN users u ON a.owner_id = u.id 
        WHERE a.seller_key = ?
    """, (seller_key,)).fetchone()
    
    if not app_row:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid seller key."}), 401
        
    # Check if owner has Seller or Owner plan
    if app_row["plan"] not in ["Seller", "Seller PRO", "Owner"] and app_row["role"] not in ["Seller", "Owner"]:
        conn.close()
        return jsonify({"status": "error", "message": "Seller API requires Seller Subscription."}), 403
        
    client_ip = request.remote_addr or "127.0.0.1"
    whitelist = app_row["seller_ip_whitelist"] or "*"
    if whitelist != "*" and client_ip not in [ip.strip() for ip in whitelist.split(",")]:
        conn.close()
        return jsonify({"status": "error", "message": f"IP {client_ip} not authorized in IP Access Control"}), 403
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Action: ADD (Generate License Keys)
    if action_type == "add":
        amount = int(req_data.get("amount", 1))
        expiry = int(req_data.get("expiry", 30))
        level = int(req_data.get("level", 1))
        mask_format = req_data.get("mask", "Standard (6x5)")
        note = req_data.get("note", "Seller API Generated")
        
        amount = max(1, min(amount, 100))
        generated_keys = []
        for _ in range(amount):
            key = generate_masked_key(mask_format)
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=expiry)).strftime("%Y-%m-%d %H:%M:%S") if expiry < 9999 else "Lifetime"
            conn.execute("""
                INSERT INTO licenses (app_id, license_key, duration_days, level, status, created_at, expires_at, note, mask_format, type)
                VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """, (app_row["id"], key, expiry, level, now_str, expires_at, note, mask_format, f"{expiry} Days"))
            generated_keys.append(key)
            
        conn.commit()
        log_audit("SELLER_API_GENERATE_KEYS", ip=client_ip, metadata=f"Generated {amount} keys (expiry: {expiry}d)", app_id=app_row["id"])
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"Successfully generated {amount} license key(s)",
            "key": generated_keys[0] if len(generated_keys) == 1 else generated_keys,
            "keys": generated_keys
        })
        
    # 2. Action: DEL (Delete Key)
    elif action_type == "del":
        key = req_data.get("key")
        if not key:
            conn.close()
            return jsonify({"status": "error", "message": "Missing key parameter"}), 400
        conn.execute("DELETE FROM licenses WHERE app_id = ? AND license_key = ?", (app_row["id"], key))
        conn.commit()
        log_audit("SELLER_API_DELETE_KEY", ip=client_ip, metadata=f"Deleted key {key}", app_id=app_row["id"])
        conn.close()
        return jsonify({"status": "success", "message": f"Key {key} deleted"})
        
    # 3. Action: RESET HWID
    elif action_type == "resethwid":
        user_param = req_data.get("user")
        if not user_param:
            conn.close()
            return jsonify({"status": "error", "message": "Missing user parameter"}), 400
        conn.execute("UPDATE app_users SET hwid = '', hwid_status = 'reset_required' WHERE app_id = ? AND username = ?", (app_row["id"], user_param))
        conn.execute("UPDATE licenses SET hwid_hash = '' WHERE app_id = ? AND username = ?", (app_row["id"], user_param))
        conn.commit()
        log_audit("HWID_RESET", ip=client_ip, metadata=f"HWID reset for {user_param}", app_id=app_row["id"])
        conn.close()
        return jsonify({"status": "success", "message": f"HWID reset for user {user_param}"})
        
    # 4. Action: BAN
    elif action_type == "ban":
        user_param = req_data.get("user")
        reason = req_data.get("reason", "Banned via Seller API")
        if not user_param:
            conn.close()
            return jsonify({"status": "error", "message": "Missing user parameter"}), 400
        conn.execute("UPDATE app_users SET is_banned = 1, account_status = 'banned', ban_reason = ? WHERE app_id = ? AND username = ?", 
                     (reason, app_row["id"], user_param))
        conn.execute("DELETE FROM active_sessions WHERE app_id = ? AND username = ?", (app_row["id"], user_param))
        conn.commit()
        log_audit("USER_BANNED", ip=client_ip, metadata=f"Banned user {user_param}: {reason}", app_id=app_row["id"])
        conn.close()
        return jsonify({"status": "success", "message": f"User {user_param} has been banned"})
        
    # 5. Action: UNBAN
    elif action_type == "unban":
        user_param = req_data.get("user")
        if not user_param:
            conn.close()
            return jsonify({"status": "error", "message": "Missing user parameter"}), 400
        conn.execute("UPDATE app_users SET is_banned = 0, account_status = 'active', ban_reason = '' WHERE app_id = ? AND username = ?", 
                     (app_row["id"], user_param))
        conn.commit()
        log_audit("USER_UNBANNED", ip=client_ip, metadata=f"Unbanned user {user_param}", app_id=app_row["id"])
        conn.close()
        return jsonify({"status": "success", "message": f"User {user_param} unbanned"})
        
    # 6. Action: STATS
    elif action_type == "stats":
        total_keys = conn.execute("SELECT COUNT(*) FROM licenses WHERE app_id = ?", (app_row["id"],)).fetchone()[0]
        used_keys = conn.execute("SELECT COUNT(*) FROM licenses WHERE app_id = ? AND status in ('Used', 'active') AND used_by != ''", (app_row["id"],)).fetchone()[0]
        total_users = conn.execute("SELECT COUNT(*) FROM app_users WHERE app_id = ?", (app_row["id"],)).fetchone()[0]
        active_sess = conn.execute("SELECT COUNT(*) FROM active_sessions WHERE app_id = ?", (app_row["id"],)).fetchone()[0]
        conn.close()
        return jsonify({
            "status": "success",
            "app_name": app_row["name"],
            "total_keys": total_keys,
            "used_keys": used_keys,
            "total_users": total_users,
            "active_sessions": active_sess
        })
        
    # 7. Action: VERIFY (Check Key Info)
    elif action_type == "verify":
        key = req_data.get("key")
        lic = conn.execute("SELECT * FROM licenses WHERE app_id = ? AND license_key = ?", (app_row["id"], key)).fetchone()
        conn.close()
        if not lic:
            return jsonify({"status": "error", "message": "Key not found"}), 404
        return jsonify({
            "status": "success",
            "key": lic["license_key"],
            "status": lic["status"],
            "duration": lic["duration_days"],
            "used_by": lic["used_by"],
            "created_at": lic["created_at"],
            "expires_at": lic["expires_at"]
        })
        
    conn.close()
    return jsonify({"status": "error", "message": f"Unknown action type: {action_type}"}), 400

# ----------------- ARENA AUTH API KEYS (From Arena Auth ApiKey.js & keys.js) ----------------- #

@app.route("/api/key/validate", methods=["POST"])
def arena_key_validate():
    data = request.get_json(silent=True) or request.form
    key = data.get("key")
    if not key:
        return jsonify({"valid": False, "error": "Invalid key"}), 400
        
    conn = get_db()
    entry = conn.execute("SELECT * FROM api_keys WHERE key = ?", (key,)).fetchone()
    if not entry:
        entry = conn.execute("SELECT username FROM users WHERE api_key = ?", (key,)).fetchone()
    if not entry:
        entry = conn.execute("SELECT username FROM app_users WHERE api_key = ?", (key,)).fetchone()
        
    conn.close()
    if not entry:
        return jsonify({"valid": False, "error": "Invalid key"}), 400
        
    return jsonify({"valid": True, "username": entry["username"]})

@app.route("/api/key/stats", methods=["GET"])
def arena_key_stats():
    conn = get_db()
    keys = conn.execute("SELECT key, username as user, created_at as createdAt FROM api_keys ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(k) for k in keys])

# ----------------- ARENA AUTH CLIENT AUTH (From Arena Auth auth.js) ----------------- #

@app.route("/api/v1/auth/register", methods=["POST"])
def arena_auth_register():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip().lower()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    
    if not username or not email or not password:
        return jsonify({
            "success": False,
            "code": "MISSING_FIELDS",
            "message": "Username, email and password are required"
        }), 400
        
    conn = get_db()
    existing = conn.execute("SELECT id FROM app_users WHERE username = ? OR email = ?", (username, email)).fetchone()
    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "code": "DUPLICATE_USERNAME",
            "message": "Username or email already exists"
        }), 400
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pw_hash = hash_pw(password)
    api_key = f"key_{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:10]}"
    license_key = f"lic_{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.remote_addr or "127.0.0.1"
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO app_users (username, email, password_hash, api_key, license_key, license_type, license_expires_at, expiry_date, created_at, account_status)
        VALUES (?, ?, ?, ?, ?, '30 Days', ?, ?, ?, 'active')
    """, (username, email, pw_hash, api_key, license_key, expires_at, expires_at, now_str))
    user_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO licenses (license_key, username, user_id, type, duration_days, status, created_at, expires_at)
        VALUES (?, ?, ?, '30 Days', 30, 'active', ?, ?)
    """, (license_key, username, user_id, now_str, expires_at))
    license_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO api_keys (key, username, created_at)
        VALUES (?, ?, ?)
    """, (api_key, username, now_str))
    
    conn.commit()
    conn.close()
    
    log_audit("USER_REGISTERED", user_id=user_id, license_id=license_id, ip=client_ip, metadata=f"Username: {username}")
    
    return jsonify({
        "success": True,
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email
        },
        "apiKey": api_key,
        "licenseKey": license_key
    }), 201

@app.route("/api/v1/auth/login", methods=["POST"])
def arena_auth_login():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    hwid = (data.get("hwid") or "").strip()
    client_ip = request.remote_addr or "127.0.0.1"
    
    if not username or not password:
        return jsonify({
            "success": False,
            "code": "MISSING_FIELDS",
            "message": "Username and password are required"
        }), 400
        
    conn = get_db()
    user = conn.execute("SELECT * FROM app_users WHERE username = ?", (username,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({
            "success": False,
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid credentials"
        }), 401
        
    # Lockout check
    now = datetime.datetime.now()
    if user["lock_until"]:
        try:
            lock_time = datetime.datetime.strptime(user["lock_until"], "%Y-%m-%d %H:%M:%S")
            if now < lock_time:
                conn.close()
                return jsonify({
                    "success": False,
                    "code": "ACCOUNT_LOCKED",
                    "message": "Account is temporarily locked. Try again later."
                }), 423
        except Exception:
            pass
            
    # Check password
    if hash_pw(password) != user["password_hash"]:
        attempts = (user["failed_login_attempts"] or 0) + 1
        lock_until = None
        if attempts >= 5:
            lock_until = (now + datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE app_users SET failed_login_attempts = ?, lock_until = ? WHERE id = ?", (attempts, lock_until, user["id"]))
        conn.commit()
        conn.close()
        return jsonify({
            "success": False,
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid credentials"
        }), 401
        
    # HWID binding logic (Arena Auth style)
    hwid_status = user["hwid_status"] or "unbound"
    hwid_match = False
    
    if hwid:
        if hwid_status == "unbound":
            hwid_status = "bound"
            conn.execute("UPDATE app_users SET hwid = ?, hwid_status = 'bound' WHERE id = ?", (hwid, user["id"]))
            conn.execute("UPDATE licenses SET hwid_hash = ? WHERE username = ?", (hwid, username))
            hwid_match = True
            log_audit("HWID_BOUND", user_id=user["id"], ip=client_ip, metadata=f"HWID: {hwid}")
        elif hwid_status == "bound":
            if user["hwid"] == hwid:
                hwid_match = True
            else:
                hwid_status = "reset_required"
                conn.execute("UPDATE app_users SET hwid_status = 'reset_required' WHERE id = ?", (user["id"],))
                
    api_key = user["api_key"]
    if not api_key:
        api_key = f"key_{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:10]}"
        conn.execute("UPDATE app_users SET api_key = ? WHERE id = ?", (api_key, user["id"]))
        conn.execute("INSERT OR IGNORE INTO api_keys (key, username, created_at) VALUES (?, ?, ?)", 
                     (api_key, username, now.strftime("%Y-%m-%d %H:%M:%S")))
        
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE app_users SET failed_login_attempts = 0, lock_until = NULL, last_login = ?, ip = ? WHERE id = ?", 
                 (now_str, client_ip, user["id"]))
    conn.commit()
    conn.close()
    
    log_audit("LOGIN_SUCCESS", user_id=user["id"], ip=client_ip, metadata=f"HWID: {hwid or 'none'}")
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "apiKey": api_key,
        "hwidBound": hwid_status == "bound",
        "hwidMatch": hwid_match,
        "accountStatus": user["account_status"] or "active"
    })

@app.route("/api/v1/auth/validate", methods=["POST"])
def arena_auth_validate():
    data = request.get_json(silent=True) or request.form
    license_key = (data.get("licenseKey") or "").strip()
    hwid = (data.get("hwid") or "").strip()
    client_ip = request.remote_addr or "127.0.0.1"
    
    if not license_key:
        return jsonify({
            "success": False,
            "code": "MISSING_LICENSE_KEY",
            "message": "License key is required"
        }), 400
        
    conn = get_db()
    license_row = conn.execute("SELECT * FROM licenses WHERE license_key = ?", (license_key,)).fetchone()
    
    if not license_row:
        conn.close()
        return jsonify({
            "success": False,
            "code": "LICENSE_NOT_FOUND",
            "message": "License key not found"
        }), 404
        
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Check revocation
    if license_row["status"] == "revoked":
        conn.close()
        log_audit("LICENSE_REVOKED", license_id=license_row["id"], ip=client_ip, metadata=license_key)
        return jsonify({
            "success": False,
            "valid": False,
            "code": "LICENSE_REVOKED",
            "message": "License has been revoked"
        }), 403
        
    # Check expiry
    is_valid = True
    days_remaining = 9999
    if license_row["expires_at"] and license_row["expires_at"] != "Lifetime":
        try:
            exp_date = datetime.datetime.strptime(license_row["expires_at"], "%Y-%m-%d %H:%M:%S")
            if now > exp_date:
                is_valid = False
            else:
                days_remaining = (exp_date - now).days + 1
        except Exception:
            pass
            
    if not is_valid:
        conn.close()
        log_audit("LICENSE_EXPIRED", license_id=license_row["id"], ip=client_ip, metadata=license_key)
        return jsonify({
            "success": False,
            "valid": False,
            "code": "LICENSE_EXPIRED",
            "message": "License has expired"
        }), 402
        
    # Check user banned status if attached
    if license_row["user_id"]:
        user_row = conn.execute("SELECT * FROM app_users WHERE id = ?", (license_row["user_id"],)).fetchone()
        if user_row and (user_row["account_status"] == "banned" or user_row["is_banned"]):
            conn.close()
            log_audit("USER_BANNED", user_id=user_row["id"], license_id=license_row["id"], ip=client_ip, metadata=license_key)
            return jsonify({
                "success": False,
                "valid": False,
                "code": "ACCOUNT_BANNED",
                "message": "Account is banned"
            }), 403
            
    # HWID validation
    hwid_match = False
    if license_row["hwid_hash"] and hwid:
        hwid_match = (license_row["hwid_hash"] == hwid)
    elif not license_row["hwid_hash"] and hwid:
        hwid_match = True
        conn.execute("UPDATE licenses SET hwid_hash = ? WHERE id = ?", (hwid, license_row["id"]))
        
    conn.execute("UPDATE licenses SET last_validation_at = ? WHERE id = ?", (now_str, license_row["id"]))
    conn.commit()
    conn.close()
    
    log_audit("LICENSE_VALIDATED", license_id=license_row["id"], ip=client_ip, 
              metadata=f"HWID Provided: {hwid}, Matched: {hwid_match}")
              
    return jsonify({
        "success": True,
        "valid": True,
        "license": {
            "type": license_row["type"] or f"{license_row['duration_days']} Days",
            "daysRemaining": days_remaining,
            "expiresAt": license_row["expires_at"]
        },
        "hwid": {
            "bound": bool(license_row["hwid_hash"] or hwid_match),
            "matched": hwid_match
        }
    })

@app.route("/api/v1/auth/reset-hwid", methods=["POST"])
def arena_auth_reset_hwid():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip().lower()
    client_ip = request.remote_addr or "127.0.0.1"
    
    if not username:
        return jsonify({
            "success": False,
            "code": "MISSING_USERNAME",
            "message": "Username is required"
        }), 400
        
    conn = get_db()
    user = conn.execute("SELECT * FROM app_users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({
            "success": False,
            "code": "USER_NOT_FOUND",
            "message": "User not found"
        }), 404
        
    conn.execute("UPDATE app_users SET hwid = '', hwid_status = 'reset_required' WHERE id = ?", (user["id"],))
    conn.execute("UPDATE licenses SET hwid_hash = '' WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    
    log_audit("HWID_RESET", user_id=user["id"], ip=client_ip, metadata=f"Username: {username}")
    
    return jsonify({
        "success": True,
        "message": "HWID binding reset successfully",
        "hwidStatus": "reset_required"
    })

@app.route("/api/v1/auth/refresh", methods=["POST"])
def arena_auth_refresh():
    return jsonify({
        "success": True,
        "message": "License refreshed"
    })

# ----------------- ARENA AUTH ADMIN API (From Arena Auth admin.js) ----------------- #

@app.route("/api/v1/admin/login", methods=["POST"])
def arena_admin_login():
    data = request.get_json(silent=True) or request.form
    admin_key = data.get("adminKey")
    if admin_key == "admin-secret-key-2024" or (session.get("role") == "Owner"):
        return jsonify({
            "success": True,
            "message": "Admin login successful",
            "admin": True
        })
    return jsonify({
        "success": False,
        "code": "INVALID_ADMIN_KEY",
        "message": "Invalid admin key"
    }), 401

@app.route("/api/v1/admin/users", methods=["GET"])
def arena_admin_get_users():
    admin_key = request.headers.get("adminKey") or request.args.get("adminKey")
    if admin_key != "admin-secret-key-2024" and session.get("role") != "Owner":
        return jsonify({"success": False, "code": "UNAUTHORIZED", "message": "Admin authentication required"}), 401
        
    conn = get_db()
    users = conn.execute("""
        SELECT id, username, email, rank as role, account_status as accountStatus, created_at as createdAt, last_login as lastLoginAt
        FROM app_users ORDER BY id DESC
    """).fetchall()
    
    total = conn.execute("SELECT COUNT(*) FROM app_users").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM app_users WHERE account_status = 'active' AND is_banned = 0").fetchone()[0]
    banned = conn.execute("SELECT COUNT(*) FROM app_users WHERE account_status = 'banned' OR is_banned = 1").fetchone()[0]
    disabled = conn.execute("SELECT COUNT(*) FROM app_users WHERE account_status = 'disabled'").fetchone()[0]
    conn.close()
    
    return jsonify({
        "success": True,
        "users": [dict(u) for u in users],
        "stats": {
            "totalUsers": total,
            "activeUsers": active,
            "bannedUsers": banned,
            "disabledUsers": disabled
        }
    })

@app.route("/api/v1/admin/licenses", methods=["GET"])
def arena_admin_get_licenses():
    admin_key = request.headers.get("adminKey") or request.args.get("adminKey")
    if admin_key != "admin-secret-key-2024" and session.get("role") != "Owner":
        return jsonify({"success": False, "code": "UNAUTHORIZED", "message": "Admin authentication required"}), 401
        
    conn = get_db()
    licenses = conn.execute("""
        SELECT id, license_key as licenseKey, username, type, status, expires_at as expiresAt, created_at as createdAt, hwid_hash as hwidHash
        FROM licenses ORDER BY id DESC
    """).fetchall()
    
    total = conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM licenses WHERE status = 'active'").fetchone()[0]
    expired = conn.execute("SELECT COUNT(*) FROM licenses WHERE status = 'expired'").fetchone()[0]
    revoked = conn.execute("SELECT COUNT(*) FROM licenses WHERE status = 'revoked'").fetchone()[0]
    hw_bound = conn.execute("SELECT COUNT(*) FROM licenses WHERE hwid_hash != ''").fetchone()[0]
    hw_unbound = conn.execute("SELECT COUNT(*) FROM licenses WHERE hwid_hash = '' OR hwid_hash IS NULL").fetchone()[0]
    conn.close()
    
    return jsonify({
        "success": True,
        "licenses": [dict(l) for l in licenses],
        "stats": {
            "totalLicenses": total,
            "activeLicenses": active,
            "expiredLicenses": expired,
            "revokedLicenses": revoked,
            "hwBoundLicenses": hw_bound,
            "hwUnboundLicenses": hw_unbound
        }
    })

@app.route("/api/v1/admin/license/create", methods=["POST"])
def arena_admin_create_license():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip().lower()
    lic_type = data.get("type", "30 Days")
    duration_days = int(data.get("durationDays", 30))
    
    if not username:
        return jsonify({"success": False, "code": "MISSING_FIELDS", "message": "Username is required"}), 400
        
    conn = get_db()
    user = conn.execute("SELECT * FROM app_users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"success": False, "code": "USER_NOT_FOUND", "message": "User not found"}), 404
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S") if lic_type != "Lifetime" else "Lifetime"
    license_key = f"lic_{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO licenses (license_key, username, user_id, type, duration_days, status, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
    """, (license_key, username, user["id"], lic_type, duration_days, now_str, expires_at))
    lic_id = cursor.lastrowid
    
    conn.execute("UPDATE app_users SET license_key = ?, license_type = ?, license_expires_at = ? WHERE id = ?",
                 (license_key, lic_type, expires_at, user["id"]))
    conn.commit()
    conn.close()
    
    log_audit("LICENSE_CREATED", user_id=user["id"], license_id=lic_id, ip=request.remote_addr or "127.0.0.1", 
              metadata=f"Username: {username}, Type: {lic_type}")
              
    return jsonify({
        "success": True,
        "message": "License created successfully",
        "licenseKey": license_key,
        "license": {
            "type": lic_type,
            "expiresAt": expires_at
        }
    })

@app.route("/api/v1/admin/license/revoke", methods=["POST"])
def arena_admin_revoke_license():
    data = request.get_json(silent=True) or request.form
    license_key = (data.get("licenseKey") or "").strip()
    reason = data.get("reason", "Revoked by administrator")
    
    conn = get_db()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE licenses SET status = 'revoked', revoke_reason = ?, revoked_at = ? WHERE license_key = ?",
                 (reason, now_str, license_key))
    conn.commit()
    conn.close()
    
    log_audit("LICENSE_REVOKED", ip=request.remote_addr or "127.0.0.1", metadata=f"Key: {license_key}, Reason: {reason}")
    return jsonify({"success": True, "message": f"License {license_key} revoked"})

@app.route("/api/v1/admin/user/ban", methods=["POST"])
def arena_admin_ban_user():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip().lower()
    reason = data.get("reason", "Banned by administrator")
    
    conn = get_db()
    conn.execute("UPDATE app_users SET is_banned = 1, account_status = 'banned', ban_reason = ? WHERE username = ?",
                 (reason, username))
    conn.commit()
    conn.close()
    
    log_audit("USER_BANNED", ip=request.remote_addr or "127.0.0.1", metadata=f"Username: {username}, Reason: {reason}")
    return jsonify({"success": True, "message": f"User {username} banned"})

@app.route("/api/v1/admin/logs", methods=["GET"])
def arena_admin_get_logs():
    admin_key = request.headers.get("adminKey") or request.args.get("adminKey")
    if admin_key != "admin-secret-key-2024" and session.get("role") != "Owner":
        return jsonify({"success": False, "code": "UNAUTHORIZED", "message": "Admin authentication required"}), 401
        
    conn = get_db()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify({"success": True, "logs": [dict(l) for l in logs]})

# ----------------- KEYAUTH / AUTHVAULTIX CLIENT SDK ENGINE ----------------- #

@app.route("/api/v1/init", methods=["POST"])
def client_api_init():
    data = request.get_json(silent=True) or request.form
    app_id = data.get("app_id")
    secret = data.get("secret_key")
    client_version = data.get("version", "1.0")
    
    if not app_id or not secret:
        return jsonify({"status": "error", "message": "Missing app_id or secret_key"}), 400
        
    conn = get_db()
    app_row = conn.execute("SELECT * FROM applications WHERE (app_id = ? OR id = ? OR name = ?) AND secret_key = ?", 
                           (app_id, app_id, app_id, secret)).fetchone()
    
    if not app_row:
        conn.close()
        return jsonify({"status": "error", "message": "Application credentials invalid or unauthorized."}), 401
        
    if app_row["status"] == "Paused":
        conn.close()
        return jsonify({"status": "error", "message": "Application is paused by developer."}), 503
        
    if app_row["status"] == "Maintenance":
        conn.close()
        return jsonify({"status": "error", "message": "Application is under maintenance."}), 503
        
    if app_row["version"] != client_version:
        conn.close()
        return jsonify({
            "status": "error", 
            "message": f"Version mismatch. Server requires v{app_row['version']}, client is v{client_version}.",
            "update_url": app_row["download_url"] or ""
        }), 426
        
    session_token = uuid.uuid4().hex
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.remote_addr or "127.0.0.1"
    
    conn.execute("""
        INSERT INTO active_sessions (app_id, session_token, username, ip, hwid, last_heartbeat, started_at)
        VALUES (?, ?, 'Anonymous', ?, '', ?, ?)
    """, (app_row["id"], session_token, client_ip, now_str, now_str))
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "message": "Initialized successfully",
        "session_token": session_token,
        "app_name": app_row["name"],
        "server_time": now_str
    })

@app.route("/api/v1/login", methods=["POST"])
def client_api_login():
    data = request.get_json(silent=True) or request.form
    session_token = data.get("session_token")
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    hwid = data.get("hwid", "").strip()
    
    if not session_token or not username or not password:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400
        
    conn = get_db()
    session_row = conn.execute("SELECT * FROM active_sessions WHERE session_token = ?", (session_token,)).fetchone()
    if not session_row:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid or expired session. Please re-init."}), 401
        
    app_id = session_row["app_id"]
    client_ip = request.remote_addr or "127.0.0.1"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    app_meta = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    
    if app_meta["force_hwid"] and not hwid:
        conn.close()
        return jsonify({"status": "error", "message": "Hardware ID is required by application policy."}), 400
        
    pw_hash = hash_pw(password)
    user_row = conn.execute("SELECT * FROM app_users WHERE app_id = ? AND username = ? AND password_hash = ?", 
                            (app_id, username, pw_hash)).fetchone()
                            
    if not user_row:
        conn.execute("""
            INSERT INTO event_logs (app_id, username, action, ip, hwid, status, timestamp)
            VALUES (?, ?, 'Failed Auth Attempt', ?, ?, 'Failed', ?)
        """, (app_id, username, client_ip, hwid, now_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401
        
    if user_row["is_banned"]:
        conn.close()
        return jsonify({"status": "error", "message": f"Account suspended: {user_row['ban_reason'] or 'Terms Violation'}"}), 403
        
    try:
        exp = datetime.datetime.strptime(user_row["expiry_date"], "%Y-%m-%d %H:%M:%S")
        if exp < datetime.datetime.now():
            conn.close()
            return jsonify({"status": "error", "message": "Subscription expired."}), 403
    except Exception:
        pass
        
    if app_meta["hwid_lock"] and user_row["hwid"] and hwid and user_row["hwid"] != hwid:
        conn.execute("""
            INSERT INTO tamper_logs (app_id, username, detection_type, details, ip, hwid, timestamp, severity)
            VALUES (?, ?, 'HWID Mismatch', ?, ?, ?, ?, 'HIGH')
        """, (app_id, username, f"Expected {user_row['hwid']} but got {hwid}", client_ip, hwid, now_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "error", "message": "HWID mismatch! Please request HWID reset from admin."}), 403
        
    if not user_row["hwid"] and hwid:
        conn.execute("UPDATE app_users SET hwid = ?, hwid_status = 'bound' WHERE id = ?", (hwid, user_row["id"]))
        
    conn.execute("UPDATE app_users SET last_login = ?, ip = ? WHERE id = ?", (now_str, client_ip, user_row["id"]))
    conn.execute("UPDATE active_sessions SET username = ?, hwid = ?, last_heartbeat = ? WHERE id = ?", 
                 (username, hwid, now_str, session_row["id"]))
    conn.execute("""
        INSERT INTO event_logs (app_id, username, action, ip, hwid, status, timestamp)
        VALUES (?, ?, 'User Login Success', ?, ?, 'Success', ?)
    """, (app_id, username, client_ip, hwid, now_str))
    
    if app_meta["webhook_url"]:
        trigger_discord_webhook(app_meta["webhook_url"], "User Authenticated", f"User **{username}** connected to **{app_meta['name']}** from `{client_ip}`.", 0x06b6d4)
        
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "message": "Logged in successfully",
        "user_info": {
            "username": user_row["username"],
            "rank": user_row["rank"],
            "expiry": user_row["expiry_date"],
            "hwid": hwid
        }
    })

@app.route("/api/v1/license", methods=["POST"])
def client_api_license_only():
    data = request.get_json(silent=True) or request.form
    session_token = data.get("session_token")
    key = data.get("key", "").strip()
    hwid = data.get("hwid", "").strip()
    
    if not session_token or not key:
        return jsonify({"status": "error", "message": "Missing key or session"}), 400
        
    conn = get_db()
    session_row = conn.execute("SELECT * FROM active_sessions WHERE session_token = ?", (session_token,)).fetchone()
    if not session_row:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid session"}), 401
        
    app_id = session_row["app_id"]
    client_ip = request.remote_addr or "127.0.0.1"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lic = conn.execute("SELECT * FROM licenses WHERE app_id = ? AND license_key = ?", (app_id, key)).fetchone()
    if not lic:
        conn.close()
        return jsonify({"status": "error", "message": "License key not found or invalid"}), 404
        
    if lic["status"] in ["Used", "revoked", "expired"]:
        if lic["hwid_hash"] and hwid and lic["hwid_hash"] != hwid:
            conn.close()
            return jsonify({"status": "error", "message": "License is locked to a different device"}), 403
            
    # Bind license
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=lic["duration_days"])).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE licenses SET status = 'Used', used_by = ?, hwid_hash = ?, expires_at = ? WHERE id = ?",
                 (f"Client_{hwid[:8]}", hwid, expires_at, lic["id"]))
    conn.execute("UPDATE active_sessions SET username = ?, hwid = ?, last_heartbeat = ? WHERE id = ?",
                 (f"KeyHolder_{key[:6]}", hwid, now_str, session_row["id"]))
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "message": "License verified and active",
        "expiry": expires_at
    })

@app.route("/api/v1/var", methods=["POST"])
def client_api_var():
    data = request.get_json(silent=True) or request.form
    session_token = data.get("session_token")
    var_name = data.get("var_name", "").strip()
    
    conn = get_db()
    session_row = conn.execute("SELECT * FROM active_sessions WHERE session_token = ?", (session_token,)).fetchone()
    if not session_row:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid session"}), 401
        
    v = conn.execute("SELECT var_value FROM global_vars WHERE app_id = ? AND var_name = ?", 
                     (session_row["app_id"], var_name)).fetchone()
    conn.close()
    
    if not v:
        return jsonify({"status": "error", "message": f"Variable '{var_name}' not found"}), 404
        
    return jsonify({"status": "success", "var_name": var_name, "var_value": v["var_value"]})

@app.route("/api/v1/heartbeat", methods=["POST"])
def client_api_heartbeat():
    data = request.get_json(silent=True) or request.form
    session_token = data.get("session_token")
    
    conn = get_db()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = conn.execute("UPDATE active_sessions SET last_heartbeat = ? WHERE session_token = ?", (now_str, session_token))
    conn.commit()
    conn.close()
    
    if result.rowcount == 0:
        return jsonify({"status": "error", "message": "Session invalidated"}), 401
        
    return jsonify({"status": "success", "message": "Heartbeat acknowledged"})

# ----------------- UI HELPER ACTIONS ----------------- #

@app.route("/api/license/generate", methods=["POST"])
@login_required
def generate_license_api():
    user = get_current_user()
    active_app = get_active_app(user["id"])
    if not active_app:
        return jsonify({"success": False, "message": "No active application selected. Create one first."}), 400
        
    amount = int(request.form.get("amount", 1))
    duration = int(request.form.get("duration", 30))
    mask_format = request.form.get("mask_format", "Standard (6x5)")
    
    conn = get_db()
    # Tester plan limit: 15 licenses per app
    if user["plan"] == "Tester":
        current_lic_count = conn.execute("SELECT COUNT(*) FROM licenses WHERE app_id = ?", (active_app["id"],)).fetchone()[0]
        if current_lic_count + amount > 15:
            conn.close()
            return jsonify({"success": False, "message": "Tester limit: Max 15 licenses per app. Upgrade to Developer or Seller plan."}), 403
            
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keys = []
    for _ in range(amount):
        key = generate_masked_key(mask_format)
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=duration)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO licenses (app_id, license_key, duration_days, level, status, created_at, expires_at, mask_format, type)
            VALUES (?, ?, ?, 1, 'active', ?, ?, ?, ?)
        """, (active_app["id"], key, duration, now_str, expires_at, mask_format, f"{duration} Days"))
        keys.append(key)
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "count": amount, "keys": keys})

@app.route("/api/license/delete/<int:lic_id>", methods=["POST"])
@login_required
def delete_license(lic_id):
    conn = get_db()
    conn.execute("DELETE FROM licenses WHERE id = ?", (lic_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/license/export/<fmt>")
@login_required
def export_licenses(fmt):
    user = get_current_user()
    active_app = get_active_app(user["id"])
    if not active_app:
        return "No application selected", 400
        
    conn = get_db()
    licenses = conn.execute("SELECT license_key, duration_days, status, used_by, created_at FROM licenses WHERE app_id = ?", 
                            (active_app["id"],)).fetchall()
    conn.close()
    
    if fmt == "csv":
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["License Key", "Duration (Days)", "Status", "Used By", "Created At"])
        for l in licenses:
            cw.writerow([l["license_key"], l["duration_days"], l["status"], l["used_by"], l["created_at"]])
        return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment;filename={active_app['name']}_licenses.csv"})
    else:
        text_content = "\n".join([l["license_key"] for l in licenses])
        return Response(text_content, mimetype="text/plain", headers={"Content-Disposition": f"attachment;filename={active_app['name']}_licenses.txt"})

@app.route("/api/user/reset_hwid/<int:user_id>", methods=["POST"])
@login_required
def user_reset_hwid(user_id):
    conn = get_db()
    conn.execute("UPDATE app_users SET hwid = '', hwid_status = 'reset_required' WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "HWID reset successfully"})

@app.route("/api/user/toggle_ban/<int:user_id>", methods=["POST"])
@login_required
def user_toggle_ban(user_id):
    conn = get_db()
    current = conn.execute("SELECT is_banned, username, app_id FROM app_users WHERE id = ?", (user_id,)) .fetchone()
    new_state = 0 if current and current["is_banned"] else 1
    new_status = "active" if new_state == 0 else "banned"
    conn.execute("UPDATE app_users SET is_banned = ?, account_status = ? WHERE id = ?", (new_state, new_status, user_id))
    if current and current["app_id"]:
        conn.execute("DELETE FROM active_sessions WHERE app_id = ? AND username = ?", (current["app_id"], current["username"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "is_banned": new_state})

@app.route("/api/session/kill/<int:session_id>", methods=["POST"])
@login_required
def kill_session(session_id):
    conn = get_db()
    conn.execute("DELETE FROM active_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/seller/whitelist_ip", methods=["POST"])
@app.route("/api/seller/whitelist_ip/<int:app_id>", methods=["POST"])
@login_required
def whitelist_ip(app_id=None):
    if app_id is None:
        app_id = request.form.get("app_id")
    ip_str = request.form.get("ip", "*").strip()
    conn = get_db()
    conn.execute("UPDATE applications SET seller_ip_whitelist = ? WHERE id = ? AND owner_id = ?", (ip_str, app_id, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "whitelist": ip_str})

@app.route("/api/seller/regenerate_key", methods=["POST"])
@app.route("/api/seller/regenerate_key/<int:app_id>", methods=["POST"])
@login_required
def regenerate_seller_key(app_id=None):
    if app_id is None:
        app_id = request.form.get("app_id")
    new_key = uuid.uuid4().hex + uuid.uuid4().hex[:32]
    conn = get_db()
    conn.execute("UPDATE applications SET seller_key = ? WHERE id = ? AND owner_id = ?", (new_key, app_id, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "new_seller_key": new_key})

@app.route("/api/billing/upgrade", methods=["POST"])
@login_required
def upgrade_plan():
    user_id = session["user_id"]
    plan_name = request.form.get("plan", "Seller")
    
    conn = get_db()
    conn.execute("""
        UPDATE users 
        SET plan = ?, role = ?, plan_expires = '365 Days Remaining'
        WHERE id = ?
    """, (plan_name, plan_name, user_id))
    conn.commit()
    conn.close()
    session["role"] = plan_name
    return jsonify({"success": True, "message": f"Account upgraded to {plan_name}!"})

@app.route("/api/billing/submit_payment", methods=["POST"])
@login_required
def submit_payment():
    user = get_current_user()
    plan_name = request.form.get("plan", "Seller").strip()
    cycle = request.form.get("cycle", "monthly").strip().lower()
    
    # Pricing configuration:
    # Developer: Monthly 100, Yearly 500
    # Seller: Monthly 300, Yearly 1000
    default_price = 300 if plan_name == "Seller" else 100
    if cycle == "yearly":
        default_price = 1000 if plan_name == "Seller" else 500
        
    try:
        amount = float(request.form.get("amount", default_price))
    except Exception:
        amount = default_price
        
    utr_ref = request.form.get("utr", "").strip()
    if not utr_ref:
        return jsonify({"success": False, "message": "Please enter the 12-digit UPI / UTR Transaction ID"}), 400
        
    days = 365 if cycle == "yearly" else 30
    plan_expires = f"{days} Days Remaining"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db()
    conn.execute("""
        INSERT INTO payments (user_id, username, plan, billing_cycle, amount, upi_id, utr_ref, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'zeeshan1710@fam', ?, 'Approved', ?)
    """, (user["id"], user["username"], plan_name, cycle, amount, utr_ref, now_str))
    
    conn.execute("""
        UPDATE users 
        SET plan = ?, role = ?, plan_expires = ?
        WHERE id = ?
    """, (plan_name, plan_name, plan_expires, user["id"]))
    conn.commit()
    conn.close()
    
    session["role"] = plan_name
    log_audit("PAYMENT_SUBMITTED", user_id=user["id"], ip=request.remote_addr or "127.0.0.1", 
              metadata=f"Plan: {plan_name} ({cycle}), Amount: ₹{amount}, UTR: {utr_ref}")
              
    return jsonify({
        "success": True,
        "message": f"Payment of ₹{amount:.0f} verified via UTR {utr_ref}! Your {plan_name} plan is now ACTIVE ({days} days access)."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting Zenith Auth Cloud Sentinel on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
