/* ============================================================
   layout.js — injects the shared sidebar + topbar shell so every
   authenticated page shares identical navigation markup.
   Usage: <div id="app-shell" data-active="dashboard" data-title="Dashboard"></div>
          <script src="js/layout.js"></script>
   ============================================================ */

const NAV_ITEMS = [
  { key: 'dashboard', href: 'dashboard.html', label: 'Dashboard', icon: '&#9632;' },
  { key: 'customers', href: 'customers.html', label: 'Customers', icon: '&#9782;' },
  { key: 'prediction', href: 'prediction.html', label: 'Predict Churn', icon: '&#9889;' },
  { key: 'high-risk', href: 'high-risk.html', label: 'High-Risk Customers', icon: '&#9888;' },
  { key: 'predictions', href: 'predictions.html', label: 'Prediction History', icon: '&#8987;' },
  { key: 'model', href: 'model.html', label: 'Model Performance', icon: '&#9673;' },
];

function renderAppShell() {
  const mount = document.getElementById('app-shell');
  if (!mount) return;
  const active = mount.dataset.active || '';
  const title = mount.dataset.title || '';
  const eyebrow = mount.dataset.eyebrow || 'Signal / Admin';

  const navHtml = NAV_ITEMS.map(
    (item) => `
      <a class="nav-link ${item.key === active ? 'active' : ''}" href="${item.href}">
        <span class="nav-icon">${item.icon}</span>${item.label}
      </a>`
  ).join('');

  mount.outerHTML = `
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-brand">
          <div class="signal-mark"><span></span><span></span><span></span><span></span></div>
          <div>
            <div class="brand-name">Signal</div>
            <div class="brand-sub">Churn Analytics</div>
          </div>
        </div>
        <nav class="sidebar-nav">${navHtml}</nav>
        <div class="sidebar-footer">
          <a class="nav-link" href="#" id="logout-btn">
            <span class="nav-icon">&#8594;</span>Logout
          </a>
        </div>
      </aside>

      <div class="main-area">
        <header class="topbar">
          <div class="topbar-title">
            <span class="eyebrow">${eyebrow}</span>
            ${title}
          </div>
          <div class="topbar-user">
            <span id="current-username"></span>
            <div class="avatar" id="current-avatar"></div>
          </div>
        </header>
        <main class="page-content" id="page-content"></main>
      </div>
    </div>
  `;

  initTopbarUser();
}

Auth.requireAuth();
renderAppShell();
