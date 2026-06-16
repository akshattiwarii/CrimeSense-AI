const refreshDashboardButton = document.querySelector("#refreshDashboardButton");

loadDashboard();

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) {
      return;
    }
    const stats = await response.json();
    renderDashboard(stats);
  } catch {
    // Static file mode or server unavailable.
  }
}

function renderDashboard(stats) {
  const categories = stats.category_distribution || [];
  const weekly = stats.weekly_trends || [];
  const topCategory = categories[0];
  const topCybercrime = stats.most_common_cybercrime || {};

  document.querySelector("#totalComplaintsText").textContent = stats.total_complaints || 0;
  document.querySelector("#topCategoryText").textContent = topCategory
    ? `${topCategory.category} (${topCategory.count})`
    : "No data yet";
  document.querySelector("#topCybercrimeText").textContent = topCybercrime.count
    ? `${topCybercrime.category} (${topCybercrime.count})`
    : "No cybercrime complaints yet";

  drawBarChart("categoryChart", categories, "category");
  drawWeeklyBarChart("weeklyChart", weekly);
  renderRecentComplaints(stats.recent_complaints || []);
}

function drawBarChart(canvasId, rows, labelKey) {
  const canvas = document.querySelector(`#${canvasId}`);
  const context = canvas.getContext("2d");
  canvas.width = canvas.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.clientHeight * window.devicePixelRatio;
  const scale = window.devicePixelRatio;
  context.scale(scale, scale);
  context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);

  if (!rows.length) {
    drawEmptyChart(context, canvas, "No category data yet");
    return;
  }

  const chartRows = rows.slice(0, 7);
  const max = Math.max(...chartRows.map((row) => row.count), 1);
  const left = 150;
  const top = 20;
  const barHeight = 24;
  const gap = 12;
  const chartWidth = canvas.clientWidth - left - 48;

  context.font = "13px system-ui";
  context.textBaseline = "middle";

  chartRows.forEach((row, index) => {
    const y = top + index * (barHeight + gap);
    const barWidth = Math.max(8, (row.count / max) * chartWidth);
    context.fillStyle = "#8fa7b7";
    context.fillText(trimLabel(row[labelKey], 20), 0, y + barHeight / 2);
    context.fillStyle = "#18e2f2";
    context.fillRect(left, y, barWidth, barHeight);
    context.fillStyle = "#effcff";
    context.fillText(String(row.count), left + barWidth + 8, y + barHeight / 2);
  });
}

function drawWeeklyBarChart(canvasId, rows) {
  const canvas = document.querySelector(`#${canvasId}`);
  const context = canvas.getContext("2d");
  canvas.width = canvas.clientWidth * window.devicePixelRatio;
  canvas.height = canvas.clientHeight * window.devicePixelRatio;
  const scale = window.devicePixelRatio;
  context.scale(scale, scale);
  context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);

  if (!rows.length) {
    drawEmptyChart(context, canvas, "No weekly data yet");
    return;
  }

  const left = 34;
  const right = 18;
  const top = 24;
  const bottom = 42;
  const max = Math.max(...rows.map((row) => row.count), 1);
  const chartWidth = canvas.clientWidth - left - right;
  const chartHeight = canvas.clientHeight - top - bottom;
  const slotWidth = chartWidth / rows.length;
  const barWidth = Math.min(42, slotWidth * 0.56);

  context.font = "12px system-ui";
  context.textAlign = "center";

  context.strokeStyle = "rgba(151, 232, 255, 0.16)";
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(left, top);
  context.lineTo(left, top + chartHeight);
  context.lineTo(left + chartWidth, top + chartHeight);
  context.stroke();

  rows.forEach((row, index) => {
    const centerX = left + index * slotWidth + slotWidth / 2;
    const barHeight = row.count ? Math.max(8, (row.count / max) * chartHeight) : 0;
    const x = centerX - barWidth / 2;
    const y = top + chartHeight - barHeight;

    context.fillStyle = "rgba(151, 232, 255, 0.08)";
    context.fillRect(x, top, barWidth, chartHeight);

    if (barHeight) {
      const gradient = context.createLinearGradient(0, y, 0, top + chartHeight);
      gradient.addColorStop(0, "#25f7b5");
      gradient.addColorStop(1, "#18e2f2");
      context.fillStyle = gradient;
      context.fillRect(x, y, barWidth, barHeight);
    }

    context.fillStyle = "#effcff";
    context.fillText(String(row.count || 0), centerX, y - 8);

    context.fillStyle = "#8fa7b7";
    context.fillText(shortDayLabel(row.day || row.date || "-"), centerX, top + chartHeight + 20);
  });

  context.textAlign = "start";
}

function drawEmptyChart(context, canvas, message) {
  context.fillStyle = "#8fa7b7";
  context.font = "14px system-ui";
  context.textAlign = "center";
  context.fillText(message, canvas.clientWidth / 2, canvas.clientHeight / 2);
  context.textAlign = "start";
}

function renderRecentComplaints(records) {
  const body = document.querySelector("#recentComplaintsTable");
  body.innerHTML = "";

  if (!records.length) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="4">No complaints analyzed yet.</td>';
    body.appendChild(row);
    return;
  }

  records.forEach((record) => {
    const row = document.createElement("tr");
    row.appendChild(tableCell(formatDate(record.timestamp)));
    const categoryCell = tableCell("");
    const link = document.createElement("a");
    link.href = `complaint.html?id=${record.id}`;
    link.textContent = record.category || "Unknown";
    categoryCell.appendChild(link);
    row.appendChild(categoryCell);
    row.appendChild(tableCell(record.priority));
    row.appendChild(tableCell(record.summary));
    body.appendChild(row);
  });
}

function tableCell(value) {
  const cell = document.createElement("td");
  cell.textContent = value || "-";
  return cell;
}

function formatDate(timestamp) {
  if (!timestamp) {
    return "-";
  }
  return new Date(timestamp).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

function trimLabel(label, maxLength) {
  return label.length > maxLength ? `${label.slice(0, maxLength - 1)}...` : label;
}

function shortDayLabel(label) {
  const parts = String(label).split(" ");
  return parts.length >= 2 ? `${parts[0]} ${parts[1]}` : String(label);
}

refreshDashboardButton.addEventListener("click", () => {
  loadDashboard();
});

let resizeTimer;
window.addEventListener("resize", () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(loadDashboard, 180);
});
