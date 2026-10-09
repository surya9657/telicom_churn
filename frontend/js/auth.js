/* ============================================================
   api.js — shared API client, auth helpers, toast/UI utilities
   Loaded on every authenticated page BEFORE the page-specific script.
   ============================================================ */

const API_BASE_URL = window.CHURN_API_BASE_URL || 'https://telicom-churn.onrender.com' ;
const TOKEN_KEY = 'churn_access_token';
const USERNAME_KEY = 'churn_username';

const Auth = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  setSession(token, username) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USERNAME_KEY, username);
  },
  getUsername() {
    return localStorage.getItem(USERNAME_KEY) || 'Admin';
  },
  clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USERNAME_KEY);
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  logout() {
    this.clearSession();
    window.location.href = 'login.html';
  },
  /** Call at the top of every protected page. */
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = 'login.html';
    }
  },
};

/**
 * Thin fetch wrapper that attaches the JWT, handles JSON, and redirects to
 * login on 401 so an expired/invalid token never leaves the admin stuck on
 * a broken page.
 */
async function apiRequest(path, { method = 'GET', body = null, isFormData = false } = {}) {
  const headers = {};
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isFormData && body) headers['Content-Type'] = 'application/json';

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      'Could not reach the server. Check that the FastAPI backend is running.',
      0,
      null
    );
  }

  if (response.status === 401) {
    Auth.clearSession();
    if (!window.location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
    throw new ApiError('Session expired. Please log in again.', 401, null);
  }

  let payload = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    payload = await response.json().catch(() => null);
  }

  if (!response.ok) {
    const detail =
      (payload && (payload.detail || payload.message)) ||
      `Request failed with status ${response.status}`;
    throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status, payload);
  }

  return payload;
}

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

const Api = {
  login: (username, password) => apiRequest('/api/auth/login', { method: 'POST', body: { username, password } }),
  me: () => apiRequest('/api/auth/me'),

  listCustomers: (params = {}) => apiRequest(`/api/customers${toQuery(params)}`),
  getCustomer: (customerId) => apiRequest(`/api/customers/${encodeURIComponent(customerId)}`),
  createCustomer: (data) => apiRequest('/api/customers', { method: 'POST', body: data }),
  deleteCustomer: (customerId) =>
    apiRequest(`/api/customers/${encodeURIComponent(customerId)}`, { method: 'DELETE' }),
  importCustomers: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiRequest('/api/customers/import', { method: 'POST', body: formData, isFormData: true });
  },

  predict: (data) => apiRequest('/api/predictions', { method: 'POST', body: data }),
  listPredictions: (params = {}) => apiRequest(`/api/predictions${toQuery(params)}`),
  getCustomerPredictionHistory: (customerId) =>
    apiRequest(`/api/predictions/customer/${encodeURIComponent(customerId)}`),
  getHighRiskCustomers: (params = {}) => apiRequest(`/api/predictions/high-risk${toQuery(params)}`),

  dashboardStats: () => apiRequest('/api/dashboard/stats'),
  churnDistribution: () => apiRequest('/api/dashboard/churn-distribution'),
  riskDistribution: () => apiRequest('/api/dashboard/risk-distribution'),
  trends: () => apiRequest('/api/dashboard/trends'),
  segmentation: () => apiRequest('/api/dashboard/segmentation'),

  modelMetrics: () => apiRequest('/api/model/metrics'),
};

function toQuery(params) {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  if (entries.length === 0) return '';
  const search = new URLSearchParams(entries);
  return `?${search.toString()}`;
}

/* ---------------- UI helpers ---------------- */

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function riskBadge(riskLevel) {
  const cls = { High: 'badge-high', Medium: 'badge-medium', Low: 'badge-low' }[riskLevel] || 'badge-neutral';
  return `<span class="badge ${cls}">${riskLevel}</span>`;
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatCurrency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function formatDate(isoString) {
  const d = new Date(isoString);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) +
    ' ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function riskColorVar(riskLevel) {
  return { High: 'var(--risk-high)', Medium: 'var(--risk-medium)', Low: 'var(--risk-low)' }[riskLevel] || 'var(--text-muted)';
}

function initTopbarUser() {
  const el = document.getElementById('current-username');
  if (el) el.textContent = Auth.getUsername();
  const avatar = document.getElementById('current-avatar');
  if (avatar) avatar.textContent = Auth.getUsername().slice(0, 2).toUpperCase();
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', () => Auth.logout());
}

function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
