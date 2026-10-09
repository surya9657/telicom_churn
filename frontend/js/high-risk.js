/* ============================================================
   high-risk.js — High-Risk Customers page logic.
   ============================================================ */

(async function initHighRiskPage() {
  const content = document.getElementById('page-content');
  content.appendChild(document.getElementById('high-risk-template').content.cloneNode(true));

  const tbody = document.getElementById('high-risk-tbody');
  const searchInput = document.getElementById('search-input');
  let allRows = [];

  async function load() {
    tbody.innerHTML = `<tr class="loading-row"><td colspan="7">Loading high-risk customers…</td></tr>`;
    try {
      allRows = await Api.getHighRiskCustomers({ limit: 200 });
      renderRows(allRows);
    } catch (err) {
      tbody.innerHTML = `<tr class="loading-row"><td colspan="7">${err.message}</td></tr>`;
    }
  }

  function renderRows(rows) {
    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-icon">&#9989;</div>No high-risk customers right now.</div></td></tr>`;
      return;
    }
    tbody.innerHTML = rows
      .map(
        (r) => `
        <tr>
          <td class="mono"><a href="customer-details.html?customer_id=${encodeURIComponent(r.customer_id)}">${r.customer_id}</a></td>
          <td>${r.tenure} mo</td>
          <td>${r.contract}</td>
          <td class="mono">${formatCurrency(r.monthly_charges)}</td>
          <td class="mono" style="color:var(--risk-high); font-weight:600;">${formatPercent(r.churn_probability)}</td>
          <td>${riskBadge(r.risk_level)}</td>
          <td class="text-muted">${formatDate(r.last_prediction_date)}</td>
        </tr>`
      )
      .join('');
  }

  searchInput.addEventListener(
    'input',
    debounce((e) => {
      const term = e.target.value.trim().toLowerCase();
      renderRows(term ? allRows.filter((r) => r.customer_id.toLowerCase().includes(term)) : allRows);
    }, 250)
  );

  load();
})();
