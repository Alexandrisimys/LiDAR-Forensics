const state = {
  result: null,
  selectedFindingId: null,
  selectedTab: "facts",
  upload: null,
};

const streamColors = {
  lidar: "#176878",
  imu: "#4a78a8",
  motor: "#c38a16",
  encoder: "#6a5797",
  gnss: "#23734c",
  other: "#6f7c82",
};

function element(id) { return document.getElementById(id); }

function streamRole(name) {
  const value = name.toLowerCase();
  if (["lidar", "pointcloud", "points"].some(token => value.includes(token))) return "lidar";
  if (value.includes("imu")) return "imu";
  if (value.includes("motor")) return "motor";
  if (value.includes("encoder")) return "encoder";
  if (value.includes("gnss") || value.includes("gps")) return "gnss";
  return "other";
}

function detectorConfig() {
  return {
    expected_lidar_frequency_hz: Number(element("lidarRate").value),
    minimum_stall_duration_s: Number(element("minStall").value),
    global_gap_threshold_s: Number(element("globalGap").value),
    stale_timestamp_threshold_s: Number(element("staleTime").value),
    catch_up_interval_threshold_s: Number(element("catchup").value),
    active_companion_min_messages: 2,
    termination_threshold_s: 1,
  };
}

function showToast(message, isError = false) {
  const toast = element("toast");
  toast.textContent = message;
  toast.className = `toast visible${isError ? " error" : ""}`;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.className = "toast"; }, 3600);
}

async function apiJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch (_) { /* no JSON body */ }
    throw new Error(detail);
  }
  return response.json();
}

async function loadDatasets() {
  const payload = await apiJson("/api/datasets");
  const select = element("datasetSelect");
  select.innerHTML = payload.datasets.map(item => `<option value="${item.id}">${item.label}</option>`).join("");
  select.value = "lidar_stall_3_4_seconds";
}

function updateInputMode() {
  const usingCustomInput = Boolean(state.upload);
  element("customInputControl").classList.toggle("is-passive", !usingCustomInput);
  document.querySelector(".dataset-control").classList.toggle("is-passive", usingCustomInput);
  element("fileButton").textContent = usingCustomInput ? "Change file" : "Choose file";
}

async function runAnalysis() {
  const button = element("analyzeButton");
  button.disabled = true;
  button.textContent = "Analyzing…";
  try {
    let result;
    if (state.upload) {
      const form = new FormData();
      form.append("file", state.upload);
      form.append("config_json", JSON.stringify(detectorConfig()));
      result = await apiJson("/api/analyze/upload", { method: "POST", body: form });
    } else {
      result = await apiJson("/api/analyze/builtin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_name: element("datasetSelect").value, config: detectorConfig() }),
      });
    }
    state.result = result;
    state.selectedFindingId = result.findings[0]?.finding_id || null;
    state.selectedTab = "facts";
    element("briefPanel").hidden = true;
    renderAll();
    showToast(`Analysis complete: ${result.summary.diagnostic_status}`);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Run analysis";
  }
}

function renderSummary() {
  const result = state.result;
  const primaryCount = result.summary.primary_incident_count;
  const relatedCount = result.summary.related_finding_count;
  const primaryLabel = primaryCount === 1 ? "primary incident" : "primary incidents";
  const relatedLabel = relatedCount === 1 ? "related finding" : "related findings";
  element("statusValue").textContent = result.summary.diagnostic_status;
  element("durationValue").textContent = `${result.duration_s.toFixed(2)} s`;
  element("findingsValue").textContent = result.summary.detected_findings_count;
  element("findingsBreakdown").textContent = `${primaryCount} ${primaryLabel} \u00b7 ${relatedCount} ${relatedLabel}`;
  element("recordingContinuityValue").textContent = `${result.summary.recording_continuity_percent.toFixed(2)}%`;
  element("lidarRelativeAvailabilityValue").textContent = `${result.summary.lidar_relative_availability_percent.toFixed(2)}%`;
  element("observedStreamsValue").textContent = result.summary.observed_streams;
  const summary = document.querySelector(".status-summary");
  summary.classList.toggle("alert", result.summary.diagnostic_status !== "NORMAL");
  element("recordingMeta").textContent = `${result.recording_id} · ${result.event_count.toLocaleString()} events · ${result.source_format.toUpperCase()}`;
}

