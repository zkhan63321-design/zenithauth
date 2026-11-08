# Best Free Hosting Guide — Zenith Auth (Custom Domain + 24/7 Discord Bot)

---

## 🌟 Sabse Best Free Hosting: **Render.com** (100% Free Forever)

### **Render.com Kyun Sabse Best Hai?**
1. **100% Free**: Zero credit card required to start.
2. **Sab Kuch Chalata Hai**:
   - Python 3.11 + Flask Web Server
   - REST API & Seller API
   - **24/7 Discord Bot** (humaare auto-start background thread ke sath ek hi container me!)
   - SQLite Database
3. **Khud Ka Custom Domain Support (Free SSL)**:
   - Aap apna koi bhi domain (e.g. `auth.yourdomain.com`, `zenithauth.com`, etc.) Render se **free me connect kar sakte hain**.
   - Render automatically **Free HTTPS/SSL Certificate** (Let's Encrypt) provide karta hai jo auto-renew hota hai!

---

## 🚀 Step-by-Step Setup Guide (5 Minutes)

### **STEP 1: Code Ko GitHub Par Upload Karein**
1. [GitHub.com](https://github.com/) par account banayein ya login karein.
2. **"New Repository"** par click karein:
   - Repository Name: `zenith-auth`
   - Privacy: **Private** (recommended)
   - Click **Create repository**.
3. Apne computer ke folder `c:\Users\USER\Downloads\ZSAUTH` ke saare files GitHub repository me upload kar dein (via GitHub Desktop ya Web drag & drop).

---

### **STEP 2: Render.com Par Free Deploy Karein**
1. [Render.com](https://render.com/) par jayein aur **"Sign Up"** (GitHub se login) karein.
2. Dashboard par **"New +"** button dabayein aur **"Web Service"** select karein.
3. Apni GitHub repository `zenith-auth` ko select karein aur connect karein.
4. Settings me yeh enter karein (humne `Procfile` aur `render.yaml` pehle se bana diya hai):
   - **Name**: `zenith-auth`
   - **Region**: Singapore ya Frankfurt (fastest for India)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: **Free**
5. **Environment Variables** (Optional, Discord Bot ke liye):
   - Click "Add Environment Variable":
     - Key: `DISCORD_BOT_TOKEN`
     - Value: Aapka Discord Bot Token
6. Click **"Deploy Web Service"**!
7. **2 minutes me aapka live public URL mil jayega**:
   `https://zenith-auth.onrender.com`

---

### **STEP 3: Khud Ka Custom Domain Kaise Connect Karein (Free SSL)**
1. Render ke dashboard me apni service (`zenith-auth`) par click karein.
2. Left menu me **"Settings"** par jayein aur scroll karke **"Custom Domains"** par click karein.
3. **"Add Custom Domain"** dabayein aur apna domain likhein:
   - Example: `auth.yourname.com` ya `yourdomain.com`
4. Render aapko ek **DNS CNAME Target** dikhayega:
   - Type: `CNAME`
   - Name: `auth` (ya subdomain)
   - Value: `zenith-auth.onrender.com`
5. Jahan se aapne domain liya hai (Cloudflare, GoDaddy, Namecheap, ya Hostinger):
   - DNS settings me jakar yeh CNAME record add kar dein.
6. **Bas!** Render automatically check karega aur **Free SSL (HTTPS 🔒)** activate kar dega.
   Aapki website ab aapke **khud ke domain** par chalegi!

---

### **STEP 4: Discord Bot Ko 24/7 Kaise Chalu Karein**

Aapke paas do 100% free tareeqe hain:

#### **Tareeqa A (Inbuilt in Render — Sabse Smart)**:
Humne `app.py` me Discord Bot background thread add kar diya hai:
- Render ke "Environment Variables" me `DISCORD_BOT_TOKEN` daal do.
- Jab Render par website start hogi, Discord Bot **background me automatically 24/7 start ho jayega**! Alag se koi server lene ki zaroorat nahi.

#### **Tareeqa B (Bot-Hosting.net — Dedicated Free Discord Bot Host)**:
1. Jao: [https://bot-hosting.net/](https://bot-hosting.net/)
2. Discord se login karo aur **Create Server** dabao (Python select karo).
3. `c:\Users\USER\Downloads\ZSAUTH\discord_bot.py` aur `requirements.txt` drag & drop upload karo.
4. Token daal kar start dabao — bot 24/7 active rahega!

---

## ⚡ Summary Cheat-Sheet

| Feature | Kahan Milta Hai | Cost |
|---|---|---|
| **Python Flask + Zenith Auth API** | Render.com Web Service | **₹0 (Free)** |
| **Khud Ka Domain + Free SSL** | Render.com Settings &rarr; Custom Domains | **₹0 (Free)** |
| **24/7 Discord Bot** | Render Background Thread / Bot-Hosting.net | **₹0 (Free)** |
| **Automated UPI QR (`zeeshan1710@fam`)** | Inbuilt in Zenith Auth | **₹0 (Free)** |
| **Seller API & Key Generator** | Inbuilt in Zenith Auth | **₹0 (Free)** |
