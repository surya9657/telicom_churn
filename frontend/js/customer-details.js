/* ============================================================
   customer-details.js — loads a single customer's profile and full
   prediction history from the API.
   ============================================================ */

(async function initCustomerDetails() {
  const content = document.getElementById('page-content');
  content.appendChild(document.getElementById('detail-template').content.cloneNode(true));

  const params = new URLSearchParams(window.location.search);
  const customerId = params.get('customer_id');
  const detailBody = document.getElementById('detail-body');

  if (!customerId) {
    detailBody.innerHTML = `<div class="empty-state">No customer selected.</div>`;
    return;
  }

  try {
    const [customer, history] = await Promise.all([
      Api.getCustomer(customerId),
      Api.getCustomerPredictionHistory(customerId),
    ]);

    detailBody.innerHTML = '';
    detailBody.appendChild(document.getElementById('detail-content-template').content.cloneNode(true));

    document.getElementById('detail-customer-id').textContent = customer.customer_id;
    document.getElementById('detail-subtitle').textContent =
      `${customer.contract} · ${customer.internet_service} internet · ${formatCurrency(customer.monthly_charges)}/mo`;
    document.getElementById('predict-again-link').href = `prediction.html?customer_id=${encodeURIComponent(customer.customer_id)}`;
    document.getElementById('detail-tenure').textContent = `${customer.tenure} mo`;

    const latest = history[0];
    if (latest) {
      document.getElementById('detail-probability').textContent = formatPercent(latest.churn_probability);
      document.getElementById('detail-risk-badge').innerHTML = riskBadge(latest.risk_level);
      document.getElementById('detail-last-date').textContent = formatDate(latest.created_at);
    } else {
      document.getElementById('detail-probability').textContent = '—';
      document.getElementById('detail-risk-badge').innerHTML = '<span class="badge badge-neutral">No prediction yet</span>';
      document.getElementById('detail-last-date').textContent = '—';
    }

    document.getElementById('profile-fields').innerHTML = [
      ['Gender', customer.gender],
      ['Senior Citizen', customer.senior_citizen ? 'Yes' : 'No'],
      ['Partner', customer.partner],
      ['Dependents', customer.dependents],
      ['Phone Service', customer.phone_service],
      ['Multiple Lines', customer.multiple_lines],
      ['Internet Service', customer.internet_service],
      ['Online Security', customer.online_security],
      ['Tech Support', customer.tech_support],
      ['Paperless Billing', customer.paperless_billing],
      ['Payment Method', customer.payment_method],
      ['Total Charges', formatCurrency(customer.total_charges)],
    ]
      .map(
        ([label, value]) =>
          `<div class="flex-between"><span class="text-muted">${label}</span><span>${value}</span></div>`
      )
      .join('');

    if (history.length === 0) {
      document.getElementById('history-chart-wrap').innerHTML =
        `<div class="empty-state"><div class="empty-icon">&#128200;</div>No predictions yet for this customer.</div>`;
      document.getElementById('history-tbody').innerHTML =
        `<tr><td colspan="5"><div class="empty-state">No prediction history.</div></td></tr>`;
    } else {
      renderProbabilityHistoryChart('chart-probability-history', history);
      document.getElementById('history-tbody').innerHTML = history
        .map(
          (h) => `
          <tr>
            <td>${formatDate(h.created_at)}</td>
            <td class="mono">${formatPercent(h.churn_probability)}</td>
            <td>${h.prediction === 1 ? 'Will Churn' : 'Will Stay'}</td>
            <td>${riskBadge(h.risk_level)}</td>
            <td class="text-muted">${h.model_name}</td>
          </tr>`
        )
        .join('');
    }
  } catch (err) {
    detailBody.innerHTML = `<div class="empty-state">${err.message || 'Failed to load customer.'}</div>`;
  }
})();