function svgNode(name, attributes = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
}

function renderTimeline() {
  const result = state.result;
  const svg = element("timeline");
  svg.replaceChildren();
  const names = Object.keys(result.timeline).sort((a, b) => streamRole(a) === "lidar" ? -1 : streamRole(b) === "lidar" ? 1 : a.localeCompare(b));
  const width = 1200;
  const margin = { left: 116, right: 28, top: 34, bottom: 34 };
  const rowHeight = Math.min(46, (250 - margin.top - margin.bottom) / Math.max(names.length, 1));
  const height = margin.top + margin.bottom + rowHeight * names.length;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const span = Math.max(result.end_timestamp - result.start_timestamp, 0.001);
  const x = value => margin.left + ((value - result.start_timestamp) / span) * (width - margin.left - margin.right);

  for (let tick = 0; tick <= 6; tick += 1) {
    const value = result.start_timestamp + span * tick / 6;
    const xpos = x(value);
    svg.appendChild(svgNode("line", { x1: xpos, y1: margin.top - 14, x2: xpos, y2: height - margin.bottom + 4, stroke: "#e0e5e7", "stroke-width": 1 }));
    const label = svgNode("text", { x: xpos, y: height - 9, fill: "#65737a", "font-size": 11, "text-anchor": "middle", "font-family": "Consolas, monospace" });
    label.textContent = `${value.toFixed(1)}s`;
    svg.appendChild(label);
  }

  result.findings.filter(item => item.category !== "NORMAL").forEach(finding => {
    const x1 = x(finding.start);
    const x2 = x(Math.max(finding.end, finding.start + span * 0.002));
    const isFailure = ["LIDAR_STREAM_STALL", "GLOBAL_RECORDING_GAP"].includes(finding.category);
    svg.appendChild(svgNode("rect", {
      x: x1, y: margin.top - 14, width: Math.max(3, x2 - x1), height: rowHeight * names.length + 18,
      fill: isFailure ? "#b33c3c" : "#c38a16", opacity: isFailure ? 0.12 : 0.08,
      stroke: isFailure ? "#b33c3c" : "#c38a16", "stroke-width": 1, "stroke-dasharray": "4 3",
    }));
  });

  names.forEach((name, index) => {
    const y = margin.top + index * rowHeight + rowHeight / 2;
    const role = streamRole(name);
    const color = streamColors[role];
    const label = svgNode("text", { x: margin.left - 12, y: y + 4, fill: "#344149", "font-size": 12, "font-weight": 700, "text-anchor": "end", "font-family": "Arial, sans-serif" });
    label.textContent = name;
    svg.appendChild(label);
    svg.appendChild(svgNode("line", { x1: margin.left, y1: y, x2: width - margin.right, y2: y, stroke: "#cbd4d8", "stroke-width": 1 }));
    result.timeline[name].forEach(timestamp => {
      svg.appendChild(svgNode("line", { x1: x(timestamp), y1: y - 8, x2: x(timestamp), y2: y + 8, stroke: color, "stroke-width": role === "lidar" ? 1.8 : 1, opacity: role === "imu" ? 0.52 : 0.82 }));
    });
  });

  const legend = element("timelineLegend");
  legend.innerHTML = names.map(name => {
    const color = streamColors[streamRole(name)];
    return `<span class="legend-item"><span class="legend-mark" style="--legend-color:${color}"></span>${name}</span>`;
  }).join("") + `<span class="legend-item"><span class="legend-mark" style="--legend-color:#b33c3c;height:10px;opacity:.28"></span>finding window</span>`;
}

