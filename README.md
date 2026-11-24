# Astro Wine Remaster

Correctifs et lecteur moderne pour **Astrologie & Horoscope** (Windows / Delphi 2003) sous Linux + Wine.

## Problèmes corrigés

| Symptôme | Cause | Correctif |
|---|---|---|
| Zone blanche après Calcul | Wine sans Gecko / `temp.htm#index` | Gecko + viewer web |
| Menu revient toujours sur Calcul du ciel | Scroll ancre cassé sous Wine | Viewer + liste déroulante |
| Imprimer plante (« installez une imprimante ») | Pas de CUPS / PDF | `AstroPDF` + `imprimer-pdf.sh` |
| Horoscope Bélier / Gémeaux vide | Dossiers avec `é` (CP1252 vs UTF-8) | Dossiers ASCII + patch exe |
| `..\astrofic32\` manquant | Casse Linux | Lien `astrofic32 → Astrofic32` |

## Structure

```
viewer/          # UI moderne (portrait + horoscope)
tools/           # fix HTML, export JSON/PDF, watchers
launchers/       # scripts Wine
docs/FIXES.md    # journal technique
```

Les binaires Windows restent à côté :  
`../windows-apps/AstroHoroscope/` (non versionnés s’ils sont trop lourds).

## Démarrage rapide

```bash
# 1) Viewer (recommandé pour lire / PDF)
./serve.sh
# → http://127.0.0.1:8766/viewer/

# 2) Après un calcul dans l’appli Wine :
python3 tools/export_sections.py \
  ../windows-apps/AstroHoroscope/Astrologie/res/temp.htm \
  ../windows-apps/AstroHoroscope/Astrologie/res/sections.json

# 3) Appli Wine
./launchers/lancer-menu.sh      # écran Astrologie / Horoscope
./launchers/lancer-astro.sh     # Astrologie seule
./launchers/imprimer-pdf.sh     # PDF propre
```

## Prérequis Wine

- `wine` + `wine32:i386`
- Wine Gecko 2.47.4 dans `~/.cache/wine/` (installé au 1er usage HTML)
- CUPS + imprimante `AstroPDF` (optionnel pour le bouton Imprimer Wine)

## Licence

Outils / viewer : usage personnel du projet OREAC.  
Les exécutables « Astrologie & Horoscope » restent la propriété de leurs auteurs d’origine.
