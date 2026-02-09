/* Public APIs Tracker */

let apis = [];
let filtered = [];
let sortKey = "name";
let sortAsc = true;

async function init() {
  const res = await fetch("data/apis.json");
  apis = await res.json();
  populateCategories();
  applyFilters();
  updateSortIndicators();
  initDetailListeners();
}

function populateCategories() {
  const select = document.getElementById("filter-category");
  const categories = [...new Set(apis.map((a) => a.category))].sort();
  for (const cat of categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    select.appendChild(opt);
  }
}

function applyFilters() {
  const search = document.getElementById("search").value.toLowerCase();
  const cat = document.getElementById("filter-category").value;
  const auth = document.getElementById("filter-auth").value;
  const status = document.getElementById("filter-status").value;

  filtered = apis.filter((a) => {
    if (
      search &&
      !a.name.toLowerCase().includes(search) &&
      !a.description.toLowerCase().includes(search)
    )
      return false;
    if (cat && a.category !== cat) return false;
    if (auth && a.auth !== auth) return false;
    if (status && a.status !== status) return false;
    return true;
  });

  sortFiltered();
  renderTable();
  renderStats();
}

function sortFiltered() {
  filtered.sort((a, b) => {
    const va = a[sortKey] || "";
    const vb = b[sortKey] || "";
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  });
}

function renderTable() {
  const tbody = document.getElementById("api-list");

  if (filtered.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="5" class="empty-state">No APIs match the current filters.</td></tr>';
    document.getElementById("result-count").textContent =
      `Showing 0 of ${apis.length} APIs`;
    return;
  }

  const rows = filtered
    .map((a, i) => {
      const notesHtml = a.notes
        ? `<span class="notes-icon" title="${escapeAttr(a.notes)}">&#9998;</span>`
        : "";
      return `<tr class="api-row" data-index="${i}">
      <td><a href="${escapeAttr(a.url)}" target="_blank" rel="noopener">${escapeHtml(a.name)}</a>${notesHtml}</td>
      <td>${escapeHtml(a.description)}</td>
      <td>${a.auth}</td>
      <td>${a.category}</td>
      <td><span class="badge badge-${a.status}">${a.status}</span></td>
    </tr>`;
    })
    .join("");

  tbody.innerHTML = rows;
  document.getElementById("result-count").textContent =
    `Showing ${filtered.length} of ${apis.length} APIs`;
}

const statusOrder = [
  "working",
  "broken",
  "needs-key",
  "paid-only",
  "pending",
  "skipped",
];

function renderStats() {
  const counts = {};
  for (const a of apis) {
    counts[a.status] = (counts[a.status] || 0) + 1;
  }

  const el = document.getElementById("stats");
  el.innerHTML = statusOrder
    .filter((s) => counts[s])
    .map(
      (status) =>
        `<span class="stat"><span class="stat-dot stat-dot-${status}"></span><span class="stat-label">${status}</span> <span class="stat-count">${counts[status]}</span></span>`,
    )
    .join("");
}

/* Detail row: expand/collapse on click */

function buildDetailHTML(api) {
  let html = '<div class="detail-panel">';

  if (api.notes) {
    html += `<p class="detail-notes">${escapeHtml(api.notes)}</p>`;
  }

  if (api["try-it"]) {
    const tryIt = api["try-it"];
    html += '<div class="try-it-section">';

    if (tryIt.params) {
      html += '<div class="try-it-params">';
      for (const [key, defaultVal] of Object.entries(tryIt.params)) {
        html += `<label>${escapeHtml(key)}: <input type="text" class="try-it-input" data-param="${escapeAttr(key)}" value="${escapeAttr(defaultVal)}"></label>`;
      }
      html += "</div>";
    }

    html += `<div class="try-it-controls">
      <code class="try-it-url">${escapeHtml(resolveUrl(tryIt.url, tryIt.params))}</code>
      <button class="try-it-btn" data-url="${escapeAttr(tryIt.url)}" data-response-type="${tryIt["response-type"]}">Try It</button>
    </div>`;

    html += '<div class="try-it-response"></div>';
    html += "</div>";
  }

  html += "</div>";
  return html;
}

function resolveUrl(urlTemplate, params) {
  if (!params) return urlTemplate;
  let url = urlTemplate;
  for (const [key, val] of Object.entries(params)) {
    url = url.replace(`{${key}}`, val);
  }
  return url;
}

