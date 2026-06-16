const form = document.querySelector("#complaintForm");
const textArea = document.querySelector("#complaintText");
const clearButton = document.querySelector("#clearButton");
const printButton = document.querySelector("#printButton");
const evidenceImages = document.querySelector("#evidenceImages");
const firSectionSelect = document.querySelector("#firSectionSelect");
const firSectionPanels = document.querySelectorAll("[data-fir-section]");
const firSectionEmpty = document.querySelector("[data-fir-empty]");
const analyzeButton = form.querySelector("button[type='submit']");
let currentAttachments = [];

const heroPillMessages = [
  "AI-powered complaint triage for police teams",
  "Classifies cyber, theft, traffic, harassment, and fraud complaints",
  "Detects priority, evidence, entities, and next steps automatically",
  "Generates clean PDF reports for case handover",
  "Stores complaint analytics for dashboard insights"
];

clearComplaintState();
startHeroPillRotation();

window.addEventListener("pageshow", () => {
  clearComplaintState();
});

function clearComplaintState() {
  form.reset();
  currentAttachments = [];
  const preview = document.querySelector("#attachmentPreview");
  if (preview) {
    preview.innerHTML = "";
  }
  updateFileUploadStatus([]);
  setActiveFirSection("");
  document.querySelector("#report").classList.add("hidden");
  document.querySelector("#emptyState").classList.remove("hidden");
}

function setLoading(isLoading) {
  analyzeButton.disabled = isLoading;
  analyzeButton.textContent = isLoading ? "Creating report..." : "Create Report";
}

function startHeroPillRotation() {
  const pillText = document.querySelector("#heroPillText");
  if (!pillText) {
    return;
  }

  let index = 0;
  window.setInterval(() => {
    index = (index + 1) % heroPillMessages.length;
    pillText.classList.add("is-changing");

    window.setTimeout(() => {
      pillText.textContent = heroPillMessages[index];
      pillText.classList.remove("is-changing");
    }, 180);
  }, 2600);
}

function setActiveFirSection(sectionName) {
  if (firSectionSelect) {
    firSectionSelect.value = sectionName;
  }

  firSectionPanels.forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.firSection !== sectionName);
  });

  if (firSectionEmpty) {
    firSectionEmpty.classList.toggle("hidden", Boolean(sectionName));
  }
}

async function analyzeComplaint(payload) {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || "Analysis failed");
  }

  return result;
}

function collectFirDetails() {
  return {
    complainant_details: {
      name: valueOf("complainantName"),
      father_name: valueOf("complainantFatherName"),
      address: valueOf("complainantAddress"),
      contact_number: valueOf("complainantContact"),
      occupation: valueOf("complainantOccupation")
    },
    victim_details: {
      name: valueOf("victimName"),
      address: valueOf("victimAddress"),
      relation_to_complainant: valueOf("victimRelation")
    },
    incident_details: {
      date: valueOf("incidentDate"),
      time: valueOf("incidentTime"),
      place: valueOf("incidentPlace"),
      accused_name_or_description: valueOf("accusedDetails")
    },
    cybercrime_details: {
      transaction_id: valueOf("transactionId"),
      accused_phone_email_or_handle: valueOf("accusedContact"),
      platform: valueOf("crimePlatform")
    }
  };
}

function valueOf(id) {
  const element = document.querySelector(`#${id}`);
  return element ? element.value.trim() : "";
}

async function prepareAttachments(files) {
  const selected = [...files].slice(0, 6);
  return Promise.all(selected.map((file) => resizeImage(file)));
}

function resizeImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const image = new Image();
      image.onload = () => {
        const maxWidth = 1100;
        const ratio = Math.min(1, maxWidth / image.width);
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(image.width * ratio);
        canvas.height = Math.round(image.height * ratio);
        const context = canvas.getContext("2d");
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
        resolve({
          name: file.name,
          type: "image/jpeg",
          size: file.size,
          data_url: canvas.toDataURL("image/jpeg", 0.72)
        });
      };
      image.onerror = reject;
      image.src = reader.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderList(elementId, items, tagName = "li") {
  const element = document.querySelector(elementId);
  element.innerHTML = "";

  (items || []).forEach((item) => {
    const child = document.createElement(tagName);
    child.textContent = item;
    if (tagName === "span") {
      child.className = "chip";
    }
    element.appendChild(child);
  });
}

function renderReport(report) {
  document.querySelector("#emptyState").classList.add("hidden");
  document.querySelector("#report").classList.remove("hidden");

  document.querySelector("#summaryText").textContent = report.summary;
  document.querySelector("#categoryText").textContent = report.category;
  document.querySelector("#departmentText").textContent = report.department;
  document.querySelector("#timestampText").textContent = new Date(report.timestamp).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  });
  document.querySelector("#originalText").textContent = report.original_complaint;

  const priorityText = document.querySelector("#priorityText");
  priorityText.textContent = `${report.priority} / ${report.risk_level}`;
  priorityText.className = `priority-${String(report.priority).toLowerCase()}`;

  document.querySelector("#engineText").textContent = report.engine_display || report.engine;
  document.querySelector("#providerStatusText").textContent = report.provider_status_display || report.provider_error || "Connected and completed successfully";
  document.querySelector("#confidenceText").textContent = `${Math.round(Number(report.confidence || 0) * 100)}%`;
  document.querySelector("#reviewText").textContent = report.needs_human_review ? "Yes" : "No";
  document.querySelector("#complaintIdText").textContent = report.complaint_id ? `#${report.complaint_id}` : "-";
  document.querySelector("#reasoningText").textContent = report.reasoning;

  renderList("#keywordsList", report.keywords, "span");
  renderList("#evidenceList", report.evidence_checklist);
  renderList("#stepsList", report.next_steps);
  renderList("#legalSectionsList", report.possible_legal_sections);
  renderFirDetails(report.fir_details || {});
  renderEntities(report.entities || {});
  renderPipelineDetails(report.preprocessing || {});
  renderSimilarComplaints(report.similar_complaints || []);
  renderAttachments("#reportAttachments", report.attachments || []);
}

