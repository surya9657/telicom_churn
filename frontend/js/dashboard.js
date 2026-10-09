/* ============================================================
   dashboard.js — populates the dashboard page from FastAPI endpoints.
   All numbers come from /api/dashboard/* — nothing is hardcoded.
   ============================================================ */

(async function initDashboard() {
  const content = document.getElementById('page-content');
  const template = document.getElementById('dashboard-template');
  content.appendChild(template.content.cloneNode(true));

  try {
    const [stats, churnDist, riskDist, trend, segmentation] = await Promise.all([
      Api.dashboardStats(),
      Api.churnDistribution(),
      Api.riskDistribution(),
      Api.trends(),
      Api.segmentation(),
    ]);

    document.getElementById('stat-total-customers').textContent = stats.total_customers;
    document.getElementById('stat-total-predictions').textContent = stats.total_predictions;
    document.getElementById('stat-high-risk').textContent = stats.high_risk_customers;
    document.getElementById('stat-medium-risk').textContent = stats.medium_risk_customers;
    document.getElementById('stat-low-risk').textContent = stats.low_risk_customers;
    document.getElementById('stat-churn-rate').textContent = formatPercent(stats.overall_churn_rate);
    document.getElementById('stat-avg-prob').textContent = formatPercent(stats.average_churn_probability);

    renderChurnDistributionChart('chart-churn-distribution', churnDist);
    renderRiskDistributionChart('chart-risk-distribution', riskDist);

    if (trend.length === 0) {
      document.getElementById('chart-trend').closest('.chart-card').innerHTML =
        '<h3>Monthly Prediction Trend</h3><div class="empty-state"><div class="empty-icon">&#8987;</div>No predictions yet — run a churn prediction to start building trend data.</div>';
    } else {
      renderTrendChart('chart-trend', trend);
    }

    renderSegmentationChart('chart-seg-contract', segmentation.by_contract, ['#4F46E5', '#6D64EE', '#A5A0F5']);
    renderSegmentationChart('chart-seg-payment', segmentation.by_payment_method, '#14B8A6');
    renderSegmentationChart('chart-seg-internet', segmentation.by_internet_service, ['#0E9F6E', '#D97706', '#8890A2']);
    renderSegmentationChart('chart-seg-tenure', segmentation.by_tenure_group, '#4F46E5');
  } catch (err) {
    showToast(err.message || 'Failed to load dashboard data', 'error');
  }
})();
