(function () {
  const API_BASE = "http://127.0.0.1:5055";
  const DEFAULT_STAGE = "10% Deposit";
  const PROJECT_CODE_RE = /\b[A-Z]{1,3}\d{2,4}\b/;

  let stages = [DEFAULT_STAGE];
  let activePopover = null;

  function text(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function api(path, options) {
    return fetch(`${API_BASE}${path}`, options).then(async (response) => {
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || "The local invoice helper is not responding.");
      }
      return payload;
    });
  }

  function setStatus(message, mode) {
    let status = document.querySelector("#acadia-invoice-status");
    if (!status) {
      status = document.createElement("div");
      status.id = "acadia-invoice-status";
      status.setAttribute("aria-live", "polite");
      document.documentElement.appendChild(status);
    }

    status.textContent = message || "";
    status.dataset.mode = mode || "";

    if (message) {
      clearTimeout(setStatus.timer);
      setStatus.timer = setTimeout(() => {
        status.textContent = "";
        status.dataset.mode = "";
      }, mode === "error" ? 9000 : 5000);
    }
  }

  function cleanProjectQuery(value) {
    return text(value)
      .replace(/^(project|job|code|name)\s*[:#-]\s*/i, "")
      .slice(0, 160);
  }

  function projectQueryFromText(value) {
    const clean = cleanProjectQuery(value);
    const codeMatch = clean.match(PROJECT_CODE_RE);
    if (!codeMatch) return clean;

    const code = codeMatch[0];
    const afterCode = clean.slice(codeMatch.index + code.length);
    const title = afterCode
      .split(/\b(?:CV|DRAWING|PROPOSAL|PROJECT INFO|Name:|Manager:|Customer:|Location:|Due Date:|clear info)\b/i)[0]
      .replace(/^[\s:-]+/, "")
      .trim();

    return title ? `${code} ${title}` : code;
  }

  function visibleElement(element) {
    if (!(element instanceof HTMLElement)) return false;
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      Number(style.opacity) !== 0
    );
  }

  function findOpenProjectPanel() {
    const headings = Array.from(document.querySelectorAll("div, span, h1, h2, h3"))
      .filter(visibleElement)
      .filter((element) => PROJECT_CODE_RE.test(text(element.textContent)));

    for (const heading of headings) {
      const panel = heading.closest('[role="dialog"], .modal, .ant-modal, .MuiDialog-root, section, article');
      if (panel && text(panel.innerText).includes("ACTIONS:")) return panel;
    }

    return Array.from(document.querySelectorAll('[role="dialog"], .modal, .ant-modal, .MuiDialog-root, section, article'))
      .filter(visibleElement)
      .find((element) => PROJECT_CODE_RE.test(text(element.innerText)) && text(element.innerText).includes("ACTIONS:"));
  }

  function visibleProjectHeaderQuery() {
    const candidates = Array.from(document.querySelectorAll("div, span, h1, h2, h3"))
      .filter(visibleElement)
      .map((element) => {
        const rect = element.getBoundingClientRect();
        const value = projectQueryFromText(element.innerText || element.textContent);
        return { element, rect, value };
      })
      .filter(({ rect, value }) => {
        return (
          PROJECT_CODE_RE.test(value) &&
          rect.top >= 35 &&
          rect.top <= 230 &&
          rect.left >= 180 &&
          rect.width >= 25
        );
      })
      .sort((a, b) => {
        const aHasTitle = a.value.replace(PROJECT_CODE_RE, "").trim().length > 2 ? 0 : 1;
        const bHasTitle = b.value.replace(PROJECT_CODE_RE, "").trim().length > 2 ? 0 : 1;
        return aHasTitle - bHasTitle || a.rect.top - b.rect.top || a.rect.left - b.rect.left;
      });

    for (const { element, value } of candidates) {
      if (value.replace(PROJECT_CODE_RE, "").trim().length > 2) {
        return value;
      }

      const parentLines = String(element.parentElement && element.parentElement.innerText ? element.parentElement.innerText : "")
        .split(/\n+/)
        .map(cleanProjectQuery)
        .filter(Boolean);
      const codeIndex = parentLines.findIndex((line) => PROJECT_CODE_RE.test(line));
      const nextLine = parentLines[codeIndex + 1] || "";
      if (codeIndex >= 0 && nextLine && !PROJECT_CODE_RE.test(nextLine)) {
        return projectQueryFromText(`${parentLines[codeIndex]} ${nextLine}`);
      }
    }

    return "";
  }

  function currentProjectQuery() {
    const headerQuery = visibleProjectHeaderQuery();
    if (headerQuery) return headerQuery;

    const panel = findOpenProjectPanel();
    const source = document.body || panel;
    const lines = String(source && source.innerText ? source.innerText : "")
      .split(/\n+/)
      .map(cleanProjectQuery)
      .filter(Boolean);
    const projectLineIndex = lines.findIndex((line) => PROJECT_CODE_RE.test(line));
    if (projectLineIndex >= 0) {
      const projectLine = lines[projectLineIndex];
      const codeOnly = projectLine.match(PROJECT_CODE_RE) && projectLine.replace(PROJECT_CODE_RE, "").trim().length === 0;
      const nextLine = lines[projectLineIndex + 1] || "";
      const nextLineLooksLikeTitle =
        nextLine &&
        !["DRAWING", "PROPOSAL", "QB:", "ACTIONS:", "DOCUSIGN:", "CABINETS:", "MATERIALS:"].includes(nextLine.toUpperCase());

      if (codeOnly && nextLineLooksLikeTitle) {
        return projectQueryFromText(`${projectLine} ${nextLine}`);
      }
      return projectQueryFromText(projectLine);
    }

    const panelText = text(panel && panel.innerText);
    const code = panelText.match(PROJECT_CODE_RE);
    return code ? code[0] : "";
  }

  function findTargetLabels() {
    const panel = findOpenProjectPanel();
    if (!panel) return [];

    const labels = Array.from(panel.querySelectorAll("div, span, label, strong, b, p, h1, h2, h3, h4"))
      .filter(visibleElement)
      .filter((element) => ["QB:", "ACTIONS:"].includes(text(element.textContent).toUpperCase()));

    const qbLabels = labels.filter((element) => text(element.textContent).toUpperCase() === "QB:");
    return qbLabels.length ? qbLabels : labels;
  }

  async function loadStages() {
    try {
      const payload = await api("/api/stages");
      if (Array.isArray(payload.stages) && payload.stages.length) {
        stages = payload.stages;
      }
    } catch {
      setStatus("Start the local invoice helper first.", "error");
    }
  }

  function closePopover() {
    if (activePopover) {
      activePopover.remove();
      activePopover = null;
    }
  }

  function buildStageOptions(selectedStage) {
    return stages
      .map((stage) => {
        const selected = stage === selectedStage ? " selected" : "";
        return `<option value="${escapeHtml(stage)}"${selected}>${escapeHtml(stage)}</option>`;
      })
      .join("");
  }

  function showPopover(anchor) {
    closePopover();

    const projectQuery = currentProjectQuery();
    const popover = document.createElement("div");
    popover.id = "acadia-invoice-popover";
    popover.innerHTML = `
      <div class="acadia-invoice-popover-title">${escapeHtml(projectQuery || "Current project")}</div>
      <select class="acadia-invoice-popover-stage" aria-label="Invoice stage">
        ${buildStageOptions(DEFAULT_STAGE)}
      </select>
      <div class="acadia-invoice-popover-actions">
        <button type="button" class="acadia-invoice-cancel">Cancel</button>
        <button type="button" class="acadia-invoice-send">Open draft</button>
      </div>
    `;

    const rect = anchor.getBoundingClientRect();
    popover.style.left = `${Math.max(10, Math.min(rect.left, window.innerWidth - 280))}px`;
    popover.style.top = `${Math.max(10, Math.min(rect.bottom + 6, window.innerHeight - 150))}px`;

    popover.querySelector(".acadia-invoice-cancel").addEventListener("click", closePopover);
    popover.querySelector(".acadia-invoice-send").addEventListener("click", async () => {
      const stage = popover.querySelector(".acadia-invoice-popover-stage").value;
      await createDraft(projectQuery, stage, anchor);
    });

    document.documentElement.appendChild(popover);
    activePopover = popover;
  }

  async function createDraft(projectQuery, stage, button) {
    const query = cleanProjectQuery(projectQuery);
    if (!query) {
      setStatus("Could not read the project code from the opened project.", "error");
      return;
    }

    try {
      closePopover();
      button.disabled = true;
      button.textContent = "Opening...";
      setStatus(`Searching Dropbox for ${query}...`, "working");

      const payload = await api("/api/create-draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_query: query,
          stage,
          page_url: window.location.href,
          page_title: document.title
        })
      });

      setStatus(`Outlook draft opened: ${payload.stage} - ${payload.project_name}`, "success");
    } catch (error) {
      setStatus(error.message || "Could not create the Outlook draft.", "error");
    } finally {
      button.disabled = false;
      button.textContent = "Invoice Request";
    }
  }

  function addProjectPanelButton(label) {
    const parent = label.parentElement;
    if (!parent || parent.querySelector(".acadia-invoice-actions-button")) return;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "acadia-invoice-actions-button";
    button.textContent = "Invoice Request";
    button.title = "Create invoice email draft";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      showPopover(button);
    });

    label.insertAdjacentElement("afterend", button);
  }

  function removeBoardButtons() {
    document
      .querySelectorAll(".acadia-invoice-card-button, #acadia-invoice-global, #acadia-invoice-loaded-marker")
      .forEach((element) => element.remove());
  }

  function scan() {
    removeBoardButtons();
    for (const label of findTargetLabels()) {
      addProjectPanelButton(label);
    }
  }

  function mount() {
    loadStages().finally(scan);

    const observer = new MutationObserver(() => {
      clearTimeout(scan.timer);
      scan.timer = setTimeout(scan, 250);
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true
    });

    document.addEventListener("click", (event) => {
      if (activePopover && !event.target.closest("#acadia-invoice-popover")) {
        closePopover();
      }
    });
  }

  mount();
})();
