/* ============================================================
   predictions.js — Prediction History page logic.
   ============================================================ */

(function initPredictionsPage() {
  const content = document.getElementById('page-content');
  content.appendChild(document.getElementById('predictions-template').content.cloneNode(true));

  const tbody = document.getElementById('predictions-tbody');
  const countLabel = document.getElementById('predictions-count-label');
  const pagination = document.getElementById('pagination');

  const state = { skip: 0, limit: 25, customer_id: '', risk_level: '', prediction_result: '' };

  async function load() {
    tbody.innerHTML = `<tr class="loading-row"><td colspan="6">Loading predictions…</td></tr>`;
    try {
      const result = await Api.listPredictions({
        customer_id: state.customer_id,
        risk_level: state.risk_level,
        prediction_result: state.prediction_result,
        skip: state.skip,
        limit: state.limit,
      });
      renderRows(result.items);
      renderPagination(result.total);
      countLabel.textContent = `${result.total} prediction${result.total === 1 ? '' : 's'} total`;
    } catch (err) {
      tbody.innerHTML = `<tr class="loading-row"><td colspan="6">${err.message}</td></tr>`;
    }
  }

  function renderRows(items) {
    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">&#128200;</div>No predictions match your filters.</div></td></tr>`;
      return;
    }
    tbody.innerHTML = items
      .map(
        (p) => `
        <tr>
          <td class="text-muted">${formatDate(p.created_at)}</td>
          <td class="mono"><a href="customer-details.html?customer_id=${encodeURIComponent(p.customer_id)}">${p.customer_id}</a></td>
          <td class="mono">${formatPercent(p.churn_probability)}</td>
          <td>${p.prediction === 1 ? 'Will churn' : 'Will stay'}</td>
          <td>${riskBadge(p.risk_level)}</td>
          <td class="text-muted">${p.model_name}</td>
        </tr>`
      )
      .join('');
  }

  function renderPagination(total) {
    const page = Math.floor(state.skip / state.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(total / state.limit));
    pagination.innerHTML = `
      <span>Page ${page} of ${totalPages}</span>
      <div class="flex gap-8">
        <button class="btn btn-secondary btn-sm" id="prev-page" ${state.skip === 0 ? 'disabled' : ''}>Previous</button>
        <button class="btn btn-secondary btn-sm" id="next-page" ${state.skip + state.limit >= total ? 'disabled' : ''}>Next</button>
      </div>`;
    document.getElementById('prev-page').addEventListener('click', () => {
      state.skip = Math.max(0, state.skip - state.limit);
      load();
    });
    document.getElementById('next-page').addEventListener('click', () => {
      state.skip += state.limit;
      load();
    });
  }

  document.getElementById('filter-customer-id').addEventListener(
    'input',
    debounce((e) => {
      state.customer_id = e.target.value;
      state.skip = 0;
      load();
    }, 350)
  );
  document.getElementById('filter-risk').addEventListener('change', (e) => {
    state.risk_level = e.target.value;
    state.skip = 0;
    load();
  });
  document.getElementById('filter-result').addEventListener('change', (e) => {
    state.prediction_result = e.target.value;
    state.skip = 0;
    load();
  });

  load();
})();
