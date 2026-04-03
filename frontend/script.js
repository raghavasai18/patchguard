const API_BASE = "https://patchguard-backend.onrender.com"; // replace with your real backend URL

let severityChartInstance = null;
let complianceChartInstance = null;
let topRiskChartInstance = null;

async function runAnalysis() {
  try {
    document.body.style.opacity = "0.85";

    await fetch(`${API_BASE}/analyze`, {
      method: "POST"
    });

    await loadDashboard();
    const risks = await loadRisks();
    await loadAlerts();
    renderCharts(risks);
  } catch (error) {
    alert("Error running analysis. Check backend connection.");
    console.error(error);
  } finally {
    document.body.style.opacity = "1";
  }
}

async function resetDashboard() {
  try {
    await fetch(`${API_BASE}/reset-analysis`, {
      method: "POST"
    });
  } catch (error) {
    console.error("Reset API error:", error);
  }

  document.getElementById("totalSystems").innerText = 0;
  document.getElementById("totalSoftware").innerText = 0;
  document.getElementById("outdatedSoftware").innerText = 0;
  document.getElementById("criticalAlerts").innerText = 0;
  document.getElementById("highRiskSystems").innerText = 0;
  document.getElementById("compliance").innerText = "0%";

  document.getElementById("riskTableBody").innerHTML = "";
  document.getElementById("alertTableBody").innerHTML = "";

  clearCharts();
  closeModal();
}

function clearCharts() {
  if (severityChartInstance) {
    severityChartInstance.destroy();
    severityChartInstance = null;
  }

  if (complianceChartInstance) {
    complianceChartInstance.destroy();
    complianceChartInstance = null;
  }

  if (topRiskChartInstance) {
    topRiskChartInstance.destroy();
    topRiskChartInstance = null;
  }

  const severityCanvas = document.getElementById("severityChart");
  const complianceCanvas = document.getElementById("complianceChart");
  const topRiskCanvas = document.getElementById("topRiskChart");

  if (severityCanvas) {
    const ctx = severityCanvas.getContext("2d");
    ctx.clearRect(0, 0, severityCanvas.width, severityCanvas.height);
  }

  if (complianceCanvas) {
    const ctx = complianceCanvas.getContext("2d");
    ctx.clearRect(0, 0, complianceCanvas.width, complianceCanvas.height);
  }

  if (topRiskCanvas) {
    const ctx = topRiskCanvas.getContext("2d");
    ctx.clearRect(0, 0, topRiskCanvas.width, topRiskCanvas.height);
  }
}

