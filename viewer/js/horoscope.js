const SIGNS = [
  { id: "01_Belier", label: "Bélier", exe: "Horoscope_01.exe" },
  { id: "02_Taureau", label: "Taureau", exe: "Horoscope_02.exe" },
  { id: "03_Gemeaux", label: "Gémeaux", exe: "Horoscope_03.exe" },
  { id: "04_Cancer", label: "Cancer", exe: "Horoscope_04.exe" },
  { id: "05_Lion", label: "Lion", exe: "Horoscope_05.exe" },
  { id: "06_Vierge", label: "Vierge", exe: "Horoscope_06.exe" },
  { id: "07_Balance", label: "Balance", exe: "Horoscope_07.exe" },
  { id: "08_Scorpion", label: "Scorpion", exe: "Horoscope_08.exe" },
  { id: "09_Sagittaire", label: "Sagittaire", exe: "Horoscope_09.exe" },
  { id: "10_Capricorne", label: "Capricorne", exe: "Horoscope_10.exe" },
  { id: "11_Verseau", label: "Verseau", exe: "Horoscope_11.exe" },
  { id: "12_Poissons", label: "Poissons", exe: "Horoscope_12.exe" },
];

const ROOT_CANDIDATES = [
  "../../windows-apps/AstroHoroscope/Horoscope",
  "../../../windows-apps/AstroHoroscope/Horoscope",
];

function $(s) {
  return document.querySelector(s);
}

function decodeHtmlBytes(buf) {
  const u8 = new Uint8Array(buf);
  const tryEnc = ["utf-8", "windows-1252", "iso-8859-1"];
  for (const enc of tryEnc) {
    try {
      return new TextDecoder(enc, { fatal: false }).decode(u8);
    } catch (_) {}
  }
  return new TextDecoder().decode(u8);
}

async function fetchText(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(String(res.status));
  const buf = await res.arrayBuffer();
  return decodeHtmlBytes(buf);
}

function preferFiles(names) {
  const rank = (n) => {
    const x = n.toLowerCase();
    if (x.includes("horoscopejour")) return 0;
    if (x.includes("tendance")) return 1;
    if (x.includes("signe")) return 2;
    if (x.startsWith("horo_part")) return 3;
    return 9;
  };
  return [...names].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}

async function listHtm(signId) {
  // No directory listing over static file server reliably → probe known names
  const known = [
    "HoroscopeJour.htm",
    "TendanceMois.htm",
    "Signe.htm",
    "Horo_part_1.htm",
    "Horo_part_2.htm",
    "Horo_part_3.htm",
    "Horo_part_4.htm",
    "Horo_part_5.htm",
    "Horo_part_6.htm",
    "print_grille.htm",
  ];
  const found = [];
  for (const root of ROOT_CANDIDATES) {
    for (const name of known) {
      const url = `${root}/${signId}/Res_Txt/${name}`;
      try {
        const res = await fetch(url, { method: "HEAD", cache: "no-store" });
        if (res.ok) found.push({ root, name, url });
      } catch (_) {}
    }
    if (found.length) return found;
  }
  return found;
}

function wire() {
  const signSel = $("#sign");
  SIGNS.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.id;
    o.textContent = s.label;
    signSel.appendChild(o);
  });

  signSel.addEventListener("change", () => loadSign(signSel.value));
  $("#file").addEventListener("change", async (e) => {
    const url = e.target.value;
    if (!url) return;
    try {
      const html = await fetchText(url);
      $("#docBody").innerHTML = html
        .replace(/<link[^>]*>/gi, "")
        .replace(/background="[^"]*"/gi, "");
      $("#docMeta").textContent = url;
    } catch (err) {
      $("#docBody").innerHTML = `<div class="empty">Impossible de lire le fichier.<br>${err}</div>`;
    }
  });

  $("#btnOpenWine").addEventListener("click", () => {
    const s = SIGNS.find((x) => x.id === signSel.value);
    alert(
      `Dans un terminal :\n\ncd ~/Documents/Astrologie/windows-apps/AstroHoroscope/Horoscope/${s.id}\nWINEPREFIX=~/.wine-astro wine ${s.exe}`
    );
  });

  loadSign(SIGNS[0].id);
}

async function loadSign(signId) {
  $("#docTitle").textContent = SIGNS.find((s) => s.id === signId)?.label || signId;
  $("#file").innerHTML = "";
  $("#docBody").innerHTML = '<div class="empty">Chargement…</div>';
  const files = await listHtm(signId);
  if (!files.length) {
    $("#docBody").innerHTML =
      '<div class="empty">Aucun HTML trouvé. Démarre le serveur local du projet (<code>./serve.sh</code>).</div>';
    return;
  }
  const ordered = preferFiles(files.map((f) => f.name));
  const byName = Object.fromEntries(files.map((f) => [f.name, f]));
  ordered.forEach((name) => {
    const o = document.createElement("option");
    o.value = byName[name].url;
    o.textContent = name;
    $("#file").appendChild(o);
  });
  $("#file").value = byName[ordered[0]].url;
  $("#file").dispatchEvent(new Event("change"));
}

wire();
