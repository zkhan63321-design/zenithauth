# Zenith Auth — API Architecture & Free Hosting Guide

This guide explains **how the Zenith Auth API operates**, **how clients & Discord bots consume it**, and **how to host it online 24/7 for free**.

---

## 1. Where Does the API Come From? ("API Kahan Se Lae?")

The API is **not from a third-party service** — your own Python Flask server (`app.py`) **IS** the API server!

### How the Architecture Works:
1. **The Server (`app.py`)** runs on your machine or cloud host and exposes two API gateways:
   - **Client Application REST API (`/api/v1`)**:
     - Used by your protected software, game loader, or C++/C#/Python client.
     - Endpoints: `/api/v1/init`, `/api/v1/login`, `/api/v1/var`, `/api/v1/heartbeat`.
   - **Seller & Automation API (`/api/seller`)**:
     - Used by Discord bots, Telegram bots, and automated shop payment gateways (Sellix/Shoppy).
     - Query format: `http://localhost:5000/api/seller?sellerkey=<YOUR_SELLER_KEY>&type=add&expiry=30&amount=1`

### Where do you get your keys?
- **App ID & Secret Key**: Generated automatically when you create an app inside the **Applications** tab in your Zenith Auth dashboard.
- **Private Seller Key**: Located in your dashboard under the **Seller API** tab. Only accounts with the **Seller** plan receive this key.

---

## 2. Free 24/7 Cloud Hosting ("Free Host Kahan Pe Kare?")

You can host Zenith Auth 100% free so that your software and Discord bot work worldwide 24/7 without keeping your PC on.

### Option A: Render.com (Recommended — 100% Free Web Service)
Render gives free HTTPS hosting for Python web apps.

1. **Push your code to GitHub**:
   - Create a free account at [github.com](https://github.com).
   - Create a new repository (e.g. `zenith-auth`) and push your `ZSAUTH` folder files.
2. **Deploy on Render**:
   - Go to [render.com](https://render.com) and create a free account.
   - Click **New +** &rarr; **Web Service**.
   - Connect your GitHub repository.
   - Set the settings:
     - **Runtime:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app` (or `python app.py`)
   - Click **Deploy Web Service**.
3. Render gives you a free live URL:
   - Example: `https://zenith-auth.onrender.com`
   - Your API is immediately live: `https://zenith-auth.onrender.com/api/v1/init` and `https://zenith-auth.onrender.com/api/seller`

---

### Option B: PythonAnywhere.com (Free Forever Python Hosting)
PythonAnywhere offers dedicated free Python Flask hosting with zero credit card needed.

1. Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com/).
2. Go to the **Files** tab and upload your `ZSAUTH` folder.
3. Go to the **Web** tab &rarr; **Add a new web app** &rarr; select **Flask** &rarr; **Python 3.11**.
4. Set the path to `app.py`.
5. Click **Reload**. Your site is instantly live at:
   - `https://yourusername.pythonanywhere.com`

---

### Option C: Instant Free Public Tunnel for Testing (Ngrok)
If you want to test from another computer, a friend's PC, or connect your Discord Bot without uploading code:

1. Download free ngrok from [ngrok.com](https://ngrok.com).
2. Start Zenith Auth server:
   ```powershell
   py app.py
   ```
3. Open a second terminal and run:
   ```powershell
   ngrok http 5000
   ```
4. Ngrok will give you a public HTTPS URL (e.g. `https://a1b2-c3d4.ngrok-free.app`).
   - Anyone in the world can now connect to your dashboard and APIs!

---

## 3. Connecting the Discord Bot

1. Create an application and bot token at [discord.com/developers/applications](https://discord.com/developers/applications).
2. Enable **Message Content Intent** in the Discord Developer Portal under Bot settings.
3. Open `discord_bot.py`:
   - Replace `ZENITH_API_URL` with your live server URL (e.g., `https://your-site.onrender.com/api/seller` or `http://localhost:5000/api/seller`).
   - Replace `SELLER_KEY` with your Private Seller Key from the dashboard.
   - Replace `BOT_TOKEN` with your Discord bot token.
4. Run the bot:
   ```powershell
   py discord_bot.py
   ```
5. In your Discord server, type:
   - `/generate days:30 level:1` &rarr; Instantly generates a key!
   - `/resethwid username:player1` &rarr; Clears HWID lock!
   - `/ban username:cheater reason:detected` &rarr; Suspends account!
   - `/stats` &rarr; Shows real-time client counts!
