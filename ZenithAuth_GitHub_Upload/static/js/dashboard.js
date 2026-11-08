// c:\Users\USER\Downloads\ZSAUTH\static\js\dashboard.js

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.dataset.tab === tabId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  document.querySelectorAll('.tab-content-panel').forEach(panel => {
    panel.classList.add('hidden');
  });

  const target = document.getElementById(`panel-${tabId}`);
  if (target) {
    target.classList.remove('hidden');
  }
  window.location.hash = tabId;
}

// Active Application Switcher
async function setActiveApp(appId, appName) {
  try {
    const res = await fetch(`/api/app/set_active/${appId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Switched to ${appName || 'Application'}`);
      window.location.href = '/dashboard';
    }
  } catch (err) {
    console.error(err);
  }
}

// Create App
async function handleCreateApp(e) {
  e.preventDefault();
  const form = document.getElementById('create-app-form');
  const formData = new FormData(form);

  try {
    const res = await fetch('/api/app/create', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      showToast(`Created application ${data.name}!`);
      closeModal('modal-create-app');
      // Direct navigation to overview of the newly created application with zero lag
      window.location.href = '/dashboard';
    } else {
      alert(data.error || data.message || "Failed to create application");
    }
  } catch (err) {
    alert("Connection error");
  }
}

