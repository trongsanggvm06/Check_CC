// ===== TAB SWITCHING =====
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(target).classList.add("active");
  });
});

// ===== COPY HELPER =====
async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    btn.classList.add("copied");
    btn.textContent = "Đã copy!";
    setTimeout(() => {
      btn.classList.remove("copied");
      btn.textContent = "📋 Copy";
    }, 1500);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    btn.classList.add("copied");
    btn.textContent = "Đã copy!";
    setTimeout(() => {
      btn.classList.remove("copied");
      btn.textContent = "📋 Copy";
    }, 1500);
  }
}

// ===== BUILD RESULT CARD (3 platform: PC, iPhone, Android) =====
function buildCard(data, index = null) {
  const card = document.createElement("div");

  if (data.ok) {
    card.className = "result-card success";
    const indexBadge = index !== null ? `<span class="badge badge-index">#${index}</span>` : "";

    const pcUrl = data.pc || data.url;
    const iosUrl = data.ios || data.pc || data.url;
    const androidUrl = data.mobile;

    const linksHtml = `
      <div class="link-platform">
        <div class="link-platform-header">
          <span class="link-platform-icon">💻</span>
          <span class="link-platform-name">PC / Web / Ipad</span>
          <span class="badge badge-ok">OK</span>
        </div>
        <div class="link-row">
          <span class="link-label">https</span>
          <a class="link-url" href="${pcUrl}" target="_blank" title="${pcUrl}">${pcUrl}</a>
          <button class="btn btn-sm btn-copy" data-copy-text="${pcUrl}">📋 Copy</button>
        </div>
      </div>
      <div class="link-platform">
        <div class="link-platform-header">
          <span class="link-platform-icon">📱</span>
          <span class="link-platform-name">iPhone</span>
          <span class="badge badge-ok">OK</span>
        </div>
        <div class="link-row">
          <span class="link-label">https</span>
          <a class="link-url" href="${iosUrl}" target="_blank" title="${iosUrl}">${iosUrl}</a>
          <button class="btn btn-sm btn-copy" data-copy-text="${iosUrl}">📋 Copy</button>
        </div>
      </div>
      <div class="link-platform">
        <div class="link-platform-header">
          <span class="link-platform-icon">🤖</span>
          <span class="link-platform-name">Android</span>
          <span class="badge badge-ok">OK</span>
        </div>
        <div class="link-row">
          <span class="link-label">https</span>
          <a class="link-url" href="${androidUrl}" target="_blank" title="${androidUrl}">${androidUrl}</a>
          <button class="btn btn-sm btn-copy" data-copy-text="${androidUrl}">📋 Copy</button>
        </div>
      </div>
    `;

    card.innerHTML = `
      <div class="result-header">
        ${indexBadge}
        <span class="badge badge-ok">✓ Thành công</span>
      </div>
      ${linksHtml}
      <div class="expiry-row">
        <span class="expiry-left">⚠️ Token sống: <span class="countdown" data-ts="${data.expires_ts || 0}">--:--</span></span>
        <div class="copy-quota" data-count="0">
          <span class="cq-label">Đã copy</span>
          <span class="cq-pips"><i></i><i></i><i></i><i></i></span>
          <b class="cq-num">0/4</b>
        </div>
      </div>
    `;

    // Countdown timer
    const countdownEl = card.querySelector(".countdown");
    if (countdownEl) {
      const expiresTs = parseInt(countdownEl.dataset.ts, 10);
      if (expiresTs > 0) {
        const tick = () => {
          const now = Date.now();
          const remaining = Math.max(0, Math.floor((expiresTs - now) / 1000));
          if (remaining <= 0) {
            countdownEl.textContent = "Hết hạn";
            countdownEl.style.color = "#ff5252";
            return;
          }
          const m = Math.floor(remaining / 60);
          const s = remaining % 60;
          countdownEl.textContent = `${m}:${String(s).padStart(2, "0")}`;
          if (remaining <= 60) countdownEl.style.color = "#ff5252";
          setTimeout(tick, 1000);
        };
        setTimeout(tick, 1000);
      } else {
        countdownEl.textContent = "59:00";
      }
    }

    // Copy counter
    const quota = card.querySelector(".copy-quota");
    const pips = quota ? quota.querySelectorAll(".cq-pips i") : [];
    const numEl = quota ? quota.querySelector(".cq-num") : null;
    const copyBtns = card.querySelectorAll(".btn-copy");
    const COUNTER_MAX = 4;
    let count = 0;
    const updateCounter = () => {
      if (quota) {
        quota.setAttribute("data-count", String(count));
        pips.forEach((p, i) => p.classList.toggle("on", i < count));
        if (numEl) numEl.textContent = `${count}/${COUNTER_MAX}`;
        quota.classList.toggle("warn", count === COUNTER_MAX - 1);
        if (count >= COUNTER_MAX) {
          quota.classList.add("done");
          quota.innerHTML = `🔄 Hết lượt — đổi link mới`;
        }
      }
      if (count >= COUNTER_MAX) {
        copyBtns.forEach(b => {
          b.disabled = true;
          b.classList.add("copy-disabled");
        });
      }
    };
    copyBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        if (count >= COUNTER_MAX) return;
        copyText(btn.dataset.copyText, btn);
        count += 1;
        updateCounter();
      });
    });
  } else {
    card.className = "result-card error-card";
    const indexBadge = index !== null ? `<span class="badge badge-index">#${index}</span>` : "";
    const debugJson = data.debug ? JSON.stringify(data.debug, null, 2) : "";
    card.innerHTML = `
      <div class="result-header">
        ${indexBadge}
        <span class="badge badge-fail">✗ Thất bại</span>
      </div>
      <div class="error-msg">❌ ${data.error}</div>
      ${debugJson ? `
        <details style="margin-top:10px;">
          <summary style="cursor:pointer;color:var(--text-muted);font-size:.8rem;user-select:none;">
            🔍 Debug log — click để mở
          </summary>
          <pre style="margin-top:8px;background:var(--card2);border:1px solid var(--border);border-radius:var(--radius);padding:12px;font-size:.72rem;color:var(--text);overflow:auto;max-height:300px;white-space:pre-wrap;word-break:break-all;">${debugJson.replace(/</g, "&lt;")}</pre>
        </details>
      ` : ""}
    `;
  }

  return card;
}

