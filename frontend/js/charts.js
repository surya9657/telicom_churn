/* ============================================================
   charts.js — Chart.js instance factories used across the dashboard,
   model performance, and customer detail pages.
   ============================================================ */

const ChartTheme = {
  ink: '#131A2A',
  muted: '#8890A2',
  border: '#E4E7F0',
  accent: '#4F46E5',
  accent2: '#14B8A6',
  low: '#0E9F6E',
  medium: '#D97706',
  high: '#DC2626',
  font: "Inter, sans-serif",
};

Chart.defaults.font.family = ChartTheme.font;
Chart.defaults.color = ChartTheme.muted;
Chart.defaults.borderColor = ChartTheme.border;

function renderChurnDistributionChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Churned', 'Retained'],
      datasets: [
        {
          data: [data.churned, data.not_churned],
          backgroundColor: [ChartTheme.high, ChartTheme.accent2],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
    },
  });
}

function renderRiskDistributionChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['High', 'Medium', 'Low'],
      datasets: [
        {
          data: [data.high, data.medium, data.low],
          backgroundColor: [ChartTheme.high, ChartTheme.medium, ChartTheme.low],
          borderRadius: 6,
          maxBarThickness: 48,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: ChartTheme.border } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderTrendChart(canvasId, trendRows) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: trendRows.map((r) => r.month),
      datasets: [
        {
          label: 'Total predictions',
          data: trendRows.map((r) => r.total_predictions),
          borderColor: ChartTheme.accent,
          backgroundColor: 'rgba(79, 70, 229, 0.08)',
          tension: 0.35,
          fill: true,
          pointRadius: 3,
        },
        {
          label: 'Predicted churn',
          data: trendRows.map((r) => r.predicted_churn),
          borderColor: ChartTheme.high,
          backgroundColor: 'rgba(220, 38, 38, 0.06)',
          tension: 0.35,
          fill: true,
          pointRadius: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: ChartTheme.border } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderSegmentationChart(canvasId, segmentObject, colorList) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  const labels = Object.keys(segmentObject);
  const values = Object.values(segmentObject);
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colorList || ChartTheme.accent,
          borderRadius: 6,
          maxBarThickness: 40,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: ChartTheme.border } },
        y: { grid: { display: false } },
      },
    },
  });
}

function renderProbabilityHistoryChart(canvasId, historyRows) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  const rows = [...historyRows].reverse();
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: rows.map((r) => new Date(r.created_at).toLocaleDateString()),
      datasets: [
        {
          label: 'Churn probability',
          data: rows.map((r) => r.churn_probability),
          borderColor: ChartTheme.accent,
          backgroundColor: 'rgba(79, 70, 229, 0.08)',
          tension: 0.3,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: rows.map((r) =>
            r.risk_level === 'High' ? ChartTheme.high : r.risk_level === 'Medium' ? ChartTheme.medium : ChartTheme.low
          ),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 1, ticks: { callback: (v) => `${Math.round(v * 100)}%` }, grid: { color: ChartTheme.border } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderMetricsComparisonChart(canvasId, rfMetrics, lrMetrics) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  const labels = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC'];
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Random Forest',
          data: [rfMetrics.accuracy, rfMetrics.precision, rfMetrics.recall, rfMetrics.f1_score, rfMetrics.roc_auc],
          backgroundColor: ChartTheme.accent,
          borderRadius: 6,
        },
        {
          label: 'Logistic Regression',
          data: lrMetrics
            ? [lrMetrics.accuracy, lrMetrics.precision, lrMetrics.recall, lrMetrics.f1_score, lrMetrics.roc_auc]
            : [],
          backgroundColor: ChartTheme.accent2,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
      scales: {
        y: { beginAtZero: true, max: 1, grid: { color: ChartTheme.border } },
        x: { grid: { display: false } },
      },
    },
  });
}
