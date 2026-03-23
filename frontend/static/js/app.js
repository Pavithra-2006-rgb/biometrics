// ─── Auth ──────────────────────────────────────────────────────────────────────
function checkAuth() {
    const user = sessionStorage.getItem('user');
    if (!user) { window.location.href = '/'; return; }
    const u = JSON.parse(user);
    const el = document.getElementById('userInfo');
    if (el) el.innerHTML = `<i class="fas fa-user-circle"></i> <strong>${u.name}</strong><br><small>${u.role.toUpperCase()}</small>`;
}

function logout() {
    sessionStorage.removeItem('user');
    window.location.href = '/';
}

// ─── API Helpers ───────────────────────────────────────────────────────────────
async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
    return res.json();
}

async function apiPost(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return res.json();
}

async function apiPut(url, body) {
    const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    return res.json();
}

async function apiDelete(url) {
    const res = await fetch(url, { method: 'DELETE' });
    return res.json();
}

// ─── Clock ────────────────────────────────────────────────────────────────────
function startClock() {
    const el = document.getElementById('clock');
    if (!el) return;
    function update() {
        const now = new Date();
        el.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            + ' | ' + now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    }
    update();
    setInterval(update, 1000);
}

// ─── Sidebar Toggle ───────────────────────────────────────────────────────────
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}
