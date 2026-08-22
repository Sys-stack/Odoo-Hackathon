/* Waypoint shared client helpers: auth, API calls, nav, formatting. */

const TOKEN_KEY = 'waypoint_token';
const USER_KEY = 'waypoint_user';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/** Redirect to /login if there's no token. Call at the top of every protected page. */
function requireAuth() {
  if (!getToken()) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

/** Fetch wrapper that attaches the Bearer token and handles 401s uniformly. */
async function apiFetch(url, options = {}) {
  const headers = Object.assign(
    { 'Content-Type': 'application/json' },
    options.headers || {},
    { Authorization: `Bearer ${getToken()}` }
  );

  const response = await fetch(url, Object.assign({}, options, { headers }));

  if (response.status === 401) {
    clearSession();
    window.location.href = '/login';
    throw new Error('Session expired.');
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.message || 'Something went wrong.');
  }

  return data;
}

/** Renders the shared top nav into #topnav. Call after requireAuth(). */
function renderNav(active) {
  const el = document.getElementById('topnav');
  if (!el) return;

  const user = getStoredUser();
  const firstName = user && user.full_name ? user.full_name.split(' ')[0] : 'there';
  const isAdmin = user && user.role === 'admin';

  el.innerHTML = `
    <a class="brand" href="/dashboard">Waypoint</a>
    <div class="links">
      <a href="/dashboard" class="${active === 'dashboard' ? 'active' : ''}">Dashboard</a>
      <a href="/trips" class="${active === 'trips' ? 'active' : ''}">My Trips</a>
      <a href="/cities" class="${active === 'cities' ? 'active' : ''}">Explore</a>
      <a href="/trips/new" class="${active === 'new' ? 'active' : ''}">Plan New Trip</a>
      ${isAdmin ? `<a href="/admin" class="${active === 'admin' ? 'active' : ''}">Admin</a>` : ''}
    </div>
    <div class="user">
      <a href="/profile" style="text-decoration:none; color:${active === 'profile' ? 'var(--paper)' : 'rgba(244,239,230,0.75)'};">Hi, ${escapeHtml(firstName)}</a>
      <button class="logout-btn" id="logoutBtn">Sign out</button>
    </div>
  `;

  document.getElementById('logoutBtn').addEventListener('click', () => {
    clearSession();
    window.location.href = '/login';
  });
}

/** Splits a list of trips (from GET /api/trips) into Ongoing / Upcoming / Completed, per today's date. */
function groupTrips(trips) {
  const today = todayISO();
  const groups = { ongoing: [], upcoming: [], completed: [] };
  trips.forEach(t => {
    if (t.start_date <= today && today <= t.end_date) groups.ongoing.push(t);
    else if (t.start_date > today) groups.upcoming.push(t);
    else groups.completed.push(t);
  });
  return groups;
}

const CATEGORY_COLORS = {
  transport: '#E8823C',
  stay: '#123B40',
  activity: '#3E7C5A',
  meals: '#C0562E',
  misc: '#8A8570',
};

function categoryColor(category) {
  return CATEGORY_COLORS[category] || '#8A8570';
}

/** Copies text to the clipboard, falling back silently if the API is unavailable. */
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str == null ? '' : String(str);
  return div.innerHTML;
}

function formatMoney(value) {
  const n = Number(value) || 0;
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

function formatDate(isoDate) {
  if (!isoDate) return '';
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateShort(isoDate) {
  if (!isoDate) return '';
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function formatDateRange(start, end) {
  return `${formatDateShort(start)} – ${formatDate(end)}`;
}

function dayCount(start, end) {
  const s = new Date(start + 'T00:00:00');
  const e = new Date(end + 'T00:00:00');
  return Math.max(1, Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1);
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
