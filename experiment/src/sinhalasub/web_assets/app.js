const state = {
  document: null,
  filename: "",
  filter: "all",
  query: "",
  preparation: null,
  quality: null,
  session: null,
};
const graphemeSegmenter = "Segmenter" in Intl ? new Intl.Segmenter("si", { granularity: "grapheme" }) : null;

const welcome = document.querySelector("#welcome");
const workspace = document.querySelector("#workspace");
const uploadForm = document.querySelector("#upload-form");
const fileInput = document.querySelector("#subtitle-file");
const dropZone = document.querySelector("#drop-zone");
const fileChoice = document.querySelector("#file-choice");
const uploadError = document.querySelector("#upload-error");
const workspaceError = document.querySelector("#workspace-error");
const cueList = document.querySelector("#cue-list");
const emptyResults = document.querySelector("#empty-results");
const searchInput = document.querySelector("#cue-search");

function formatForFilename(filename) {
  const extension = filename.toLowerCase().split(".").pop();
  if (extension === "srt") return "srt";
  if (extension === "vtt" || extension === "webvtt") return "webvtt";
  throw new Error("Choose an SRT, VTT, or WebVTT file.");
}

function formatTime(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const millis = milliseconds % 1000;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

function graphemeCount(text) {
  return graphemeSegmenter ? Array.from(graphemeSegmenter.segment(text)).length : Array.from(text).length;
}

function startSession() {
  state.session = {
    startedAt: new Date().toISOString(),
    startedPerformance: performance.now(),
    activeEditMs: 0,
    activeSince: null,
    keyboardActions: 0,
    editEvents: 0,
    approvalChanges: 0,
  };
}

function startActiveEdit() {
  if (state.session && state.session.activeSince === null) state.session.activeSince = performance.now();
}

function stopActiveEdit() {
  if (!state.session || state.session.activeSince === null) return;
  state.session.activeEditMs += performance.now() - state.session.activeSince;
  state.session.activeSince = null;
}

function sessionPayload() {
  const now = performance.now();
  const inProgress = state.session.activeSince === null ? 0 : now - state.session.activeSince;
  const activeEditMs = Math.round(state.session.activeEditMs + inProgress);
  const elapsedMs = Math.max(activeEditMs, Math.round(now - state.session.startedPerformance));
  return {
    started_at: state.session.startedAt,
    ended_at: new Date().toISOString(),
    elapsed_ms: elapsedMs,
    active_edit_ms: activeEditMs,
    keyboard_actions: state.session.keyboardActions,
    edit_events: state.session.editEvents,
    approval_changes: state.session.approvalChanges,
    approved_cue_ids: state.document.cues.filter((cue) => cue.approved).map((cue) => cue.id),
  };
}

function downloadText(content, filename, type) {
  const blob = new Blob([content], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function clearError(element) {
  element.textContent = "";
  element.hidden = true;
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.error || "The request failed.");
  return data;
}

function selectedFile() {
  return fileInput.files && fileInput.files[0];
}

function updateFileChoice(file) {
  fileChoice.textContent = file ? `${file.name} · ${Math.max(1, Math.round(file.size / 1024))} KB` : "No file selected";
}

fileInput.addEventListener("change", () => {
  clearError(uploadError);
  updateFileChoice(selectedFile());
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const files = event.dataTransfer.files;
  if (!files.length) return;
  fileInput.files = files;
  updateFileChoice(files[0]);
  clearError(uploadError);
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError(uploadError);
  const file = selectedFile();
  if (!file) {
    showError(uploadError, "Choose a subtitle file first.");
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    showError(uploadError, "The file is larger than the 2 MiB experiment limit.");
    return;
  }

  const submitButton = uploadForm.querySelector("button[type='submit']");
  submitButton.disabled = true;
  submitButton.firstChild.textContent = "Opening... ";
  try {
    const format = formatForFilename(file.name);
    const content = await file.text();
    state.document = await postJson("/api/parse", { format, content });
    state.filename = file.name;
    state.filter = "all";
    state.query = "";
    state.preparation = null;
    state.quality = null;
    startSession();
    searchInput.value = "";
    document.querySelectorAll(".filter-button").forEach((button) => button.classList.toggle("active", button.dataset.filter === "all"));
    openWorkspace();
  } catch (error) {
    showError(uploadError, error.message);
  } finally {
    submitButton.disabled = false;
    submitButton.firstChild.textContent = "Open workspace ";
  }
});

function openWorkspace() {
  document.querySelector("#workspace-title").textContent = state.filename;
  document.querySelector("#source-file-name").textContent = state.filename;
  document.querySelector("#cue-total").textContent = state.document.cues.length;
  document.querySelector("#format-label").textContent = state.document.format === "srt" ? "SRT" : "WebVTT";
  welcome.hidden = true;
  workspace.hidden = false;
  document.querySelector("#confirmed-names").value = "";
  document.querySelector("#preparation-status").textContent = "Not prepared yet";
  updateQaSummary();
  renderCues();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderCues() {
  cueList.replaceChildren();
  const normalizedQuery = state.query.trim().toLocaleLowerCase();
  const visible = state.document.cues.filter((cue) => {
    const filterMatch = state.filter === "all" || (state.filter === "approved" ? cue.approved : !cue.approved);
    const queryMatch = !normalizedQuery || `${cue.text}\n${cue.target_text}`.toLocaleLowerCase().includes(normalizedQuery);
    return filterMatch && queryMatch;
  });

  visible.forEach((cue) => cueList.append(createCueCard(cue)));
  emptyResults.hidden = visible.length !== 0;
  updateProgress();
}

function createCueCard(cue) {
  const card = document.createElement("article");
  card.className = `cue-card${cue.approved ? " reviewed" : ""}`;
  card.dataset.cueId = cue.id;

  const number = document.createElement("div");
  number.className = "cue-number";
  number.textContent = String(cue.index).padStart(2, "0");

  const source = document.createElement("div");
  source.className = "cue-source";
  source.textContent = cue.text;
  const time = document.createElement("span");
  time.className = "cue-time";
  time.textContent = `${formatTime(cue.start_ms)}  →  ${formatTime(cue.end_ms)}`;
  source.append(time);

  const targetWrap = document.createElement("div");
  const target = document.createElement("textarea");
  target.className = "cue-target";
  target.value = cue.target_text;
  target.setAttribute("aria-label", `Target text for cue ${cue.id}`);
  target.addEventListener("focus", startActiveEdit);
  target.addEventListener("blur", stopActiveEdit);
  target.addEventListener("keydown", (event) => {
    if (event.key.length === 1 || ["Backspace", "Delete", "Enter"].includes(event.key)) {
      state.session.keyboardActions += 1;
    }
  });
  const characterCount = document.createElement("div");
  characterCount.className = "char-count";
  characterCount.textContent = `${graphemeCount(cue.target_text)} graphemes`;
  target.addEventListener("input", () => {
    cue.target_text = target.value;
    cue.approved = false;
    state.quality = null;
    state.session.editEvents += 1;
    targetWrap.querySelector(".warning-list")?.remove();
    characterCount.textContent = `${graphemeCount(target.value)} graphemes`;
    card.classList.remove("reviewed");
    checkbox.checked = false;
    updateProgress();
    updateQaSummary();
  });
  targetWrap.append(target, characterCount);
  const protectedValues = state.preparation?.protected_by_cue?.[cue.id] || [];
  if (protectedValues.length) {
    const protectedList = document.createElement("div");
    protectedList.className = "protected-list";
    protectedValues.forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "protected-chip";
      chip.textContent = `${item.kind}: ${item.value}`;
      protectedList.append(chip);
    });
    targetWrap.append(protectedList);
  }
  const qualityWarnings = state.quality?.warnings_by_cue?.[cue.id] || [];
  if (qualityWarnings.length) {
    const warningList = document.createElement("div");
    warningList.className = "warning-list";
    qualityWarnings.forEach((warning) => {
      const chip = document.createElement("div");
      chip.className = `warning-chip ${warning.severity}`;
      chip.textContent = `${warning.code.replaceAll("_", " ")} · ${warning.message}`;
      warningList.append(chip);
    });
    targetWrap.append(warningList);
  }

  const status = document.createElement("div");
  status.className = "cue-status";
  const checkbox = document.createElement("input");
  checkbox.className = "review-check";
  checkbox.type = "checkbox";
  checkbox.checked = Boolean(cue.approved);
  checkbox.id = `review-${cue.index}`;
  const label = document.createElement("label");
  label.htmlFor = checkbox.id;
  label.textContent = "Reviewed";
  checkbox.addEventListener("change", () => {
    cue.approved = checkbox.checked;
    state.session.approvalChanges += 1;
    card.classList.toggle("reviewed", cue.approved);
    updateProgress();
  });
  status.append(checkbox, label);

  card.append(number, source, targetWrap, status);
  return card;
}

function updateProgress() {
  const approved = state.document.cues.filter((cue) => cue.approved).length;
  document.querySelector("#approved-total").textContent = `${approved} / ${state.document.cues.length}`;
}

function updateQaSummary() {
  const summary = document.querySelector("#qa-summary");
  if (!state.quality) {
    summary.textContent = "QA has not been run on this draft.";
    summary.classList.remove("has-warnings");
    return;
  }
  const counts = state.quality.counts;
  summary.textContent = state.quality.total
    ? `${state.quality.total} warning${state.quality.total === 1 ? "" : "s"}: ${counts.high} high · ${counts.medium} medium · ${counts.low} low`
    : "QA passed with no readability or source-timing warnings.";
  summary.classList.toggle("has-warnings", state.quality.total > 0);
}

searchInput.addEventListener("input", () => {
  state.query = searchInput.value;
  renderCues();
});

document.querySelectorAll(".filter-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter-button").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
    renderCues();
  });
});

