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
~/Documents/Astrologie/windows-apps/lancer-astro.sh
# si le HTML ne s'affiche pas dans l'app :
~/Documents/Astrologie/windows-apps/voir-portrait.sh
```

## Navigation sommaire / scroll / PDF (2026-11-24)
- Cause menu : l'exe navigue toujours vers `temp.htm#index` ; sous Wine le scroll vers IndexN échoue → on retombe sur Calcul du ciel.
- Correctif : `tools/fix_temp_htm.py` injecte un **SOMMAIRE cliquable** + scroll CSS/JS dans `temp.htm` (watcher auto au lancement).
- PDF propre : `./exporter-pdf.sh` (Chromium headless) → `Astrologie/res/portrait.pdf` au lieu de l'imprimante Wine.