function initDetailListeners() {
  const tbody = document.getElementById("api-list");

  // Row expand/collapse
  tbody.addEventListener("click", (e) => {
    if (e.target.closest("a, button, input, .try-it-section")) return;
    const row = e.target.closest("tr.api-row");
    if (!row) return;

    const existing = row.nextElementSibling;
    if (existing && existing.classList.contains("detail-row")) {
      existing.remove();
      row.classList.remove("expanded");
      return;
    }

    const api = filtered[parseInt(row.dataset.index)];
    const detailRow = document.createElement("tr");
    detailRow.className = "detail-row";
    const td = document.createElement("td");
    td.colSpan = 5;
    td.innerHTML = buildDetailHTML(api);
    detailRow.appendChild(td);
    row.after(detailRow);
    row.classList.add("expanded");
  });

  // Try It button
  tbody.addEventListener("click", async (e) => {
    const btn = e.target.closest(".try-it-btn");
    if (!btn) return;

    const section = btn.closest(".try-it-section");
    const responseEl = section.querySelector(".try-it-response");
    const responseType = btn.dataset.responseType;
    let url = btn.dataset.url;

    // Substitute params
    section.querySelectorAll(".try-it-input").forEach((input) => {
      url = url.replace(
        `{${input.dataset.param}}`,
        encodeURIComponent(input.value),
      );
    });

    // Image: use <img> directly (bypasses CORS)
    if (responseType === "image") {
      responseEl.innerHTML = '<p class="try-it-loading">Loading image...</p>';
      const img = document.createElement("img");
      img.className = "try-it-image";
      img.alt = "API response";
      img.onload = () => {
        responseEl.innerHTML = "";
        responseEl.appendChild(img);
      };
      img.onerror = () => {
        responseEl.innerHTML =
          '<p class="try-it-error">Failed to load image.</p>';
      };
      img.src = url;
      return;
    }

    // JSON/text: use fetch
    responseEl.innerHTML = '<p class="try-it-loading">Fetching...</p>';
    btn.disabled = true;

    try {
      const res = await fetch(url);
      if (!res.ok) {
        responseEl.innerHTML = `<p class="try-it-error">HTTP ${res.status} ${res.statusText}</p>`;
        return;
      }
      if (responseType === "json") {
        const data = await res.json();
        responseEl.innerHTML = `<pre class="try-it-json">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
      } else {
        const text = await res.text();
        responseEl.innerHTML = `<pre class="try-it-json">${escapeHtml(text)}</pre>`;
      }
    } catch (err) {
      responseEl.innerHTML = `<p class="try-it-error">CORS blocked — this API doesn't allow browser requests.<br>Try: <code>curl ${escapeHtml(url)}</code></p>`;
    } finally {
      btn.disabled = false;
    }
  });

  // Live URL preview update on param input
  tbody.addEventListener("input", (e) => {
    if (!e.target.classList.contains("try-it-input")) return;
    const section = e.target.closest(".try-it-section");
    const btn = section.querySelector(".try-it-btn");
    let url = btn.dataset.url;
    section.querySelectorAll(".try-it-input").forEach((input) => {
      url = url.replace(`{${input.dataset.param}}`, input.value);
    });
    section.querySelector(".try-it-url").textContent = url;
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Event listeners
document.getElementById("search").addEventListener("input", applyFilters);
document
  .getElementById("filter-category")
  .addEventListener("change", applyFilters);
document
  .getElementById("filter-auth")
  .addEventListener("change", applyFilters);
document
  .getElementById("filter-status")
  .addEventListener("change", applyFilters);

// Column sorting
document.querySelectorAll("thead th[data-sort]").forEach((th) => {
  th.addEventListener("click", () => {
    const key = th.dataset.sort;
    if (sortKey === key) {
      sortAsc = !sortAsc;
    } else {
      sortKey = key;
      sortAsc = true;
    }
    updateSortIndicators();
    sortFiltered();
    renderTable();
  });
});

function updateSortIndicators() {
  document.querySelectorAll("thead th[data-sort]").forEach((th) => {
    th.classList.toggle("sorted", th.dataset.sort === sortKey);
    if (th.dataset.sort === sortKey) {
      th.dataset.sortDir = sortAsc ? "asc" : "desc";
    } else {
      delete th.dataset.sortDir;
    }
  });
}

init();
