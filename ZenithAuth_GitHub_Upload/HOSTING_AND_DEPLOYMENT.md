# Zenith Auth — Hosting, UPI Payment & Discord Bot Setup Guide

---

## 1. Kyun Aisa Aa Raha Tha? (Unstyled Look Fix)

Aapki **Image 1** me website unstyled isliye dikhi kyunki:
1. Aapne `templates/index.html` ko file manager se double-click karke direct browser me khola tha (`file:///...`), ya fir external Tailwind CDN block hua tha.
2. **Kese Kholna Hai**:
   - `run.bat` par double-click karo (yeh server start karke browser me `http://localhost:5000` open karega).
   - Humne **`static/css/style.css`** me standalone offline fallback CSS daal diya hai. Ab chahe internet ho ya na ho, design hamesha 100% dark glowing cyber neon theme me hi dikhega!

---

## 2. Dynamic UPI QR Code & Plan Activation (zeeshan1710@fam)

Aapki payment request aur pricing set kar di gayi hai:

### **Pricing Updated**:
- **Tester Plan**: Free (2 Apps, 15 Licenses, 15 Users per app)
- **Developer Plan**:
  - Monthly: **₹100 / month**
  - Yearly: **₹500 / year** *(Save 58%)*
- **Seller Plan** (Featured):
  - Monthly: **₹300 / month**
  - Yearly: **₹1,000 / year** *(Save 72%)*

### **Auto UPI QR Generation**:
- Jab bhi koi user **Choose Developer** ya **Activate Seller** par click karega:
  1. Live **UPI QR Code** automatically generate hoga:
     `upi://pay?pa=zeeshan1710@fam&pn=Zenith%20Auth&am={price}&cu=INR&tn={plan}_{cycle}`
  2. GPay, PhonePe, Paytm, BHIM, Cred se scan karke direct **`zeeshan1710@fam`** par payment jayegi.
  3. Buyer apna 12-digit **UTR / Transaction ID** enter karega aur **"Verify Payment & Activate Plan"** click karega.
  4. Backend automatically account ko **Seller / Developer** me upgrade kar dega aur Private Seller Key unlock kar dega!
  5. Owner Account (`Zeeshan_cf5fq`) apne **Owner Admin Hub** me saari payments aur UTR numbers live dekh sakta hai!

---

## 3. "API Kahan Se Lau?" (Where to get the API)

**Zenith Auth ke andar hi aapki API banti hai!** Bahar kisi third-party se API khareedne ki zaroorat nahi hai:
1. **Application Secret Key**:
   - Jab aap Zenith Auth dashboard me **+ Create Application** karte hain, system automatically **Application Secret** banata hai.
   - Yeh aapke game/software loader binary ke liye API hai (`/api/v1/init`, `/api/v1/login`, `/api/v1/validate`).
2. **Private Seller Key**:
   - Application create hote hi aapko **Seller Key** milti hai.
   - Yeh aapke Discord Bot, Telegram Bot ya payment gateway ke liye automatic key generate karne ki API hai (`/api/seller?sellerkey=...&type=add`).
3. **Discord Bot Token (Free)**:
   - Discord Bot Token bilkul free me Discord se milta hai:
     1. [Discord Developer Portal](https://discord.com/developers/applications) par login karo.
     2. **New Application** dabao -> Name do `Zenith Bot`.
     3. Left side me **Bot** par click karo -> **Reset Token** dabao aur token **Copy** kar lo.
     4. `discord_bot.py` file me `BOT_TOKEN = "paste_your_token_here"` daal do!

---

## 4. InfinityFree Hosting (`zenithauth.kesug.com` - Image 2)

Aapki **Image 2** me InfinityFree ka dashboard dikh raha hai:
- Domain: **`zenithauth.kesug.com`**
- Directory: **`htdocs`**
- InfinityFree ek **PHP & MySQL shared web hosting** hai.

### **InfinityFree par Website Live Kaise Karein (2 Minutes)**:
1. Humne aapke project me **`infinityfree_htdocs`** folder bana diya hai jisme `index.php` ready hai!
2. InfinityFree dashboard me **"File Manager"** button dabao.
3. **`htdocs`** folder open karo.
4. `c:\Users\USER\Downloads\ZSAUTH\infinityfree_htdocs\index.php` ko `htdocs` me upload kar do.
5. Ab aapka domain **`zenithauth.kesug.com`** live ho jayega aur uspar aapka Zenith Auth portal aur UPI QR generator chalne lagega!

---

## 5. Discord Bot Ko 24/7 Free Kaise Host Karein?

> [!NOTE]
> InfinityFree sirf PHP websites host karta hai, continuous background Python processes (jaise Discord Bot) ko block karta hai. Discord bot ko 24/7 chalane ke liye niche diye gaye **100% Free 24/7 Hosts** use karein:

### **Option 1: Bot-Hosting.net (Sabse Aasan & 100% Free 24/7)**
1. Website open karo: [https://bot-hosting.net/](https://bot-hosting.net/)
2. Discord se login karo aur **Create Server** dabao (Python select karo).
3. `c:\Users\USER\Downloads\ZSAUTH\discord_bot.py` aur `requirements.txt` drag & drop upload karo.
4. Start button dabao — aapka bot **24/7 online** ho jayega!

### **Option 2: Discloud (Free Discord Bot Cloud)**
1. Website: [https://discloud.app/](https://discloud.app/)
2. Discord se login karo aur `discloud.config` ke saath `discord_bot.py` upload karo.
3. 24/7 uptime guaranteed.

### **Option 3: Render.com (Free Web Service for Python API & Bot)**
1. Website: [https://render.com/](https://render.com/)
2. "New Web Service" dabao aur repository connect karo.
3. Start Command: `gunicorn app:app` ya `python app.py`.
4. Free public URL mil jayega jo 24/7 live rahega.
