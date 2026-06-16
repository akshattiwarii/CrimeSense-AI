const params = new URLSearchParams(window.location.search);
const complaintId = params.get("id");

loadComplaint();

async function loadComplaint() {
  if (!complaintId) {
    showError("Complaint ID missing.");
    return;
  }

  try {
    const response = await fetch(`/api/complaint?id=${encodeURIComponent(complaintId)}`);
    const record = await response.json();
    if (!response.ok) {
      showError(record.error || "Complaint not found.");
      return;
    }
    renderComplaint(record);
  } catch {
    showError("Unable to load complaint record.");
  }
}

function renderComplaint(record) {
  document.querySelector("#complaintTitle").textContent = `Complaint #${record.id}`;
  document.querySelector("#detailCategory").textContent = record.category || "-";
  document.querySelector("#detailPriority").textContent = `${record.priority || "-"} / ${record.risk_level || "-"}`;
  document.querySelector("#detailDepartment").textContent = record.department || "-";
  document.querySelector("#detailTimestamp").textContent = record.timestamp ? new Date(record.timestamp).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }) : "-";
  document.querySelector("#detailSummary").textContent = record.summary || "-";
  document.querySelector("#detailOriginal").textContent = record.original_complaint || "Original text not available for this older record.";
  document.querySelector("#detailEngine").textContent = record.engine_display || record.engine || "-";
  document.querySelector("#detailConfidence").textContent = `${Math.round(Number(record.confidence || 0) * 100)}%`;
  document.querySelector("#detailReview").textContent = record.needs_human_review ? "Yes" : "No";
  document.querySelector("#detailReasoning").textContent = record.reasoning || "Reasoning not available for this older record.";

  renderChips("#detailKeywords", record.keywords || []);
  renderList("#detailEvidence", record.evidence_checklist || [], "Evidence checklist not available for this older record.");
  renderList("#detailSteps", record.next_steps || [], "Suggested steps not available for this older record.");
  renderList("#detailLegalSections", record.possible_legal_sections || [], "Legal section suggestions not available for this older record.");
  renderFirDetails(record.fir_details || {});
  renderEntities(record.entities || {});
  renderPipeline(record.preprocessing || {});
  renderSimilar(record.similar_complaints || []);
  renderAttachments(record.attachments || []);
}

function showError(message) {
  document.querySelector("#complaintTitle").textContent = message;
}

function renderChips(selector, items) {
  const box = document.querySelector(selector);
  box.innerHTML = "";

  if (!items.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "No keywords stored for this record.";
    box.appendChild(note);
    return;
  }

  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item;
    box.appendChild(chip);
  });
}

function renderList(selector, items, emptyText) {
  const list = document.querySelector(selector);
  list.innerHTML = "";

  if (!items.length) {
    const item = document.createElement("li");
    item.textContent = emptyText;
    list.appendChild(item);
    return;
  }

  items.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
}

function renderEntities(entities) {
  const rows = Object.entries(entities)
    .filter(([, values]) => Array.isArray(values) && values.length)
    .map(([key, values]) => `${formatEntityName(key)}: ${values.join(", ")}`);

  renderList("#detailEntities", rows, "No structured entities stored for this record.");
}

function renderSimilar(matches) {
  const box = document.querySelector("#detailSimilar");
  box.innerHTML = "";

  if (!matches.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "No similar complaints were stored for this record.";
    box.appendChild(note);
    return;
  }

  matches.forEach((match) => {
    const card = document.createElement("a");
    card.className = "similar-card";
    card.href = match.url || `complaint.html?id=${match.id}`;

    const title = document.createElement("strong");
    title.textContent = `${match.similarity}% similar to Complaint #${match.id}`;

    const meta = document.createElement("span");
    meta.textContent = `${match.category || "Unknown"} • ${match.priority || "Unknown"}`;

    const summary = document.createElement("p");
    summary.textContent = match.summary || "Open complaint record";

    card.append(title, meta, summary);
    box.appendChild(card);
  });
}

function renderFirDetails(details) {
  const box = document.querySelector("#detailFirDetails");
  box.innerHTML = "";
  const rows = [];

  Object.entries(details).forEach(([section, values]) => {
    if (!values || typeof values !== "object") {
      return;
    }
    Object.entries(values).forEach(([key, value]) => {
      if (value) {
        rows.push({
          label: `${formatEntityName(section)} - ${formatEntityName(key)}`,
          value
        });
      }
    });
  });

  if (!rows.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "FIR draft details not available for this older record.";
    box.appendChild(note);
    return;
  }

  rows.forEach((row) => {
    const item = document.createElement("div");
    const label = document.createElement("span");
    label.textContent = row.label;
    const value = document.createElement("strong");
    value.textContent = row.value;
    item.append(label, value);
    box.appendChild(item);
  });
}

function renderPipeline(preprocessing) {
  const box = document.querySelector("#detailPipeline");
  box.innerHTML = "";

  const rows = [
    ["Detected Language", preprocessing.language_detected],
    ["Token Count", preprocessing.token_count],
    ["Transliteration", preprocessing.transliteration],
    ["Clean Text", preprocessing.clean_text],
  ].filter(([, value]) => value !== undefined && value !== null && String(value).trim());

  if (!rows.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "Pipeline metadata not available for this older record.";
    box.appendChild(note);
    return;
  }

  rows.forEach(([label, value]) => {
    const item = document.createElement("div");
    const labelElement = document.createElement("span");
    labelElement.textContent = label;
    const valueElement = document.createElement("strong");
    valueElement.textContent = value;
    item.append(labelElement, valueElement);
    box.appendChild(item);
  });
}

function renderAttachments(attachments) {
  const box = document.querySelector("#detailAttachments");
  box.innerHTML = "";

  if (!attachments.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "No evidence images stored for this record.";
    box.appendChild(note);
    return;
  }

  attachments.forEach((attachment) => {
    const figure = document.createElement("figure");
    const image = document.createElement("img");
    image.src = attachment.data_url;
    image.alt = attachment.name || "Evidence image";
    const caption = document.createElement("figcaption");
    caption.textContent = attachment.name || "Evidence image";
    figure.append(image, caption);
    box.appendChild(figure);
  });
}

function formatEntityName(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