// ===== SINGLE MODE =====
const singleForm = document.getElementById("single-form");
const singleInput = document.getElementById("single-input");
const singleBtn = document.getElementById("single-btn");
const singleSpinner = document.getElementById("single-spinner");
const singleResults = document.getElementById("single-results");

document.getElementById("clear-single").addEventListener("click", () => {
  singleInput.value = "";
  singleResults.innerHTML = '<div class="empty-state"><div class="icon">🎬</div>Kết quả sẽ hiện ở đây</div>';
});

function switchToBatchWith(rawCookies) {
  document.querySelector('[data-tab="tab-batch"]').click();
  batchInput.value = rawCookies;
  setTimeout(() => batchInput.scrollIntoView({ behavior: "smooth", block: "center" }), 50);
}

singleForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const raw = singleInput.value.trim();
    if (!raw) return;

    singleBtn.disabled = true;
    singleSpinner.style.display = "inline-block";
    singleResults.innerHTML = "";

    const autoRefresh = document.getElementById("opt-refresh").checked;

    try {
        const resp = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cookies: raw, auto_refresh: autoRefresh }),
        });
        const data = await resp.json();
        const card = buildCard(data);

        if (!data.ok && data.suggest_tab === "tab-batch") {
            const switchBtn = document.createElement("button");
            switchBtn.className = "btn-retry";
            switchBtn.style.borderColor = "var(--primary)";
            switchBtn.style.color = "var(--primary)";
            switchBtn.textContent = `📦 Chuyển sang tab Batch (${data.count} cookie)`;
            switchBtn.onclick = () => switchToBatchWith(raw);
            card.appendChild(switchBtn);
        }

        singleResults.appendChild(card);
    } catch {
        singleResults.innerHTML = '<div class="result-card error-card"><div class="error-msg">❌ Lỗi kết nối đến server</div></div>';
    } finally {
        singleBtn.disabled = false;
        singleSpinner.style.display = "none";
    }
});