function renderFindings() {
  const findings = state.result.findings;
  const findingCount = findings.filter(item => item.finding_role !== "ASSESSMENT").length;
  element("findingBadge").textContent = findingCount
    ? `${findingCount} finding${findingCount === 1 ? "" : "s"}`
    : "Baseline assessment";
  element("findingRows").innerHTML = findings.map(item => {
    const cssClass = item.category.toLowerCase().replaceAll("_", "-");
    const roleClass = item.finding_role.toLowerCase().replaceAll("_", "-");
    const roleLabel = item.finding_role === "PRIMARY_INCIDENT"
      ? "Primary"
      : item.finding_role === "RELATED_FINDING" ? "Related" : "Assessment";
    const selected = item.finding_id === state.selectedFindingId ? "selected" : "";
    return `<tr class="${selected} role-${roleClass}" data-id="${item.finding_id}">
      <td><strong>${item.finding_id}</strong></td>
      <td><span class="finding-role ${roleClass}">${roleLabel}</span></td>
      <td>${item.start.toFixed(3)} s</td>
      <td>${item.duration.toFixed(3)} s</td>
      <td><span class="classification ${cssClass}" title="${item.category}">${item.category}</span></td>
      <td>${item.confidence}</td>
    </tr>`;
  }).join("");
  document.querySelectorAll("#findingRows tr").forEach(row => row.addEventListener("click", () => {
    state.selectedFindingId = row.dataset.id;
    renderFindings();
    renderDetails();
  }));
}

function listMarkup(items, fallback) {
  const values = items?.length ? items : [fallback];
  return `<ul>${values.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function renderDetails() {
  const finding = state.result.findings.find(item => item.finding_id === state.selectedFindingId) || state.result.findings[0];
  if (!finding) return;
  element("selectedFinding").textContent = finding.finding_id;
  element("detailOverview").innerHTML = `<strong>${finding.category} · ${finding.confidence} confidence</strong><p>${escapeHtml(finding.interpretation)}</p>`;
  document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.tab === state.selectedTab));
  const content = element("detailContent");
  if (state.selectedTab === "facts") {
    content.innerHTML = `<h3>Confirmed observations</h3>${listMarkup(finding.confirmed_facts, "No configured anomaly threshold was exceeded.")}`;
  } else if (state.selectedTab === "assessment") {
    content.innerHTML = `<h3>Interpretation</h3><p>${escapeHtml(finding.interpretation)}</p><h3>Hypotheses, not proven causes</h3>${listMarkup(finding.hypotheses, "No failure hypothesis is asserted.")}<h3>Missing evidence</h3>${listMarkup(finding.missing_evidence, "No additional evidence listed.")}`;
  } else if (state.selectedTab === "evidence") {
    content.innerHTML = `<pre>${escapeHtml(JSON.stringify(finding.evidence, null, 2))}</pre>`;
  } else {
    content.innerHTML = `<h3>Recommended next tests</h3>${listMarkup(finding.recommended_tests, "Retain this recording as a comparison baseline.")}`;
  }
}

function renderAll() {
  renderSummary();
  renderTimeline();
  renderFindings();
  renderDetails();
}

async function exportFormat(format) {
  if (!state.result) return;
  try {
    const response = await fetch(`/api/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.result),
    });
    if (!response.ok) throw new Error(`Export failed (${response.status})`);
    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = disposition.match(/filename=([^;]+)/)?.[1] || `lidar_forensics.${format}`;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
    showToast(`${filename} generated`);
  } catch (error) { showToast(error.message, true); }
}

async function generateBrief() {
  if (!state.result) return;
  const button = element("briefButton");
  button.disabled = true;
  try {
    const payload = await apiJson("/api/brief", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.result),
    });
    element("briefText").textContent = payload.markdown;
    element("briefGenerator").textContent = payload.generator;
    element("briefPanel").hidden = false;
    element("briefPanel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { showToast(error.message, true); }
  finally { button.disabled = false; }
}

function bindControls() {
  element("fileButton").addEventListener("click", () => element("fileInput").click());
  element("fileInput").addEventListener("change", event => {
    state.upload = event.target.files[0] || null;
    element("fileName").textContent = state.upload ? state.upload.name : "No file selected";
    updateInputMode();
  });
  element("datasetSelect").addEventListener("change", () => {
    state.upload = null;
    element("fileInput").value = "";
    element("fileName").textContent = "No file selected";
    updateInputMode();
  });
  element("analyzeButton").addEventListener("click", runAnalysis);
  document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
    state.selectedTab = tab.dataset.tab;
    renderDetails();
  }));
  document.querySelectorAll("[data-format]").forEach(button => button.addEventListener("click", () => exportFormat(button.dataset.format)));
  element("briefButton").addEventListener("click", generateBrief);
  updateInputMode();
}

async function initialize() {
  bindControls();
  try {
    await loadDatasets();
    await runAnalysis();
  } catch (error) { showToast(error.message, true); }
}

initialize();
