const FIELDS = ["vendor", "invoice_date", "invoice_no", "net", "vat", "gross", "currency"];
const LABELS = {
  vendor: "Lieferant",
  invoice_date: "Datum",
  invoice_no: "Nummer",
  net: "Netto",
  vat: "MwSt",
  gross: "Brutto",
  currency: "Währung",
};
const NUMERIC = new Set(["net", "vat", "gross"]);

const rowsEl = document.getElementById("rows");
const emptyEl = document.getElementById("empty");
const errorEl = document.getElementById("error");
const statsEl = document.getElementById("stats");
const hintEl = document.getElementById("hint");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
  setTimeout(() => { errorEl.hidden = true; }, 8000);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_) { /* not json */ }
    throw new Error(detail);
  }
  return response.headers.get("content-type")?.includes("json")
    ? response.json()
    : response.text();
}

function fmt(value) {
  if (value === null || value === undefined || value === "") return "";
  return typeof value === "number"
    ? value.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : String(value);
}

function renderStats(stats) {
  statsEl.innerHTML = `
    <span>Rechnungen <b>${stats.total}</b></span>
    <span>vollständig <b>${stats.complete}</b></span>
    <span>unvollständig <b>${stats.with_missing_fields}</b></span>
    <span>Tesseract <b style="color:${stats.tesseract_ready ? "var(--ok)" : "var(--danger)"}">
      ${stats.tesseract_ready ? "bereit" : "fehlt"}</b></span>`;
}

function makeCell(row, field) {
  const td = document.createElement("td");
  const value = row[field];
  const missing = value === null || value === "" || value === undefined;
  td.className = "cell" + (missing ? " missing" : "") + (NUMERIC.has(field) ? " num" : "");
  td.textContent = fmt(value) || (missing ? "" : "");
  td.title = missing ? "Feld fehlt — klicken zum Ergänzen" : "Klicken zum Bearbeiten";

  td.addEventListener("click", () => {
    if (td.querySelector("input")) return;
    const input = document.createElement("input");
    input.value = value ?? "";
    input.type = NUMERIC.has(field) ? "number" : "text";
    if (NUMERIC.has(field)) input.step = "0.01";
    td.textContent = "";
    td.appendChild(input);
    input.focus();
    input.select();

    const commit = async () => {
      const raw = input.value.trim();
      try {
        await api(`/api/invoices/${row.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [field]: raw === "" ? null : raw }),
        });
        await load();
      } catch (error) {
        showError(error.message);
        await load();
      }
    };

    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") commit();
      if (event.key === "Escape") load();
    });
    input.addEventListener("blur", () => {
      if (td.contains(input)) commit();
    });
  });

  return td;
}

function makeActions(row) {
  const td = document.createElement("td");
  td.className = "act";

  if (row.has_file) {
    const link = document.createElement("a");
    link.className = "link";
    link.href = `/api/files/${row.id}`;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "Original";
    td.appendChild(link);
  }

  const remove = document.createElement("button");
  remove.className = "danger";
  remove.textContent = "Löschen";
  let armed = false;
  remove.addEventListener("click", async () => {
    if (!armed) {
      armed = true;
      remove.classList.add("armed");
      remove.textContent = "Sicher?";
      setTimeout(() => {
        armed = false;
        remove.classList.remove("armed");
        remove.textContent = "Löschen";
      }, 4000);
      return;
    }
    try {
      await api(`/api/invoices/${row.id}`, { method: "DELETE" });
      await load();
    } catch (error) {
      showError(error.message);
    }
  });
  td.appendChild(remove);
  return td;
}

function renderRows(invoices) {
  rowsEl.innerHTML = "";
  emptyEl.hidden = invoices.length > 0;

  for (const row of invoices) {
    const tr = document.createElement("tr");
    for (const field of FIELDS) tr.appendChild(makeCell(row, field));
    tr.appendChild(makeActions(row));
    rowsEl.appendChild(tr);
  }
}

async function load() {
  const [data, stats] = await Promise.all([api("/api/invoices"), api("/api/stats")]);
  renderRows(data.invoices);
  renderStats(stats);
}

async function upload(file) {
  const body = new FormData();
  body.append("file", file);
  hintEl.textContent = "Scanne… kann bei großen PDFs einige Sekunden dauern.";
  try {
    const result = await api("/api/scan", { method: "POST", body });
    hintEl.textContent = `Fertig: ${result.found}/7 Felder erkannt.`;
    await load();
  } catch (error) {
    hintEl.textContent = "Klick auf eine Zelle, um sie zu korrigieren.";
    showError(error.message);
  }
}

async function loadSettings() {
  const options = await api("/api/settings");
  document.getElementById("opt-lang").value = options.lang;
  document.getElementById("opt-dpi").value = String(options.dpi);
  document.getElementById("opt-cmd").value = options.tesseract_cmd;
  document.getElementById("opt-keep").checked = options.keep_original;
}

document.getElementById("file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) upload(file);
  event.target.value = "";
});

document.getElementById("toggle-settings").addEventListener("click", (event) => {
  const panel = document.getElementById("settings");
  panel.hidden = !panel.hidden;
  event.currentTarget.setAttribute("aria-expanded", String(!panel.hidden));
});

document.getElementById("save-settings").addEventListener("click", async () => {
  try {
    await api("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lang: document.getElementById("opt-lang").value,
        dpi: Number(document.getElementById("opt-dpi").value),
        tesseract_cmd: document.getElementById("opt-cmd").value,
        keep_original: document.getElementById("opt-keep").checked,
      }),
    });
    hintEl.textContent = "Optionen gespeichert.";
    await load();
  } catch (error) {
    showError(error.message);
  }
});

loadSettings().catch((error) => showError(error.message));
load().catch((error) => showError(error.message));