// ===== CHECK COOKIE MODE (PROGRESSIVE) — dùng /api/generate cho từng cookie =====
const batchForm = document.getElementById("batch-form");
const batchInput = document.getElementById("batch-input");
const batchBtn = document.getElementById("batch-btn");
const batchSpinner = document.getElementById("batch-spinner");
const batchResults = document.getElementById("batch-results");
const lifeResults = document.getElementById("life-results");
const dieResults = document.getElementById("die-results");
const lifeCount = document.getElementById("life-count");
const dieCount = document.getElementById("die-count");
const batchStats = document.getElementById("batch-stats");
const downloadLifeBtn = document.getElementById("download-life");
const downloadDieBtn = document.getElementById("download-die");
const stopBtn = document.getElementById("stop-batch");
const progressWrap = document.getElementById("batch-progress-wrap");
const progressText = document.getElementById("batch-progress-text");
const progressPercent = document.getElementById("batch-progress-percent");
const progressFill = document.getElementById("batch-progress-fill");

const THROTTLE_MS = 300;
let cancelRequested = false;
let batchRun = {
  total: 0,
  processed: 0,
  cancelled: false,
  results: new Map(),
};

function resetBatchResults() {
  lifeResults.innerHTML = '<div class="group-empty">Chưa có cookie LIFE</div>';
  dieResults.innerHTML = '<div class="group-empty">Chưa có cookie DIE</div>';
  batchRun = {
    total: 0,
    processed: 0,
    cancelled: false,
    results: new Map(),
  };
  updateBatchResultCounters();
  updateDownloadButtons();
  batchStats.style.display = "none";
  progressWrap.style.display = "none";
  progressFill.classList.remove("done");
  progressFill.style.width = "0%";
  progressPercent.textContent = "0%";
}

function addGroupEmptyMessage(group, message, isError = false) {
  const empty = document.createElement("div");
  empty.className = isError ? "group-empty batch-error" : "group-empty";
  empty.textContent = message;
  group.appendChild(empty);
}

function moveCardToGroup(card, status) {
  const target = status === "life" ? lifeResults : dieResults;
  const existingEmpty = target.querySelector(".group-empty");
  if (existingEmpty) existingEmpty.remove();
  target.appendChild(card);
  card.dataset.status = status;
  updateBatchResultCounters();
}

function getBatchCounts() {
  let life = 0;
  let die = 0;
  batchRun.results.forEach((record) => {
    if (record.data.ok) life += 1;
    else die += 1;
  });
  return { life, die };
}

function updateBatchResultCounters() {
  const { life, die } = getBatchCounts();
  lifeCount.textContent = String(life);
  dieCount.textContent = String(die);

  [lifeResults, dieResults].forEach((group) => {
    if (!group.children.length) {
      const empty = document.createElement("div");
      empty.className = "group-empty";
      empty.textContent = group === lifeResults ? "Chưa có cookie LIFE" : "Chưa có cookie DIE";
      group.appendChild(empty);
    }
  });
}

function updateDownloadButtons() {
  const { life, die } = getBatchCounts();
  downloadLifeBtn.disabled = life === 0;
  downloadDieBtn.disabled = die === 0;
  downloadLifeBtn.textContent = `Tải LIFE (.txt) · ${life}`;
  downloadDieBtn.textContent = `Tải DIE (.txt) · ${die}`;
}

