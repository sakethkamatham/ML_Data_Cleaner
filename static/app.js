(() => {
  // State
  let state = {
    filepath: null,
    sessionId: null,
  };

  // Elements
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileInfo = document.getElementById("file-info");
  const infoName = document.getElementById("info-name");
  const infoShape = document.getElementById("info-shape");
  const infoCols = document.getElementById("info-cols");

  const sectionConfig = document.getElementById("section-config");
  const sectionLog = document.getElementById("section-log");
  const sectionExport = document.getElementById("section-export");

  const splitRatio = document.getElementById("split-ratio");
  const splitLabel = document.getElementById("split-label");
  const missingThreshold = document.getElementById("missing-threshold");
  const missingLabel = document.getElementById("missing-label");
  const doScale = document.getElementById("do-scale");
  const doEncode = document.getElementById("do-encode");
  const encodeOptions = document.getElementById("encode-options");
  const randomSeed = document.getElementById("random-seed");
  const runBtn = document.getElementById("run-btn");

  const progressBar = document.getElementById("progress-bar");
  const progressStatus = document.getElementById("progress-status");
  const logList = document.getElementById("log-list");

  const dlTrain = document.getElementById("dl-train");
  const dlTest = document.getElementById("dl-test");
  const dlCleaned = document.getElementById("dl-cleaned");
  const resetBtn = document.getElementById("reset-btn");

  // Stat boxes
  const sOrigRows = document.getElementById("s-orig-rows");
  const sCleanRows = document.getElementById("s-clean-rows");
  const sTrainRows = document.getElementById("s-train-rows");
  const sTestRows = document.getElementById("s-test-rows");
  const sOrigCols = document.getElementById("s-orig-cols");
  const sCleanCols = document.getElementById("s-clean-cols");

  // ---- UI Helpers ----

  splitRatio.addEventListener("input", () => {
    splitLabel.textContent = splitRatio.value + "%";
  });

  missingThreshold.addEventListener("input", () => {
    missingLabel.textContent = missingThreshold.value + "%";
  });

  doEncode.addEventListener("change", () => {
    encodeOptions.style.opacity = doEncode.checked ? "1" : "0.3";
    encodeOptions.querySelectorAll("input").forEach(i => (i.disabled = !doEncode.checked));
  });

  // ---- File upload ----

  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
  });

  async function handleFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    runBtn.disabled = true;
    infoName.textContent = "Uploading…";
    fileInfo.classList.remove("hidden");
    sectionConfig.classList.add("hidden");

    try {
      const res = await fetch("/upload", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Upload failed.");
        fileInfo.classList.add("hidden");
        return;
      }

      state.filepath = data.filepath;
      infoName.textContent = "📄 " + data.filename;
      infoShape.textContent = `${data.rows.toLocaleString()} rows`;
      infoCols.textContent = `${data.cols} columns`;

      sectionConfig.classList.remove("hidden");
      runBtn.disabled = false;
    } catch (e) {
      alert("Network error during upload.");
      fileInfo.classList.add("hidden");
    }
  }

  // ---- Run pipeline ----

  runBtn.addEventListener("click", async () => {
    if (!state.filepath) return;

    const encodeStrategy = document.querySelector('input[name="encode-strategy"]:checked')?.value || "label";

    const config = {
      filepath: state.filepath,
      test_size: parseInt(splitRatio.value) / 100,
      missing_col_threshold: parseInt(missingThreshold.value) / 100,
      do_scale: doScale.checked,
      do_encode: doEncode.checked,
      encode_strategy: encodeStrategy,
      random_state: parseInt(randomSeed.value) || 42,
    };

    // Prepare log section
    logList.innerHTML = "";
    progressBar.style.width = "0%";
    progressStatus.textContent = "Running pipeline…";
    sectionLog.classList.remove("hidden");
    sectionExport.classList.add("hidden");
    runBtn.disabled = true;
    sectionLog.scrollIntoView({ behavior: "smooth", block: "start" });

    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      const data = await res.json();

      if (!res.ok) {
        progressStatus.textContent = "Error: " + (data.error || "Pipeline failed.");
        runBtn.disabled = false;
        return;
      }

      state.sessionId = data.session_id;

      // Animate log entries
      const total = data.log_entries.length;
      for (let i = 0; i < total; i++) {
        await new Promise(r => setTimeout(r, 280));
        appendLogEntry(data.log_entries[i]);
        const pct = Math.round(((i + 1) / total) * 100);
        progressBar.style.width = pct + "%";
        progressStatus.textContent = `Step ${i + 1} of ${total} complete`;
      }

      progressStatus.textContent = "All steps complete.";
      renderExport(data);
      sectionExport.classList.remove("hidden");
      sectionExport.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      progressStatus.textContent = "Network error. Please try again.";
    } finally {
      runBtn.disabled = false;
    }
  });

  function appendLogEntry(entry) {
    const isSkipped = entry.detail.startsWith("Skipped");
    const div = document.createElement("div");
    div.className = "log-entry " + (isSkipped ? "skipped" : "done");

    const rowDiff = entry.rows_after - entry.rows_before;
    const colDiff = entry.cols_after - entry.cols_before;
    const rowStr = rowDiff !== 0 ? ` (${rowDiff > 0 ? "+" : ""}${rowDiff} rows)` : "";
    const colStr = colDiff !== 0 ? ` (${colDiff > 0 ? "+" : ""}${colDiff} cols)` : "";

    div.innerHTML = `
      <div class="log-step ${isSkipped ? "skipped" : "done"}">${isSkipped ? "⏭" : "✓"} ${entry.step}</div>
      <div class="log-meta">
        Rows: ${entry.rows_before.toLocaleString()} → ${entry.rows_after.toLocaleString()}${rowStr} &nbsp;|&nbsp;
        Cols: ${entry.cols_before} → ${entry.cols_after}${colStr}
      </div>
      <div class="log-detail">${entry.detail}</div>
    `;
    logList.appendChild(div);
    div.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ---- Export section ----

  function renderExport(data) {
    sOrigRows.textContent = data.original_rows.toLocaleString();
    sCleanRows.textContent = data.cleaned_rows.toLocaleString();
    sTrainRows.textContent = data.train_rows.toLocaleString();
    sTestRows.textContent = data.test_rows.toLocaleString();
    sOrigCols.textContent = data.original_cols;
    sCleanCols.textContent = data.cleaned_cols;

    renderStatsTable(data.summary_stats);

    dlTrain.disabled = false;
    dlTest.disabled = false;
    dlCleaned.disabled = false;
  }

  function renderStatsTable(stats) {
    const head = document.getElementById("stats-head");
    const body = document.getElementById("stats-body");
    head.innerHTML = "";
    body.innerHTML = "";

    const cols = Object.keys(stats);
    if (!cols.length) return;

    const rows = Object.keys(stats[cols[0]]);

    // Header
    const thStat = document.createElement("th");
    thStat.textContent = "Statistic";
    head.appendChild(thStat);
    cols.forEach(c => {
      const th = document.createElement("th");
      th.textContent = c;
      head.appendChild(th);
    });

    // Rows
    rows.forEach(row => {
      const tr = document.createElement("tr");
      const tdLabel = document.createElement("td");
      tdLabel.textContent = row;
      tr.appendChild(tdLabel);
      cols.forEach(c => {
        const td = document.createElement("td");
        const val = stats[c][row];
        td.textContent = (val !== null && val !== undefined) ? Number(val).toLocaleString(undefined, { maximumFractionDigits: 4 }) : "—";
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  }

  // ---- Download buttons ----

  function downloadFile(filetype) {
    if (!state.sessionId) return;
    window.location.href = `/download/${state.sessionId}/${filetype}`;
  }

  dlTrain.addEventListener("click", () => downloadFile("train"));
  dlTest.addEventListener("click", () => downloadFile("test"));
  dlCleaned.addEventListener("click", () => downloadFile("cleaned"));

  // ---- Reset ----

  resetBtn.addEventListener("click", () => {
    state = { filepath: null, sessionId: null };
    fileInput.value = "";
    fileInfo.classList.add("hidden");
    sectionConfig.classList.add("hidden");
    sectionLog.classList.add("hidden");
    sectionExport.classList.add("hidden");
    logList.innerHTML = "";
    progressBar.style.width = "0%";
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
})();
