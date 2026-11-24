# Astrologie & Horoscope — correctifs Wine (v-fix)

## Diagnostic
1. Calcul OK : génère `Astrologie/res/temp.htm` (portrait complet).
2. Affichage vide + popup `Erreur lors de la navigation dans le fichier html...`
   → TWebBrowser (IE) sous Wine sans **Gecko**.
3. Chemin `Astrologie & Horoscope` (espace + `&`) casse parfois les URL `file://`.

## Correctifs appliqués
- Wine32 + winetricks installés
- Wine Gecko 2.47.4 installé dans `~/.wine-astro`
- Copie app sans `&` : `windows-apps/AstroHoroscope/`
- Lien `Astrologie/astrofic32` → données villes/éphémérides
- Lanceurs : `lancer-astro.sh`, `lancer-menu.sh`, `voir-portrait.sh`

## Lancer
```bash
~/Documents/Astrologie/astro-wine-remaster/launchers/lancer-menu.sh
# si le HTML ne s'affiche pas dans l'app :
~/Documents/Astrologie/astro-wine-remaster/launchers/voir-portrait.sh
~/Documents/Astrologie/astro-wine-remaster/launchers/voir-horoscope.sh
```

## Horoscope = cadre noir / rien (2026-11-24)
- Cause : TWebBrowser (Shell Embedding) reste **1×1** ou noir ; Wine `allocate_virtual_memory` OOM en 32-bit (surtout avec 2× `Horoscope_*.exe`).
- Le texte est bien écrit dans `Horoscope/*/Res_Txt/temp.rtf` → converti en `temp.htm`.
- Sous **Linux/Wine** : `voir-horoscope.sh` (Chrome/Firefox). `ASTRO_OPEN_BROWSER=1` pour ouvrir auto.
- Sous **Windows réel** : IE/WebBrowser natif → le texte s’affiche **dans l’app** (`Lancer-Windows.bat`). Pas besoin de Chrome.

## App qui se ferme au clic (2026-11-24)
- Cause : plusieurs instances Wine du **mauvais dossier** `Astrologie & Horoscope` (accents) + IE qui OOM → tout le process meurt.
- Correctif : une seule session via `astro-wine-remaster/launchers/lancer-menu.sh` → dossier `AstroHoroscope` (ASCII). `wineserver -k` au relance.

## Portrait : trait de défilement + fermeture Horoscope (2026-11-24)
- `fix_temp_htm.py` v3 : barre droite avec **thumb tirable** (comme une scrollbar) + nav ▲▼.
- Fermer Horoscope / OREAC → le watcher **réactive le menu** « Choisir Astrologie ou Horoscope ».
- Tag GitHub : `v0.3-oreac-horoscope-viewer`.

## Navigation sommaire / scroll / PDF (2026-11-24)
- Cause menu : l'exe navigue toujours vers `temp.htm#index` ; sous Wine le scroll vers IndexN échoue → on retombe sur Calcul du ciel.
- Correctif : `tools/fix_temp_htm.py` injecte un **SOMMAIRE cliquable** + scroll CSS/JS dans `temp.htm` (watcher auto au lancement).
- PDF propre : `./exporter-pdf.sh` (Chromium headless) → `Astrologie/res/portrait.pdf` au lieu de l'imprimante Wine.
