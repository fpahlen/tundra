/* Tundra interview UI */

let session = null;

const $ = (id) => document.getElementById(id);

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("text/yaml") || ct.includes("text/plain")) {
    return res;
  }
  return res.json();
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Safe light markdown: paragraphs, breaks, bold/italic, unordered lists. */
function renderLightMarkdown(text) {
  const raw = String(text || "").replace(/\r\n/g, "\n").trim();
  if (!raw) return "";

  const blocks = raw.split(/\n{2,}/);
  const html = [];

  for (const block of blocks) {
    const lines = block.split("\n");
    let para = [];
    let list = [];

    const flushPara = () => {
      if (!para.length) return;
      const body = inlineMd(escapeHtml(para.join("\n")).replace(/\n/g, "<br>"));
      html.push(`<p>${body}</p>`);
      para = [];
    };
    const flushList = () => {
      if (!list.length) return;
      const items = list
        .map((item) => `<li>${inlineMd(escapeHtml(item))}</li>`)
        .join("");
      html.push(`<ul>${items}</ul>`);
      list = [];
    };

    for (const line of lines) {
      const m = line.match(/^\s*[-*]\s+(.*)$/);
      if (m) {
        flushPara();
        list.push(m[1]);
      } else {
        flushList();
        para.push(line);
      }
    }
    flushList();
    flushPara();
  }
  return html.join("");
}

function inlineMd(escaped) {
  // **bold** first, then single-asterisk *italic* (avoid eating **)
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
}

function renderMessages(messages) {
  const el = $("messages");
  el.innerHTML = "";
  for (const m of messages || []) {
    if (m.role === "system") continue;
    const div = document.createElement("div");
    div.className = `msg ${m.role === "author" ? "author" : "facilitator"}`;
    div.innerHTML = renderLightMarkdown(m.content);
    el.appendChild(div);
  }
  el.scrollTop = el.scrollHeight;
}

/** Highlight YAML list items that contain source: inferred (assumed rules). */
function renderDraft(yamlText) {
  const el = $("draft");
  if (!yamlText) {
    el.textContent = "// No draft yet.";
    return;
  }
  const lines = String(yamlText).replace(/\r\n/g, "\n").split("\n");
  const highlight = new Set();
  const sourceRe = /^\s*source:\s*inferred\b/i;
  const listItemRe = /^\s*-\s/;

  for (let i = 0; i < lines.length; i++) {
    if (!sourceRe.test(lines[i])) continue;
    highlight.add(i);
    for (let j = i - 1; j >= 0; j--) {
      highlight.add(j);
      if (listItemRe.test(lines[j])) break;
      // stop if we leave the object (dedent past nested keys without list start)
      if (lines[j].trim() === "") break;
    }
  }

  el.innerHTML = lines
    .map((line, i) => {
      const cls = highlight.has(i) ? "draft-line inferred" : "draft-line";
      const empty = line.length === 0 ? " " : line;
      return `<span class="${cls}">${escapeHtml(empty)}</span>`;
    })
    .join("\n");
}

function renderChecklist(items) {
  const ul = $("checklist");
  ul.innerHTML = "";
  if (!items || !items.length) {
    ul.innerHTML = "<li class='soft'>Start a session and produce a draft.</li>";
    return;
  }
  for (const it of items) {
    const li = document.createElement("li");
    const mark = document.createElement("span");
    mark.className =
      "mark " + (it.ok ? "ok" : it.blocking ? "bad" : "soft");
    mark.textContent = it.ok ? "✓" : "✗";
    const label = document.createElement("span");
    label.textContent =
      it.label + (it.detail ? ` — ${it.detail}` : "");
    li.appendChild(mark);
    li.appendChild(label);
    ul.appendChild(li);
  }
}

function renderReport(v) {
  const el = $("report");
  if (!v) {
    el.textContent = "No report yet.";
    return;
  }
  const lines = [];
  lines.push(v.ok ? "Structural: OK" : "Structural: FAIL");
  for (const e of v.errors || []) lines.push("error: " + e);
  for (const w of v.warnings || []) lines.push("warning: " + w);
  el.textContent = lines.join("\n");
}

function applySession(s) {
  session = s;
  $("session-badge").textContent = `session: ${s.session_state}`;
  $("draft-badge").textContent = `draft: ${s.draft_state}`;
  $("draft-badge").className =
    "badge " +
    (s.draft_state === "Structurally valid" || s.draft_state === "Domain ready"
      ? "ok"
      : s.draft_state === "Structurally invalid"
        ? "bad"
        : "");
  renderMessages(s.messages);
  renderDraft(s.draft_yaml);
  renderChecklist(s.checklist);
  renderReport(s.last_validation);
  const hasDraft = Boolean(s.draft_yaml);
  $("validate-btn").disabled = !hasDraft || s.session_state === "Abandoned";
  $("export-btn").disabled = !s.export_allowed;
  $("snapshot-btn").disabled = !s.id;
  $("abandon-btn").disabled = s.session_state === "Abandoned";
  $("send-btn").disabled = s.session_state === "Abandoned";
}

async function newSession() {
  const s = await api("/api/sessions", { method: "POST", body: "{}" });
  applySession(s);
}

async function sendChat(text) {
  if (!session) await newSession();
  $("send-btn").disabled = true;
  try {
    const s = await api(`/api/sessions/${session.id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });
    applySession(s);
  } finally {
    $("send-btn").disabled = false;
  }
}

$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("input").value.trim();
  if (!text) return;
  $("input").value = "";
  try {
    await sendChat(text);
  } catch (err) {
    alert(err.message);
  }
});

$("new-btn").addEventListener("click", () => {
  newSession().catch((e) => alert(e.message));
});

$("validate-btn").addEventListener("click", async () => {
  if (!session) return;
  try {
    const data = await api(`/api/sessions/${session.id}/validate`, {
      method: "POST",
      body: "{}",
    });
    applySession(data.session);
  } catch (err) {
    alert(err.message);
  }
});

$("export-btn").addEventListener("click", async () => {
  if (!session) return;
  try {
    const res = await api(`/api/sessions/${session.id}/export`, {
      method: "POST",
      body: "{}",
    });
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const m = /filename="([^"]+)"/.exec(cd);
    const name = m ? m[1] : "model.tundra";
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
    // refresh session state (exported)
    const s = await api(`/api/sessions/${session.id}`);
    applySession(s);
  } catch (err) {
    alert(err.message);
  }
});

$("snapshot-btn").addEventListener("click", async () => {
  if (!session) return;
  try {
    const res = await fetch(`/api/sessions/${session.id}/snapshot`);
    if (!res.ok) throw new Error(await res.text());
    // Also confirm file path for the user
    alert(
      "Snapshot written for the coding agent:\n" +
        "web/debug/last-session.md\n\n" +
        "(Also available at GET /api/debug/last)"
    );
  } catch (err) {
    alert(err.message);
  }
});

$("abandon-btn").addEventListener("click", async () => {
  if (!session) return;
  try {
    const s = await api(`/api/sessions/${session.id}/abandon`, {
      method: "POST",
      body: "{}",
    });
    applySession(s);
  } catch (err) {
    alert(err.message);
  }
});

// boot
api("/api/health")
  .then((h) => {
    $("llm-mode").textContent = h.llm === "live" ? "LLM: live" : "LLM: demo";
    $("llm-mode").className = "badge " + (h.llm === "live" ? "ok" : "");
  })
  .catch(() => {
    $("llm-mode").textContent = "API down";
    $("llm-mode").className = "badge bad";
  });

newSession().catch((e) => {
  $("messages").textContent = "Failed to start session: " + e.message;
});