function renderBatchStats() {
  const { life, die } = getBatchCounts();

  const counts = batchStats.querySelector(".batch-counts");
  counts.innerHTML = `
    <span>Tổng: <strong>${batchRun.total}</strong></span>
    <span>LIFE: <span class="ok">${life}</span></span>
    <span>DIE: <span class="fail">${die}</span></span>
    <span>Đã xử lý: <strong>${batchRun.processed}</strong></span>
    ${batchRun.cancelled ? `<span>Chưa xử lý: <strong>${batchRun.total - batchRun.processed}</strong></span>` : ""}
  `;
  batchStats.style.display = "flex";
}

function registerBatchResult(data, index, raw = null) {
  const record = { data, index };
  if (raw !== null) record.raw = raw;
  batchRun.results.set(index, record);
  updateBatchResultCounters();
  updateDownloadButtons();
  renderBatchStats();
}

document.getElementById("clear-batch").addEventListener("click", () => {
  cancelRequested = true;
  batchRun.cancelled = true;
  batchInput.value = "";
  resetBatchResults();
});

stopBtn.addEventListener("click", () => {
  cancelRequested = true;
  stopBtn.disabled = true;
  stopBtn.textContent = "Đang dừng...";
});

function setProgress(done, total) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  progressFill.style.width = pct + "%";
  progressPercent.textContent = pct + "%";
  progressText.textContent = `Đang xử lý ${done}/${total}...`;
  if (done >= total) {
    progressText.textContent = `Hoàn tất ${done}/${total}`;
    progressFill.classList.add("done");
  }
}

function buildPendingCard(index) {
  const card = document.createElement("div");
  card.className = "result-card pending";
  card.id = `card-pending-${index}`;
  card.dataset.index = index;
  card.dataset.status = "pending";
  card.innerHTML = `
    <div class="result-header">
      <span class="badge badge-index">#${index}</span>
      <div class="pending-label">
        <div class="mini-spinner"></div>
        Đang kiểm tra...
      </div>
    </div>
  `;
  return card;
}

function buildRetryButton(rawBlock, index, autoRefresh) {
  const btn = document.createElement("button");
  btn.className = "btn-retry";
  btn.textContent = "🔄 Thử lại";
  btn.onclick = async () => {
    btn.disabled = true;
    btn.textContent = "Đang thử lại...";
    const data = await callGenerate(rawBlock, autoRefresh);
    data.index = index;
    registerBatchResult(data, index, rawBlock);

    const newCard = buildCard(data, index);
    newCard.dataset.index = index;
    const status = data.ok ? "life" : "die";
    if (!data.ok) {
      newCard.appendChild(buildRetryButton(rawBlock, index, autoRefresh));
    }

    const oldCard = document.querySelector(`#batch-results .result-card[data-index="${index}"]`);
    if (oldCard) oldCard.remove();
    moveCardToGroup(newCard, status);
  };
  return btn;
}

async function callGenerate(rawBlock, autoRefresh) {
  try {
    const resp = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookies: rawBlock, auto_refresh: autoRefresh }),
    });

    const contentType = resp.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
      const text = await resp.text();
      return {
        ok: false,
        error: `Server trả về phản hồi không hợp lệ (HTTP ${resp.status})`,
        debug_preview: text.slice(0, 200),
      };
    }

    const data = await resp.json();
    if (!resp.ok) {
      return {
        ok: false,
        error: data?.error || `HTTP ${resp.status}`,
        debug: data?.debug,
      };
    }
    return data;
  } catch (err) {
    return { ok: false, error: err?.message || "Lỗi kết nối đến server" };
  }
}

async function fetchAccountInfo(rawBlock) {
  try {
    const resp = await fetch("/api/account-info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookies: rawBlock }),
    });
    const data = await resp.json();
    if (!data || data.ok === false) return null;
    return { next_payment: data.next_payment, plan: data.plan };
  } catch {
    return null;
  }
}

