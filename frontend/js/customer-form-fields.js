/* ============================================================
   customer-form-fields.js — single source of truth for the customer
   profile field schema, shared by the "Add Customer" modal and the
   "Predict Churn" form so both stay in sync with the backend Pydantic
   schema (app/schemas/customer.py).
   ============================================================ */

const CUSTOMER_FIELDS = [
  { name: 'customer_id', label: 'Customer ID', type: 'text', placeholder: 'e.g. CUST-1042', group: 'Identity' },
  { name: 'gender', label: 'Gender', type: 'select', options: ['Male', 'Female'], group: 'Identity' },
  { name: 'senior_citizen', label: 'Senior Citizen', type: 'select', options: [{ v: 0, l: 'No' }, { v: 1, l: 'Yes' }], group: 'Identity' },
  { name: 'partner', label: 'Has Partner', type: 'select', options: ['Yes', 'No'], group: 'Identity' },
  { name: 'dependents', label: 'Has Dependents', type: 'select', options: ['Yes', 'No'], group: 'Identity' },
  { name: 'tenure', label: 'Tenure (months)', type: 'number', min: 0, max: 100, group: 'Identity' },

  { name: 'phone_service', label: 'Phone Service', type: 'select', options: ['Yes', 'No'], group: 'Services' },
  { name: 'multiple_lines', label: 'Multiple Lines', type: 'select', options: ['Yes', 'No', 'No phone service'], group: 'Services' },
  { name: 'internet_service', label: 'Internet Service', type: 'select', options: ['DSL', 'Fiber optic', 'No'], group: 'Services' },
  { name: 'online_security', label: 'Online Security', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },
  { name: 'online_backup', label: 'Online Backup', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },
  { name: 'device_protection', label: 'Device Protection', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },
  { name: 'tech_support', label: 'Tech Support', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },
  { name: 'streaming_tv', label: 'Streaming TV', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },
  { name: 'streaming_movies', label: 'Streaming Movies', type: 'select', options: ['Yes', 'No', 'No internet service'], group: 'Services' },

  { name: 'contract', label: 'Contract', type: 'select', options: ['Month-to-month', 'One year', 'Two year'], group: 'Billing' },
  { name: 'paperless_billing', label: 'Paperless Billing', type: 'select', options: ['Yes', 'No'], group: 'Billing' },
  {
    name: 'payment_method', label: 'Payment Method', type: 'select',
    options: ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'], group: 'Billing',
  },
  { name: 'monthly_charges', label: 'Monthly Charges ($)', type: 'number', step: '0.01', min: 0, max: 1000, group: 'Billing' },
  { name: 'total_charges', label: 'Total Charges ($)', type: 'number', step: '0.01', min: 0, max: 100000, group: 'Billing' },
];

/**
 * Builds form field HTML into the given container. Returns nothing; reads
 * values back out later via collectFormValues().
 */
function buildCustomerFormFields(containerEl, { prefix = '' } = {}) {
  containerEl.innerHTML = CUSTOMER_FIELDS.map((f) => {
    const id = `${prefix}${f.name}`;
    let inputHtml;
    if (f.type === 'select') {
      const options = f.options
        .map((opt) => {
          const value = typeof opt === 'object' ? opt.v : opt;
          const label = typeof opt === 'object' ? opt.l : opt;
          return `<option value="${value}">${label}</option>`;
        })
        .join('');
      inputHtml = `<select id="${id}" name="${f.name}" required>${options}</select>`;
    } else {
      inputHtml = `<input type="${f.type}" id="${id}" name="${f.name}" ${f.step ? `step="${f.step}"` : ''} ${
        f.min !== undefined ? `min="${f.min}"` : ''
      } ${f.max !== undefined ? `max="${f.max}"` : ''} placeholder="${f.placeholder || ''}" required />`;
    }
    return `
      <div class="field">
        <label for="${id}">${f.label}</label>
        ${inputHtml}
        <div class="field-error" id="${id}-error"></div>
      </div>`;
  }).join('');

  // Keep multiple_lines consistent with phone_service, mirroring the
  // backend validator so the admin gets instant feedback.
  const phoneSelect = containerEl.querySelector(`#${prefix}phone_service`);
  const linesSelect = containerEl.querySelector(`#${prefix}multiple_lines`);
  if (phoneSelect && linesSelect) {
    phoneSelect.addEventListener('change', () => {
      if (phoneSelect.value === 'No') linesSelect.value = 'No phone service';
    });
  }
}

function collectFormValues(containerEl, prefix = '') {
  const values = {};
  CUSTOMER_FIELDS.forEach((f) => {
    const el = containerEl.querySelector(`#${prefix}${f.name}`);
    if (!el) return;
    values[f.name] = f.type === 'number' ? Number(el.value) : el.value;
  });
  return values;
}

function populateFormValues(containerEl, data, prefix = '') {
  CUSTOMER_FIELDS.forEach((f) => {
    const el = containerEl.querySelector(`#${prefix}${f.name}`);
    if (el && data[f.name] !== undefined) el.value = data[f.name];
  });
}
