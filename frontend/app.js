/**
 * AudioSense AI – app.js
 * Frontend logic: tab navigation, AI chat, RC filter calculator, noise troubleshooter.
 * All API calls go to the FastAPI backend on the same origin.
 */

const API_BASE = "";   // same-origin; change to "http://localhost:8000" for dev if needed

// ── Utility helpers ────────────────────────────────────────────────────────

function $(id) { return document.getElementById(id); }

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Convert plain text with markdown-like formatting to HTML.
 * Handles **bold**, `code`, numbered lists, bullet lists, and line breaks.
 */
function formatResponse(text) {
  // Escape HTML first
  let html = escapeHtml(text);

  // Code blocks (``` … ```)
  html = html.replace(/```([\s\S]*?)```/g, (_, code) =>
    `<pre>${code.trim()}</pre>`
  );

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // Numbered list items
  html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>");

  // Bullet list items
  html = html.replace(/^[-•]\s+(.+)$/gm, "<li>$1</li>");

  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>[\s\S]*?<\/li>)(\s*<li>)/g, "$1$2");
  html = html.replace(/(<li>)/g, "<ul><li>");
  html = html.replace(/(<\/li>)(?!\s*<li>)/g, "</li></ul>");

  // Paragraph breaks (double newline)
  html = html.split(/\n{2,}/).map(para => {
    para = para.trim();
    if (!para) return "";
    if (para.startsWith("<ul>") || para.startsWith("<pre>")) return para;
    return `<p>${para.replace(/\n/g, "<br>")}</p>`;
  }).join("\n");

  return html || "<p>(No response)</p>";
}

function showError(elementId, message) {
  const el = $(elementId);
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideError(elementId) {
  const el = $(elementId);
  el.textContent = "";
  el.classList.add("hidden");
}

// ── Tab navigation ─────────────────────────────────────────────────────────

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;

    document.querySelectorAll(".tab-btn").forEach(b => {
      b.classList.remove("active");
      b.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    $("panel-" + target).classList.add("active");
  });
});

// ── AI Assistant chat ───────────────────────────────────────────────────────

const chatMessages = $("chat-messages");
const chatInput    = $("chat-input");
const chatSendBtn  = $("chat-send-btn");
const charCount    = $("char-count");

chatInput.addEventListener("input", () => {
  charCount.textContent = chatInput.value.length;
});

// Enter to send (Shift+Enter for newline)
chatInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("chat-form").dispatchEvent(new Event("submit"));
  }
});

// Example question buttons
document.querySelectorAll(".example-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    chatInput.value = btn.dataset.q;
    charCount.textContent = btn.dataset.q.length;
    chatInput.focus();
  });
});