function downloadTextFile(filename, content) {
  if (!content) return;
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function buildLifeRecord(record) {
  const raw = (record.raw || "").trim();
  const profile = record.profile;
  const next = profile && profile.next_payment ? profile.next_payment : "N/A";
  const plan = profile && profile.plan ? profile.plan : "N/A";
  return `COOKIE = ${raw} | Next Payment = ${next} | Plan = ${plan}`;
}

function getLifeExport() {
  return [...batchRun.results.values()]
    .filter((record) => record.data.ok)
    .sort((a, b) => a.index - b.index)
    .map(buildLifeRecord)
    .join("\n\n");
}

function getDieExport() {
  return [...batchRun.results.values()]
    .filter((record) => !record.data.ok)
    .sort((a, b) => a.index - b.index)
    .map((record) => `COOKIE = ${(record.raw || "").trim()}`)
    .join("\n\n");
}

downloadLifeBtn.addEventListener("click", () => downloadTextFile("life.txt", getLifeExport()));
downloadDieBtn.addEventListener("click", () => downloadTextFile("die.txt", getDieExport()));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

batchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const raw = batchInput.value.trim();
  if (!raw) return;

  cancelRequested = false;
  batchBtn.disabled = true;
  batchSpinner.style.display = "inline-block";
  stopBtn.style.display = "inline-block";
  stopBtn.disabled = false;
  stopBtn.textContent = "⏹ Dừng";
  resetBatchResults();
  const autoRefreshBatch = document.getElementById("opt-refresh-batch").checked;

  let blocks = [];
  try {
    const splitResp = await fetch("/api/split", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookies: raw }),
    });
    const splitData = await splitResp.json();
    if (!splitData.ok || !splitData.blocks?.length) {
      addGroupEmptyMessage(lifeResults, splitData.error || "Không tách được block cookie", true);
      throw new Error("split failed");
    }
    blocks = splitData.blocks;
  } catch (err) {
    if (err.message !== "split failed") {
      addGroupEmptyMessage(lifeResults, "Lỗi kết nối đến server (split)", true);
    }
    batchBtn.disabled = false;
    batchSpinner.style.display = "none";
    stopBtn.style.display = "none";
    return;
  }

  const total = blocks.length;
  batchRun.total = total;
  progressWrap.style.display = "block";
  setProgress(0, total);

  blocks.forEach((block, i) => {
    const index = i + 1;
    const card = buildPendingCard(index);
    moveCardToGroup(card, "life");
    card.dataset.raw = block;
  });

  for (let i = 0; i < blocks.length; i++) {
    if (cancelRequested) break;

    const block = blocks[i];
    const idx = i + 1;
    const data = await callGenerate(block, autoRefreshBatch);
    data.index = idx;

    let profile = null;
    if (data.ok) {
      profile = await fetchAccountInfo(block);
    }

    batchRun.results.set(idx, { data, index: idx, raw: block, profile });
    batchRun.processed += 1;

    const newCard = buildCard(data, idx);
    newCard.dataset.index = idx;
    if (!data.ok) {
      newCard.appendChild(buildRetryButton(block, idx, autoRefreshBatch));
    }

    const pendingCard = document.getElementById(`card-pending-${idx}`);
    if (pendingCard) pendingCard.remove();
    moveCardToGroup(newCard, data.ok ? "life" : "die");

    updateBatchResultCounters();
    updateDownloadButtons();
    renderBatchStats();
    setProgress(batchRun.processed, total);

    if (i < blocks.length - 1 && !cancelRequested) {
      await sleep(THROTTLE_MS);
    }
  }

  if (cancelRequested) {
    batchRun.cancelled = true;
    document.querySelectorAll("#batch-results .result-card.pending").forEach((card) => card.remove());
    progressText.textContent = `Đã dừng — xử lý ${batchRun.processed}/${total}`;
  }

  updateBatchResultCounters();
  updateDownloadButtons();
  renderBatchStats();

  batchBtn.disabled = false;
  batchSpinner.style.display = "none";
  stopBtn.style.display = "none";
});