document.querySelector("#new-file").addEventListener("click", () => {
  state.document = null;
  stopActiveEdit();
  state.session = null;
  fileInput.value = "";
  updateFileChoice(null);
  workspace.hidden = true;
  welcome.hidden = false;
  clearError(workspaceError);
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelector("#prepare-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError(workspaceError);
  const names = document.querySelector("#confirmed-names").value
    .split(",")
    .map((name) => name.trim())
    .filter(Boolean);
  const button = event.currentTarget.querySelector("button[type='submit']");
  const status = document.querySelector("#preparation-status");
  button.disabled = true;
  status.textContent = "Preparing context and protected values...";
  try {
    state.preparation = await postJson("/api/prepare-translation", {
      ...state.document,
      confirmed_names: names,
    });
    status.textContent = `${state.preparation.blocks.length} context block${state.preparation.blocks.length === 1 ? "" : "s"} · ${state.preparation.protected_count} protected value${state.preparation.protected_count === 1 ? "" : "s"}`;
    renderCues();
  } catch (error) {
    status.textContent = "Preparation failed";
    showError(workspaceError, error.message);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#qa-button").addEventListener("click", async () => {
  clearError(workspaceError);
  const button = document.querySelector("#qa-button");
  button.disabled = true;
  button.textContent = "Checking...";
  try {
    state.quality = await postJson("/api/qa", state.document);
    renderCues();
    updateQaSummary();
  } catch (error) {
    showError(workspaceError, error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Run QA";
  }
});

document.querySelector("#report-button").addEventListener("click", async () => {
  clearError(workspaceError);
  const button = document.querySelector("#report-button");
  button.disabled = true;
  button.textContent = "Building...";
  try {
    const report = await postJson("/api/experiment-report", {
      ...state.document,
      filename: state.filename,
      session: sessionPayload(),
      preparation: state.preparation,
      quality: state.quality,
    });
    const stem = state.filename.replace(/\.(srt|vtt|webvtt)$/i, "");
    downloadText(`${JSON.stringify(report, null, 2)}\n`, `${stem}.experiment-report.json`, "application/json;charset=utf-8");
  } catch (error) {
    showError(workspaceError, error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Experiment report";
  }
});

document.querySelector("#export-button").addEventListener("click", async () => {
  clearError(workspaceError);
  const emptyCue = state.document.cues.find((cue) => !cue.target_text.trim());
  if (emptyCue) {
    showError(workspaceError, `Cue ${emptyCue.id} is empty. Add target text before exporting.`);
    return;
  }

  const button = document.querySelector("#export-button");
  button.disabled = true;
  try {
    const result = await postJson("/api/export", state.document);
    const extension = state.document.format === "srt" ? ".srt" : ".vtt";
    const stem = state.filename.replace(/\.(srt|vtt|webvtt)$/i, "");
    downloadText(result.content, `${stem}.reviewed${extension}`, "text/plain;charset=utf-8");
  } catch (error) {
    showError(workspaceError, error.message);
  } finally {
    button.disabled = false;
  }
});
