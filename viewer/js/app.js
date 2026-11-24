const DEFAULT_SECTIONS_URLS = [
  "../../windows-apps/AstroHoroscope/Astrologie/res/sections.json",
  "../data/sections.json",
  "./data/sections.json",
];

function $(sel, root = document) {
  return root.querySelector(sel);
}

function setStatus(msg) {
  const el = $("#status");
  if (el) el.textContent = msg || "";
}

async function loadSections() {
  const custom = new URLSearchParams(location.search).get("src");
  const urls = custom ? [custom, ...DEFAULT_SECTIONS_URLS] : DEFAULT_SECTIONS_URLS;
  for (const url of urls) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) continue;
      const data = await res.json();
      if (data && Array.isArray(data.sections)) return { data, url };
    } catch (_) {}
  }
  return null;
}

function renderNav(sections) {
  const sel = $("#jump");
  const list = $("#navList");
  if (!sel || !list) return;
  sel.innerHTML = '<option value="">Aller à une rubrique…</option>';
  list.innerHTML = "";
  sections.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = String(s.id);
    opt.textContent = s.label;
    sel.appendChild(opt);

    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = s.label;
    btn.dataset.id = String(s.id);
    btn.addEventListener("click", () => goSection(s.id));
    li.appendChild(btn);
    list.appendChild(li);
  });
}

function renderBody(data) {
  const head = $("#docTitle");
  const meta = $("#docMeta");
  const body = $("#docBody");
  head.textContent = data.title || "Portrait astral";
  meta.textContent = `${data.sections.length} rubriques`;
  body.innerHTML = "";
  data.sections.forEach((s) => {
    const card = document.createElement("section");
    card.className = "section-card";
    card.id = `sec-${s.id}`;
    const h = document.createElement("h2");
    h.textContent = s.label;
    card.appendChild(h);
    const content = document.createElement("div");
    // Prefer cleaned HTML fragment when safe-ish; else text
    if (s.html && s.html.length < 200000) {
      content.innerHTML = s.html
        .replace(/background="[^"]*"/gi, "")
        .replace(/<a name="[^"]*"[^>]*>\s*<\/a>/gi, "");
    } else {
      content.innerHTML = `<pre style="white-space:pre-wrap;font:inherit">${escapeHtml(
        s.text || ""
      )}</pre>`;
    }
    card.appendChild(content);
    body.appendChild(card);
  });
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function goSection(id) {
  const el = document.getElementById(`sec-${id}`);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
  $("#jump").value = String(id);
  document.querySelectorAll("#navList button").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === String(id));
  });
}

function wire() {
  $("#jump")?.addEventListener("change", (e) => {
    if (e.target.value !== "") goSection(e.target.value);
  });
  $("#btnPrev")?.addEventListener("click", () => step(-1));
  $("#btnNext")?.addEventListener("click", () => step(1));
  $("#btnPrint")?.addEventListener("click", () => window.print());
}

function step(dir) {
  const buttons = [...document.querySelectorAll("#navList button")];
  if (!buttons.length) return;
  const cur = buttons.findIndex((b) => b.classList.contains("active"));
  const next = Math.max(0, Math.min(buttons.length - 1, (cur < 0 ? 0 : cur) + dir));
  goSection(buttons[next].dataset.id);
}

async function main() {
  wire();
  setStatus("Chargement du portrait…");
  const loaded = await loadSections();
  if (!loaded) {
    setStatus("Aucun portrait trouvé. Lance un calcul dans Astrologie, puis régénère sections.json.");
    $("#docBody").innerHTML =
      '<div class="empty">Pas de données.<br>Exécute <code>tools/export_sections.py</code> après un calcul.</div>';
    return;
  }
  renderNav(loaded.data.sections);
  renderBody(loaded.data);
  setStatus(`Source : ${loaded.url}`);
  if (loaded.data.sections[0]) goSection(loaded.data.sections[0].id);
}

main();
