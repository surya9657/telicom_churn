/* ============================================================
   customers.js — customer management page logic.
   ============================================================ */

(function initCustomersPage() {
  const content = document.getElementById('page-content');
  const template = document.getElementById('customers-template');
  content.appendChild(template.content.cloneNode(true));

  const tbody = document.getElementById('customers-tbody');
  const countLabel = document.getElementById('customer-count-label');
  const pagination = document.getElementById('pagination');
  const searchInput = document.getElementById('search-input');
  const filterContract = document.getElementById('filter-contract');
  const filterInternet = document.getElementById('filter-internet');

  const state = { skip: 0, limit: 20, search: '', contract: '', internet_service: '' };
  let pendingDeleteId = null;

  async function loadCustomers() {
    tbody.innerHTML = `<tr class="loading-row"><td colspan="8">Loading customers…</td></tr>`;
    try {
      const result = await Api.listCustomers({
        search: state.search,
        contract: state.contract,
        internet_service: state.internet_service,
        skip: state.skip,
        limit: state.limit,
      });
      renderRows(result.items);
      renderPagination(result.total);
      countLabel.textContent = `${result.total} customer${result.total === 1 ? '' : 's'} total`;
    } catch (err) {
      tbody.innerHTML = `<tr class="loading-row"><td colspan="8">${err.message}</td></tr>`;
    }
  }

  function renderRows(items) {
    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">&#128100;</div>No customers match your filters.</div></td></tr>`;
      return;
    }
    tbody.innerHTML = items
      .map(
        (c) => `
        <tr>
          <td class="mono"><a href="customer-details.html?customer_id=${encodeURIComponent(c.customer_id)}">${c.customer_id}</a></td>
          <td>${c.gender}</td>
          <td>${c.tenure} mo</td>
          <td>${c.contract}</td>
          <td>${c.internet_service}</td>
          <td class="mono">${formatCurrency(c.monthly_charges)}</td>
          <td class="text-muted">${formatDate(c.created_at)}</td>
          <td>
            <button class="btn btn-secondary btn-sm delete-btn" data-id="${c.customer_id}">Delete</button>
          </td>
        </tr>`
      )
      .join('');

    tbody.querySelectorAll('.delete-btn').forEach((btn) =>
      btn.addEventListener('click', () => openDeleteModal(btn.dataset.id))
    );
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
      loadCustomers();
    });
    document.getElementById('next-page').addEventListener('click', () => {
      state.skip += state.limit;
      loadCustomers();
    });
  }

  searchInput.addEventListener(
    'input',
    debounce((e) => {
      state.search = e.target.value;
      state.skip = 0;
      loadCustomers();
    }, 350)
  );
  filterContract.addEventListener('change', (e) => {
    state.contract = e.target.value;
    state.skip = 0;
    loadCustomers();
  });
  filterInternet.addEventListener('change', (e) => {
    state.internet_service = e.target.value;
    state.skip = 0;
    loadCustomers();
  });

  /* ---------------- Add customer modal ---------------- */

  const addModal = document.getElementById('add-modal');
  const formFieldsContainer = document.getElementById('customer-form-fields');
  buildCustomerFormFields(formFieldsContainer);

  document.getElementById('add-customer-btn').addEventListener('click', () => addModal.classList.add('open'));
  document.getElementById('cancel-add-btn').addEventListener('click', () => addModal.classList.remove('open'));

  document.getElementById('add-customer-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const saveBtn = document.getElementById('save-customer-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';

    // clear previous field errors
    CUSTOMER_FIELDS.forEach((f) => {
      const errEl = document.getElementById(`${f.name}-error`);
      if (errEl) errEl.textContent = '';
    });

    try {
      const values = collectFormValues(formFieldsContainer);
      await Api.createCustomer(values);
      showToast(`Customer ${values.customer_id} created`, 'success');
      addModal.classList.remove('open');
      e.target.reset();
      state.skip = 0;
      loadCustomers();
    } catch (err) {
      if (err.status === 422 && err.payload && err.payload.errors) {
        err.payload.errors.forEach((fieldErr) => {
          const field = fieldErr.loc[fieldErr.loc.length - 1];
          const errEl = document.getElementById(`${field}-error`);
          if (errEl) errEl.textContent = fieldErr.msg;
        });
        showToast('Please fix the highlighted fields', 'error');
      } else {
        showToast(err.message || 'Failed to save customer', 'error');
      }
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save Customer';
    }
  });

  /* ---------------- Delete modal ---------------- */

  const deleteModal = document.getElementById('delete-modal');
  function openDeleteModal(customerId) {
    pendingDeleteId = customerId;
    document.getElementById('delete-modal-text').textContent =
      `This will permanently remove customer ${customerId} and their prediction history.`;
    deleteModal.classList.add('open');
  }
  document.getElementById('cancel-delete-btn').addEventListener('click', () => deleteModal.classList.remove('open'));
  document.getElementById('confirm-delete-btn').addEventListener('click', async () => {
    try {
      await Api.deleteCustomer(pendingDeleteId);
      showToast(`Customer ${pendingDeleteId} deleted`, 'success');
      deleteModal.classList.remove('open');
      loadCustomers();
    } catch (err) {
      showToast(err.message || 'Failed to delete customer', 'error');
    }
  });

  /* ---------------- CSV import ---------------- */

  const importModal = document.getElementById('import-modal');
  document.getElementById('import-file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const summary = await Api.importCustomers(file);
      document.getElementById('import-summary-body').innerHTML = `
        <div class="stat-grid" style="grid-template-columns: repeat(2,1fr); margin-bottom:16px;">
          <div class="stat-card"><div class="stat-label">Total Records</div><div class="stat-value">${summary.total_records}</div></div>
          <div class="stat-card"><div class="stat-label">Imported</div><div class="stat-value low">${summary.imported}</div></div>
          <div class="stat-card"><div class="stat-label">Failed</div><div class="stat-value high">${summary.failed}</div></div>
          <div class="stat-card"><div class="stat-label">Duplicates</div><div class="stat-value medium">${summary.duplicates}</div></div>
        </div>
        ${
          summary.errors.length
            ? `<div class="text-muted" style="max-height:160px; overflow-y:auto; font-size:12.5px;">${summary.errors
                .map((e) => `<div style="padding:4px 0; border-bottom:1px solid var(--border);">${e}</div>`)
                .join('')}</div>`
            : ''
        }
      `;
      importModal.classList.add('open');
      loadCustomers();
    } catch (err) {
      showToast(err.message || 'CSV import failed', 'error');
    } finally {
      e.target.value = '';
    }
  });
  document.getElementById('close-import-btn').addEventListener('click', () => importModal.classList.remove('open'));

  loadCustomers();
})();
