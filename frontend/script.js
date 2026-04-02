const API_BASE = "http://127.0.0.1:5000";

async function runAnalysis() {
  await fetch(`${API_BASE}/analyze`, {
    method: "POST"
  });
  await loadDashboard();
  await loadRisks();
  await loadAlerts();
}

async function loadDashboard() {
  const res = await fetch(`${API_BASE}/dashboard-summary`);
  const data = await res.json();

  document.getElementById("totalSystems").innerText = data.total_systems;
  document.getElementById("totalSoftware").innerText = data.total_software;
  document.getElementById("outdatedSoftware").innerText = data.outdated_software;
  document.getElementById("criticalAlerts").innerText = data.critical_alerts;
  document.getElementById("highRiskSystems").innerText = data.predicted_high_risk_systems;
  document.getElementById("compliance").innerText = data.patch_compliance_percent + "%";
}

async function loadRisks() {
  const res = await fetch(`${API_BASE}/risks`);
  const data = await res.json();

  const tbody = document.getElementById("riskTableBody");
  tbody.innerHTML = "";

  data.forEach(item => {
    const row = document.createElement("tr");
    const severityClass = item.severity.toLowerCase();

    row.innerHTML = `
      <td>${item.hostname}</td>
      <td>${item.software_name}</td>
      <td>${item.installed_version}</td>
      <td>${item.latest_version}</td>
      <td>${item.days_outdated}</td>
      <td>${item.risk_score}</td>
      <td class="${severityClass}">${item.severity}</td>
      <td>${item.predicted_high_risk ? "Yes" : "No"}</td>
    `;

    tbody.appendChild(row);
  });
}

async function loadAlerts() {
  const res = await fetch(`${API_BASE}/alerts`);
  const data = await res.json();

  const tbody = document.getElementById("alertTableBody");
  tbody.innerHTML = "";

  data.forEach(item => {
    const row = document.createElement("tr");
    const severityClass = item.severity.toLowerCase();

    row.innerHTML = `
      <td>${item.hostname}</td>
      <td>${item.message}</td>
      <td class="${severityClass}">${item.severity}</td>
      <td>${item.status}</td>
    `;

    tbody.appendChild(row);
  });
}

loadDashboard();
loadRisks();
loadAlerts();