function appendMessage(role, htmlContent, extraClass = "") {
  const avatarText = role === "assistant" ? "AI" : "You";
  const msgClass   = role === "assistant" ? "assistant-message" : "user-message";

  const msgEl = document.createElement("div");
  msgEl.className = `message ${msgClass} ${extraClass}`.trim();
  msgEl.innerHTML = `
    <div class="msg-avatar">${escapeHtml(avatarText)}</div>
    <div class="msg-body">${htmlContent}</div>
  `;
  chatMessages.appendChild(msgEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return msgEl;
}

function removeMessage(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

$("chat-form").addEventListener("submit", async e => {
  e.preventDefault();

  const question = chatInput.value.trim();
  if (!question) return;

  // Show user message
  appendMessage("user", `<p>${escapeHtml(question)}</p>`);

  chatInput.value = "";
  charCount.textContent = "0";
  chatSendBtn.disabled = true;

  // Show thinking indicator
  const thinkingEl = appendMessage(
    "assistant",
    `<span class="dots">Thinking</span>`,
    "thinking-indicator"
  );

  try {
    const res = await fetch(`${API_BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    removeMessage(thinkingEl);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      const detail = errData.detail || "Unknown error from server.";
      appendMessage(
        "assistant",
        `<p><strong>Error ${res.status}:</strong> ${escapeHtml(detail)}</p>`,
        "error-message"
      );
      return;
    }

    const data = await res.json();
    appendMessage("assistant", formatResponse(data.answer));

  } catch (err) {
    removeMessage(thinkingEl);
    appendMessage(
      "assistant",
      `<p><strong>Network error:</strong> Could not reach the server. Make sure the backend is running.</p>`,
      "error-message"
    );
    console.error("AI fetch error:", err);
  } finally {
    chatSendBtn.disabled = false;
    chatInput.focus();
  }
});

// ── RC Filter Calculator ────────────────────────────────────────────────────

$("filter-form").addEventListener("submit", async e => {
  e.preventDefault();
  hideError("filter-form-error");

  const filterType = $("filter-type").value;
  const cutoffFreq = parseFloat($("cutoff-freq").value);
  const resistVal  = $("resistance").value.trim();
  const capVal     = $("capacitance").value.trim();

  // Validation
  if (!cutoffFreq || cutoffFreq <= 0) {
    showError("filter-form-error", "Please enter a valid positive cutoff frequency.");
    return;
  }
  if (!resistVal && !capVal) {
    showError("filter-form-error", "Please enter at least one component value (Resistance or Capacitance).");
    return;
  }

  const payload = {
    filter_type: filterType,
    cutoff_frequency: cutoffFreq,
  };

  if (resistVal) {
    const r = parseFloat(resistVal);
    if (isNaN(r) || r <= 0) {
      showError("filter-form-error", "Resistance must be a positive number.");
      return;
    }
    payload.resistance = r;
  }

  if (capVal) {
    const c = parseFloat(capVal) * 1e-6;  // µF → F
    if (isNaN(c) || c <= 0) {
      showError("filter-form-error", "Capacitance must be a positive number.");
      return;
    }
    payload.capacitance = c;
  }

  const submitBtn = $("filter-submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Calculating…";

  try {
    const res = await fetch(`${API_BASE}/api/filter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      showError("filter-form-error", `Error: ${err.detail || res.statusText}`);
      return;
    }

    const d = await res.json();
    renderFilterResult(d);

  } catch (err) {
    showError("filter-form-error", "Network error — make sure the backend is running.");
    console.error("Filter fetch error:", err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Calculate Filter";
  }
});

function renderFilterResult(d) {
  const container = $("filter-result-content");
  container.innerHTML = `
    <div class="result-row">
      <span class="result-label">Filter Type</span>
      <span class="result-value">${escapeHtml(d.filter_type)} RC Filter</span>
    </div>
    <div class="result-row">
      <span class="result-label">Desired Cutoff Frequency</span>
      <span class="result-value">${d.cutoff_frequency_hz.toLocaleString()} Hz</span>
    </div>
    <div class="result-row">
      <span class="result-label">Actual Cutoff Frequency</span>
      <span class="result-value">${d.actual_cutoff_frequency_hz.toLocaleString(undefined, {maximumFractionDigits:3})} Hz</span>
    </div>
    <div class="result-row">
      <span class="result-label">Resistance (R)</span>
      <span class="result-value">${formatOhms(d.resistance_ohms)}</span>
    </div>
    <div class="result-row">
      <span class="result-label">Capacitance (C, calculated)</span>
      <span class="result-value">${d.capacitance_uf.toFixed(6)} µF</span>
    </div>
    <div class="result-row">
      <span class="result-label">Nearest Standard Capacitor</span>
      <span class="result-value">${d.standard_capacitance_uf} µF (E12 series)</span>
    </div>
    <div class="result-row">
      <span class="result-label">Formula</span>
      <span class="result-value">${escapeHtml(d.formula)}</span>
    </div>
    <div class="result-explanation">${escapeHtml(d.explanation)}</div>
  `;

  const resultCard = $("filter-result");
  resultCard.classList.remove("hidden");
  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function formatOhms(ohms) {
  if (ohms >= 1_000_000) return (ohms / 1_000_000).toPrecision(4) + " MΩ";
  if (ohms >= 1_000)     return (ohms / 1_000).toPrecision(4) + " kΩ";
  return ohms.toPrecision(4) + " Ω";
}

// ── Noise Troubleshooter ────────────────────────────────────────────────────

// Example buttons for noise panel
document.querySelectorAll(".noise-example-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    $("noise-desc").value = btn.dataset.q;
    $("noise-desc").focus();
  });
});

$("noise-form").addEventListener("submit", async e => {
  e.preventDefault();
  hideError("noise-form-error");

  const description = $("noise-desc").value.trim();
  if (!description || description.length < 5) {
    showError("noise-form-error", "Please describe your audio problem (at least 5 characters).");
    return;
  }

  const submitBtn = $("noise-submit-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Diagnosing…";

  try {
    const res = await fetch(`${API_BASE}/api/noise`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      showError("noise-form-error", `Error: ${err.detail || res.statusText}`);
      return;
    }

    const d = await res.json();
    renderNoiseResult(d);

  } catch (err) {
    showError("noise-form-error", "Network error — make sure the backend is running.");
    console.error("Noise fetch error:", err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Diagnose Problem";
  }
});

function renderNoiseResult(d) {
  $("noise-result-title").textContent = "Diagnosis Result";

  const listItems = items => items.map(i => `<li>${escapeHtml(i)}</li>`).join("");

  $("noise-result-content").innerHTML = `
    <div class="noise-type-badge">${escapeHtml(d.noise_type)}</div>

    <div class="noise-section">
      <h4>Possible Causes</h4>
      <ul>${listItems(d.possible_causes)}</ul>
    </div>

    <div class="noise-section">
      <h4>How to Identify</h4>
      <ul>${listItems(d.identification_steps)}</ul>
    </div>

    <div class="noise-section">
      <h4>Solutions</h4>
      <ul>${listItems(d.solutions)}</ul>
    </div>

    <div class="noise-summary">${escapeHtml(d.summary)}</div>
  `;

  const resultCard = $("noise-result");
  resultCard.classList.remove("hidden");
  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