async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/dashboard-summary`);
    const data = await res.json();

    document.getElementById("totalSystems").innerText = data.total_systems ?? 0;
    document.getElementById("totalSoftware").innerText = data.total_software ?? 0;
    document.getElementById("outdatedSoftware").innerText = data.outdated_software ?? 0;
    document.getElementById("criticalAlerts").innerText = data.critical_alerts ?? 0;
    document.getElementById("highRiskSystems").innerText = data.predicted_high_risk_systems ?? 0;
    document.getElementById("compliance").innerText = (data.patch_compliance_percent ?? 0) + "%";
  } catch (error) {
    console.error("Dashboard load error:", error);
  }
}

async function loadRisks() {
  try {
    const res = await fetch(`${API_BASE}/risks`);
    const data = await res.json();

    const tbody = document.getElementById("riskTableBody");
    tbody.innerHTML = "";

    data.forEach(item => {
      const row = document.createElement("tr");
      const severityClass = (item.severity || "low").toLowerCase();

      row.onclick = () => showDetails(item);

      row.innerHTML = `
        <td>${item.hostname}</td>
        <td>${item.software_name}</td>
        <td>${item.installed_version}</td>
        <td>${item.latest_version}</td>
        <td>${item.days_outdated}</td>
        <td>${item.risk_score}</td>
        <td><span class="${severityClass}">${item.severity}</span></td>
        <td>${item.predicted_high_risk ? "🔥 Yes" : "No"}</td>
      `;

      tbody.appendChild(row);
    });

    return data;
  } catch (error) {
    console.error("Risks load error:", error);
    return [];
  }
}

async function loadAlerts() {
  try {
    const res = await fetch(`${API_BASE}/alerts`);
    const data = await res.json();

    const tbody = document.getElementById("alertTableBody");
    tbody.innerHTML = "";

    data.forEach(item => {
      const row = document.createElement("tr");
      const severityClass = (item.severity || "low").toLowerCase();

      row.innerHTML = `
        <td>${item.hostname}</td>
        <td>${item.message}</td>
        <td><span class="${severityClass}">${item.severity}</span></td>
        <td>${item.status}</td>
      `;

      tbody.appendChild(row);
    });
  } catch (error) {
    console.error("Alerts load error:", error);
  }
}

function renderCharts(risks) {
  renderSeverityChart(risks);
  renderComplianceChart();
  renderTopRiskChart(risks);
}

function renderSeverityChart(risks) {
  const counts = {
    Low: 0,
    Medium: 0,
    High: 0,
    Critical: 0
  };

  risks.forEach(item => {
    if (counts[item.severity] !== undefined) {
      counts[item.severity]++;
    }
  });

  const ctx = document.getElementById("severityChart").getContext("2d");

  if (severityChartInstance) {
    severityChartInstance.destroy();
  }

  severityChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Low", "Medium", "High", "Critical"],
      datasets: [{
        data: [counts.Low, counts.Medium, counts.High, counts.Critical],
        backgroundColor: ["#16a34a", "#f59e0b", "#f97316", "#ef4444"],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

function renderComplianceChart() {
  const totalSoftware = Number(document.getElementById("totalSoftware").innerText) || 0;
  const outdated = Number(document.getElementById("outdatedSoftware").innerText) || 0;
  const updated = Math.max(totalSoftware - outdated, 0);

  const ctx = document.getElementById("complianceChart").getContext("2d");

  if (complianceChartInstance) {
    complianceChartInstance.destroy();
  }

  complianceChartInstance = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Updated", "Outdated"],
      datasets: [{
        data: [updated, outdated],
        backgroundColor: ["#22c55e", "#ef4444"],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

function renderTopRiskChart(risks) {
  const sortedRisks = [...risks]
    .sort((a, b) => b.risk_score - a.risk_score)
    .slice(0, 5);

  const labels = sortedRisks.map(item => `${item.hostname} - ${item.software_name}`);
  const scores = sortedRisks.map(item => item.risk_score);

  const ctx = document.getElementById("topRiskChart").getContext("2d");

  if (topRiskChartInstance) {
    topRiskChartInstance.destroy();
  }

  topRiskChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Risk Score",
        data: scores,
        backgroundColor: "#2563eb",
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      indexAxis: "y",
      scales: {
        x: {
          beginAtZero: true,
          max: 100
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });
}

function showDetails(item) {
  const modal = document.getElementById("detailsModal");
  const content = document.getElementById("modalContent");

  content.innerHTML = `
    <p><b>Hostname:</b> ${item.hostname}</p>
    <p><b>Software:</b> ${item.software_name}</p>
    <p><b>Installed Version:</b> ${item.installed_version}</p>
    <p><b>Latest Version:</b> ${item.latest_version}</p>
    <p><b>Days Outdated:</b> ${item.days_outdated}</p>
    <p><b>Risk Score:</b> ${item.risk_score}</p>
    <p><b>Severity:</b> ${item.severity}</p>
    <p><b>Predicted High Risk:</b> ${item.predicted_high_risk ? "Yes" : "No"}</p>
  `;

  modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("detailsModal");
  if (modal) {
    modal.style.display = "none";
  }
}

window.onclick = function(event) {
  const modal = document.getElementById("detailsModal");
  if (event.target === modal) {
    closeModal();
  }
};

// Start with empty dashboard
resetDashboard();