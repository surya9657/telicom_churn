/* ============================================================
   model.js — Model Performance page logic. Reads evaluation metrics
   produced by ml/train.py (accuracy, precision, recall, F1, ROC-AUC,
   confusion matrix) via GET /api/model/metrics.
   ============================================================ */

(async function initModelPage() {
  const content = document.getElementById('page-content');
  content.appendChild(document.getElementById('model-template').content.cloneNode(true));

  try {
    const metrics = await Api.modelMetrics();
    const rf = metrics.random_forest;
    const lr = metrics.logistic_regression;

    document.getElementById('model-meta-line').textContent =
      `Evaluated on ${metrics.test_rows} held-out test rows (${metrics.training_rows} used for training) — ${metrics.features.length} input features.`;

    renderMetricsComparisonChart('chart-metrics-comparison', rf, lr);

    const cm = rf.confusion_matrix;
    document.getElementById('confusion-matrix-grid').innerHTML = `
      <div style="display:grid; grid-template-columns: auto 1fr 1fr; gap:1px; background:var(--border); border:1px solid var(--border); border-radius:var(--radius-sm); overflow:hidden; font-size:13px;">
        <div style="background:var(--surface-2); padding:10px;"></div>
        <div style="background:var(--surface-2); padding:10px; text-align:center; font-weight:600;">Predicted: Stay</div>
        <div style="background:var(--surface-2); padding:10px; text-align:center; font-weight:600;">Predicted: Churn</div>

        <div style="background:var(--surface-2); padding:10px; font-weight:600;">Actual: Stay</div>
        <div style="background:var(--surface); padding:16px; text-align:center;" class="mono">${cm.true_negative}</div>
        <div style="background:var(--risk-high-bg); padding:16px; text-align:center;" class="mono">${cm.false_positive}</div>

        <div style="background:var(--surface-2); padding:10px; font-weight:600;">Actual: Churn</div>
        <div style="background:var(--risk-high-bg); padding:16px; text-align:center;" class="mono">${cm.false_negative}</div>
        <div style="background:var(--surface); padding:16px; text-align:center;" class="mono">${cm.true_positive}</div>
      </div>
      <p class="text-muted" style="font-size:12.5px; margin-top:12px;">
        Because churn is imbalanced (far more retained customers than churned ones), accuracy alone is
        misleading — recall and F1 score better reflect how many actual churners the model catches.
      </p>
    `;

    const rows = [
      ['Accuracy', rf.accuracy, lr.accuracy],
      ['Precision', rf.precision, lr.precision],
      ['Recall', rf.recall, lr.recall],
      ['F1 Score', rf.f1_score, lr.f1_score],
      ['ROC-AUC', rf.roc_auc, lr.roc_auc],
    ];
    document.getElementById('metrics-tbody').innerHTML = rows
      .map(
        ([label, rfVal, lrVal]) => `
        <tr>
          <td>${label}</td>
          <td class="mono">${(rfVal * 100).toFixed(2)}%</td>
          <td class="mono">${(lrVal * 100).toFixed(2)}%</td>
        </tr>`
      )
      .join('');
  } catch (err) {
    document.getElementById('page-content').innerHTML =
      `<div class="empty-state"><div class="empty-icon">&#9888;</div>${err.message || 'Could not load model metrics.'}</div>`;
  }
})();
