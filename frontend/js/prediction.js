/* ============================================================
   prediction.js — Predict Churn page logic.
   ============================================================ */

(function initPredictionPage() {
  const content = document.getElementById('page-content');
  content.appendChild(document.getElementById('prediction-template').content.cloneNode(true));

  const formFields = document.getElementById('prediction-form-fields');
  buildCustomerFormFields(formFields);

  // Pre-fill a sensible default so the form isn't blank on first load.
  populateFormValues(formFields, {
    customer_id: '',
    gender: 'Female',
    senior_citizen: 0,
    partner: 'No',
    dependents: 'No',
    tenure: 12,
    phone_service: 'Yes',
    multiple_lines: 'No',
    internet_service: 'Fiber optic',
    online_security: 'No',
    online_backup: 'No',
    device_protection: 'No',
    tech_support: 'No',
    streaming_tv: 'No',
    streaming_movies: 'No',
    contract: 'Month-to-month',
    paperless_billing: 'Yes',
    payment_method: 'Electronic check',
    monthly_charges: 70.0,
    total_charges: 840.0,
  });

  // If arriving from a customer detail page, pre-load that customer.
  const params = new URLSearchParams(window.location.search);
  const prefillId = params.get('customer_id');
  if (prefillId) {
    document.getElementById('load-customer-id').value = prefillId;
    loadCustomer(prefillId);
  }

  document.getElementById('load-customer-btn').addEventListener('click', () => {
    const id = document.getElementById('load-customer-id').value.trim();
    if (id) loadCustomer(id);
  });

  async function loadCustomer(customerId) {
    try {
      const customer = await Api.getCustomer(customerId);
      populateFormValues(formFields, customer);
      showToast(`Loaded profile for ${customerId}`, 'success');
    } catch (err) {
      showToast(err.message || `Could not find customer ${customerId}`, 'error');
    }
  }

  document.getElementById('prediction-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    CUSTOMER_FIELDS.forEach((f) => {
      const errEl = document.getElementById(`${f.name}-error`);
      if (errEl) errEl.textContent = '';
    });

    const predictBtn = document.getElementById('predict-btn');
    predictBtn.disabled = true;
    predictBtn.textContent = 'Predicting…';

    try {
      const values = collectFormValues(formFields);
      const result = await Api.predict(values);
      renderResult(result);
      showToast('Prediction complete', 'success');
    } catch (err) {
      if (err.status === 422 && err.payload && err.payload.errors) {
        err.payload.errors.forEach((fieldErr) => {
          const field = fieldErr.loc[fieldErr.loc.length - 1];
          const errEl = document.getElementById(`${field}-error`);
          if (errEl) errEl.textContent = fieldErr.msg;
        });
        showToast('Please fix the highlighted fields', 'error');
      } else {
        showToast(err.message || 'Prediction failed', 'error');
      }
    } finally {
      predictBtn.disabled = false;
      predictBtn.textContent = 'Predict Churn';
    }
  });

  function renderResult(result) {
    document.getElementById('result-empty').style.display = 'none';
    const contentEl = document.getElementById('result-content');
    contentEl.style.display = 'block';

    const pct = formatPercent(result.churn_probability);
    const color = riskColorVar(result.risk_level);

    const probEl = document.getElementById('result-probability');
    probEl.textContent = pct;
    probEl.style.color = color;

    const fill = document.getElementById('result-progress-fill');
    fill.style.width = `${Math.round(result.churn_probability * 100)}%`;
    fill.style.background = color;

    document.getElementById('result-risk-badge').innerHTML = riskBadge(result.risk_level);
    document.getElementById('result-prediction-text').textContent =
      result.prediction === 1 ? 'Likely to churn' : 'Likely to stay';
    document.getElementById('result-model').textContent = result.model_used;
    document.getElementById('result-timestamp').textContent = formatDate(result.predicted_at);
    document.getElementById('view-customer-link').href =
      `customer-details.html?customer_id=${encodeURIComponent(result.customer_id)}`;
  }
})();