// Save App Settings (Screenshot 2)
async function handleSaveAppSettings(appId) {
  if (!appId) {
    const selInput = document.getElementById('seller-whitelist-ip-input');
    appId = selInput ? selInput.dataset.appId || 0 : 0;
  }
  if (!appId) {
    alert("Please create or select an application first.");
    return;
  }
  const formData = new FormData();

  formData.append('version', document.getElementById('setting-version').value.trim());
  formData.append('download_url', document.getElementById('setting-download-url').value.trim());
  formData.append('webhook_url', document.getElementById('setting-webhook-url').value.trim());
  formData.append('status', document.getElementById('setting-app-status').checked ? 'Active' : 'Paused');
  formData.append('hwid_lock', document.getElementById('setting-hwid-lock').checked ? '1' : '0');
  formData.append('force_hwid', document.getElementById('setting-force-hwid').checked ? '1' : '0');
  formData.append('block_vpn', document.getElementById('setting-block-vpn').checked ? '1' : '0');
  formData.append('hash_check', document.getElementById('setting-hash-check').checked ? '1' : '0');
  formData.append('log_ip', document.getElementById('setting-log-ip').checked ? '1' : '0');

  try {
    const res = await fetch(`/api/app/save_settings/${appId}`, { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      showToast("Settings saved successfully!");
    } else {
      alert(data.error || "Save error");
    }
  } catch (err) {
    alert("Save error");
  }
}

// Delete App
async function handleDeleteApp(appId, name) {
  if (!confirm(`Permanently delete application "${name}"?`)) return;
  try {
    const res = await fetch(`/api/app/delete/${appId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast("Application deleted.");
      window.location.href = '/dashboard';
    }
  } catch (err) {
    console.error(err);
  }
}

// Generate License
async function handleGenerateLicense(e) {
  e.preventDefault();
  const form = document.getElementById('generate-license-form');
  const formData = new FormData(form);

  try {
    const res = await fetch('/api/license/generate', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.success) {
      showToast(`Generated ${data.count} keys!`);
      closeModal('modal-generate-license');
      setTimeout(() => window.location.reload(), 500);
    } else {
      alert(data.error || "Generation error");
    }
  } catch (err) {
    alert("Network error");
  }
}

// Reset HWID
async function handleResetHWID(userId, username) {
  if (!confirm(`Reset HWID for client ${username}?`)) return;
  try {
    const res = await fetch(`/api/user/reset_hwid/${userId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(`HWID cleared for ${username}`);
      const c = document.getElementById(`user-hwid-${userId}`);
      if (c) c.textContent = "None (Unlocked)";
    }
  } catch (err) {
    console.error(err);
  }
}

// Toggle Ban
async function handleToggleBan(userId, username) {
  try {
    const res = await fetch(`/api/user/toggle_ban/${userId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.is_banned ? `User ${username} BANNED` : `User ${username} UNBANNED`);
      setTimeout(() => window.location.reload(), 400);
    }
  } catch (err) {
    console.error(err);
  }
}

// Kill Session
async function handleKillSession(sessId) {
  try {
    const res = await fetch(`/api/session/kill/${sessId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast("Session terminated.");
      setTimeout(() => window.location.reload(), 400);
    }
  } catch (err) {
    console.error(err);
  }
}

// Owner Edit Developer Plan Modal Helpers
function openEditUserModal(id, username, plan, expiry, balance, status) {
  document.getElementById('edit-user-id').value = id;
  document.getElementById('edit-user-name').value = username;
  document.getElementById('edit-user-plan').value = plan;
  
  const expirySelect = document.getElementById('edit-user-expiry');
  if (['Lifetime Access', '365 Days', '90 Days', '30 Days', '7 Days', '1 Day'].includes(expiry)) {
    expirySelect.value = expiry;
    document.getElementById('custom-expiry-wrap').classList.add('hidden');
  } else {
    expirySelect.value = 'Custom';
    document.getElementById('custom-expiry-wrap').classList.remove('hidden');
    document.getElementById('edit-custom-date').value = expiry || '';
  }
  
  document.getElementById('edit-user-balance').value = balance !== undefined ? balance : 0;
  document.getElementById('edit-user-status').value = status || 'ONLINE';
  
  openModal('modal-edit-user-plan');
}

function toggleCustomExpiry(val) {
  const wrap = document.getElementById('custom-expiry-wrap');
  if (val === 'Custom') {
    wrap.classList.remove('hidden');
  } else {
    wrap.classList.add('hidden');
  }
}

async function handleSaveUserPlan(e) {
  e.preventDefault();
  const form = document.getElementById('owner-edit-user-form');
  const fd = new FormData(form);

  try {
    const res = await fetch('/api/owner/change_plan', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      closeModal('modal-edit-user-plan');
      setTimeout(() => window.location.reload(), 600);
    } else {
      alert(data.message || 'Failed to update user plan');
    }
  } catch (err) {
    alert('Connection error');
  }
}

// Quick Owner Change Plan
async function handleOwnerChangePlan(userId, newPlan) {
  const fd = new FormData();
  fd.append('user_id', userId);
  fd.append('plan', newPlan);

  try {
    const res = await fetch('/api/owner/change_plan', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      setTimeout(() => window.location.reload(), 600);
    }
  } catch (err) {
    alert("Failed to update user plan");
  }
}

// Whitelist Seller IP
async function handleWhitelistSellerIP(appId) {
  const ip = document.getElementById('seller-whitelist-ip-input').value.trim() || '*';
  const fd = new FormData();
  fd.append('app_id', appId);
  fd.append('ip', ip);

  try {
    const res = await fetch('/api/seller/whitelist_ip', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast(`Seller IP filter set to: ${data.whitelist}`);
    }
  } catch (err) {
    console.error(err);
  }
}

// Regenerate Seller Key
async function handleRegenerateSellerKey(appId) {
  if (!confirm("Regenerate private Seller Key? Any existing bot connection using the old key will stop working.")) return;
  const fd = new FormData();
  fd.append('app_id', appId);

  try {
    const res = await fetch('/api/seller/regenerate_key', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast("New Seller Key generated!");
      document.getElementById('seller-key-input').value = data.new_seller_key;
      updateBuilderUrl();
    }
  } catch (err) {
    console.error(err);
  }
}

// ==============================================================
//             INTERACTIVE SELLER API REQUEST BUILDER
// ==============================================================
let builderMaskFormat = "Standard (6x5)";
let builderSnippetMode = "url";

function setBuilderDays(days) {
  document.getElementById('builder-days-input').value = days;
  document.getElementById('builder-expiry-badge').textContent = `${days} days`;
  updateBuilderUrl();
}

function setBuilderMask(format) {
  builderMaskFormat = format;
  if (format.includes("4x3")) {
    document.getElementById('builder-mask-input').value = "XXXX-XXXX-XXXX";
  } else if (format.includes("Zenith")) {
    document.getElementById('builder-mask-input').value = "ZENITH-XXXX-XXXX-XXXX";
  } else {
    document.getElementById('builder-mask-input').value = "XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX";
  }
  updateBuilderUrl();
}

function setBuilderSnippetMode(mode) {
  builderSnippetMode = mode;
  updateBuilderUrl();
}

function updateBuilderUrl() {
  const action = document.getElementById('builder-action-type') ? document.getElementById('builder-action-type').value : 'add';
  const days = document.getElementById('builder-days-input') ? document.getElementById('builder-days-input').value : 30;
  const sellerKeyEl = document.getElementById('seller-key-input');
  const sellerKey = sellerKeyEl ? sellerKeyEl.value : '799b1605a63e8131b94f1d50590e3d18';
  const mask = document.getElementById('builder-mask-input') ? document.getElementById('builder-mask-input').value : 'XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX';
  const host = window.location.origin;

  let url = `${host}/api/seller?sellerkey=${sellerKey}&type=${action}`;
  if (action === 'add') {
    url += `&amount=1&expiry=${days}&mask=${mask}&level=1`;
  } else if (action === 'resethwid') {
    url += `&user=aurora_user_1`;
  } else if (action === 'ban') {
    url += `&user=aurora_user_1&reason=Cheating`;
  } else if (action === 'extend') {
    url += `&user=aurora_user_1&days=${days}`;
  } else if (action === 'del') {
    url += `&key=ZENITH-SAMPLE-KEY`;
  }

  const displayEl = document.getElementById('builder-url-display');
  if (!displayEl) return;

  if (builderSnippetMode === 'curl') {
    displayEl.textContent = `curl -X GET "${url}"`;
  } else if (builderSnippetMode === 'python') {
    displayEl.textContent = `import requests\nresponse = requests.get("${url}").json()\nprint(response)`;
  } else {
    displayEl.textContent = url;
  }
}

async function executeSellerLiveRequest() {
  const action = document.getElementById('builder-action-type').value;
  const days = document.getElementById('builder-days-input').value;
  const sellerKey = document.getElementById('seller-key-input').value;
  const mask = document.getElementById('builder-mask-input').value;
  const outputEl = document.getElementById('builder-live-output');

  outputEl.textContent = `[*] Calling Seller API endpoint ...\n`;

  let url = `/api/seller?sellerkey=${sellerKey}&type=${action}`;
  if (action === 'add') {
    url += `&amount=1&expiry=${days}&mask=${mask}&level=1`;
  } else if (action === 'resethwid') {
    url += `&user=aurora_user_1`;
  } else if (action === 'ban') {
    url += `&user=aurora_user_1&reason=Moderation`;
  } else if (action === 'extend') {
    url += `&user=aurora_user_1&days=${days}`;
  } else if (action === 'del') {
    url += `&key=SAMPLE_KEY`;
  }

  try {
    const res = await fetch(url);
    const json = await res.json();
    outputEl.textContent = `HTTP ${res.status} Response:\n` + JSON.stringify(json, null, 2);
    showToast(`Seller API: ${json.status.toUpperCase()}`);
  } catch (err) {
    outputEl.textContent = `[!] Error: ${err.message}`;
  }
}

// ==============================================================
//           DASHBOARD UPI PAYMENT & BILLING LOGIC
// ==============================================================
let dashboardBillingCycle = 'monthly';
const dashboardPrices = {
  Developer: { monthly: 100, yearly: 500 },
  Seller: { monthly: 300, yearly: 1000 }
};

function setDashboardCycle(cycle) {
  dashboardBillingCycle = cycle;
  const btnMonthly = document.getElementById('dash-toggle-monthly');
  const btnYearly = document.getElementById('dash-toggle-yearly');
  if (btnMonthly) btnMonthly.classList.toggle('active', cycle === 'monthly');
  if (btnYearly) btnYearly.classList.toggle('active', cycle === 'yearly');

  if (cycle === 'yearly') {
    document.getElementById('dash-price-dev').textContent = '₹500';
    document.getElementById('dash-cycle-dev').textContent = '/year';
    document.getElementById('dash-btn-price-dev').textContent = '₹500/yr';
    document.getElementById('dash-badge-dev').classList.remove('hidden');

    document.getElementById('dash-price-seller').textContent = '₹1,000';
    document.getElementById('dash-cycle-seller').textContent = '/year';
    document.getElementById('dash-btn-price-seller').textContent = '₹1,000/yr';
    document.getElementById('dash-badge-seller').classList.remove('hidden');
  } else {
    document.getElementById('dash-price-dev').textContent = '₹100';
    document.getElementById('dash-cycle-dev').textContent = '/mo';
    document.getElementById('dash-btn-price-dev').textContent = '₹100';
    document.getElementById('dash-badge-dev').classList.add('hidden');

    document.getElementById('dash-price-seller').textContent = '₹300';
    document.getElementById('dash-cycle-seller').textContent = '/mo';
    document.getElementById('dash-btn-price-seller').textContent = '₹300';
    document.getElementById('dash-badge-seller').classList.add('hidden');
  }
}

let activeDashModalPlan = 'Seller';
function openDashboardUpiModal(planName) {
  activeDashModalPlan = planName;
  const price = dashboardPrices[planName][dashboardBillingCycle];

  const titleEl = document.getElementById('dash-modal-plan-title');
  const amountEl = document.getElementById('dash-modal-amount-display');
  if (titleEl) titleEl.textContent = `${planName} Plan (${dashboardBillingCycle.toUpperCase()})`;
  if (amountEl) amountEl.textContent = `₹${price}`;

  // Generate dynamic QR Code for zeeshan1710@fam
  const upiString = `upi://pay?pa=zeeshan1710@fam&pn=Zenith%20Auth&am=${price}&cu=INR&tn=${planName}_${dashboardBillingCycle}`;
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(upiString)}&color=050609&bgcolor=ffffff`;
  const imgEl = document.getElementById('dash-upi-qr-image');
  if (imgEl) imgEl.src = qrUrl;

  openModal('modal-upi-payment');
}

async function handleDashboardUpiSubmit(e) {
  e.preventDefault();
  const utrInput = document.getElementById('dash-upi-utr-input');
  const utr = utrInput ? utrInput.value.trim() : '';
  const price = dashboardPrices[activeDashModalPlan][dashboardBillingCycle];

  const fd = new FormData();
  fd.append('plan', activeDashModalPlan);
  fd.append('cycle', dashboardBillingCycle);
  fd.append('amount', price);
  fd.append('utr', utr);

  try {
    const res = await fetch('/api/billing/submit_payment', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast(data.message);
      closeModal('modal-upi-payment');
      setTimeout(() => window.location.reload(), 1200);
    } else {
      alert(data.message || 'Verification error');
    }
  } catch (err) {
    alert('Payment verification connection error');
  }
}

// Modal Helpers
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}

// Init & Hotkeys
document.addEventListener('DOMContentLoaded', () => {
  const initial = window.location.hash.replace('#', '') || 'overview';
  switchTab(initial);
  updateBuilderUrl();

  // Ctrl+S to save app config
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSaveAppSettings();
    }
  });
});