function renderEntities(entities) {
  const rows = Object.entries(entities)
    .filter(([, values]) => Array.isArray(values) && values.length)
    .map(([key, values]) => `${formatEntityName(key)}: ${values.join(", ")}`);

  renderList("#entitiesList", rows.length ? rows : ["No structured entities detected"]);
}

function formatEntityName(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderSimilarComplaints(matches) {
  const container = document.querySelector("#similarComplaintsList");
  container.innerHTML = "";

  if (!matches.length) {
    const empty = document.createElement("p");
    empty.className = "muted-note";
    empty.textContent = "No similar registered complaints found yet.";
    container.appendChild(empty);
    return;
  }

  matches.forEach((match) => {
    const card = document.createElement("a");
    card.className = "similar-card";
    card.href = match.url;
    card.target = "_blank";
    card.rel = "noopener";

    const title = document.createElement("strong");
    title.textContent = `${match.similarity}% similar to Complaint #${match.id}`;

    const meta = document.createElement("span");
    meta.textContent = `${match.category} • ${match.priority}`;

    const summary = document.createElement("p");
    summary.textContent = match.summary || "Open complaint record";

    card.append(title, meta, summary);
    container.appendChild(card);
  });
}

function renderFirDetails(details) {
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

  const container = document.querySelector("#firDetailsList");
  container.innerHTML = "";
  if (!rows.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "No structured FIR draft details entered.";
    container.appendChild(note);
    return;
  }

  rows.forEach((row) => {
    const item = document.createElement("div");
    const label = document.createElement("span");
    label.textContent = row.label;
    const value = document.createElement("strong");
    value.textContent = row.value;
    item.append(label, value);
    container.appendChild(item);
  });
}

function renderPipelineDetails(preprocessing) {
  const rows = [
    ["Detected Language", preprocessing.language_detected],
    ["Token Count", preprocessing.token_count],
    ["Transliteration", preprocessing.transliteration],
    ["Clean Text", preprocessing.clean_text],
  ].filter(([, value]) => value !== undefined && value !== null && String(value).trim());

  const container = document.querySelector("#pipelineDetailsList");
  container.innerHTML = "";

  if (!rows.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "Pipeline metadata not available.";
    container.appendChild(note);
    return;
  }

  rows.forEach(([label, value]) => {
    const item = document.createElement("div");
    const labelElement = document.createElement("span");
    labelElement.textContent = label;
    const valueElement = document.createElement("strong");
    valueElement.textContent = value;
    item.append(labelElement, valueElement);
    container.appendChild(item);
  });
}

function renderAttachments(selector, attachments) {
  const container = document.querySelector(selector);
  container.innerHTML = "";
  if (!attachments.length) {
    const note = document.createElement("p");
    note.className = "muted-note";
    note.textContent = "No evidence images attached.";
    container.appendChild(note);
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
    container.appendChild(figure);
  });
}

function updateFileUploadStatus(files) {
  const status = document.querySelector("#fileUploadStatus");
  if (!status) {
    return;
  }

  if (!files.length) {
    status.textContent = "No files selected";
    return;
  }

  status.textContent = files.length === 1
    ? files[0].name
    : `${files.length} images selected`;
}

async function submitComplaint(text) {
  setLoading(true);
  try {
    const firDetails = collectFirDetails();
    const report = await analyzeComplaint({
      complaint_text: text,
      fir_details: firDetails,
      attachments: currentAttachments
    });
    renderReport(report);
  } catch (error) {
    alert(error.message);
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = textArea.value.trim();
  const firDetails = collectFirDetails();

  if (!text && !hasFirDetails(firDetails) && !currentAttachments.length) {
    alert("Please enter complaint text or fill at least one FIR detail.");
    return;
  }

  submitComplaint(text);
});

function hasFirDetails(details) {
  return Object.values(details).some((section) => {
    if (!section || typeof section !== "object") {
      return false;
    }
    return Object.values(section).some((value) => String(value || "").trim());
  });
}

clearButton.addEventListener("click", () => {
  clearComplaintState();
  document.querySelector("#report").classList.add("hidden");
  document.querySelector("#emptyState").classList.remove("hidden");
  textArea.focus();
});

firSectionSelect.addEventListener("change", () => {
  setActiveFirSection(firSectionSelect.value);
});

evidenceImages.addEventListener("change", async () => {
  updateFileUploadStatus([...evidenceImages.files]);
  currentAttachments = await prepareAttachments(evidenceImages.files);
  renderAttachments("#attachmentPreview", currentAttachments);
});

printButton.addEventListener("click", () => {
  window.print();
});
