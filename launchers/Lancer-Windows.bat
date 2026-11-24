@echo off
REM Lanceur Windows NATIF — le texte s'affiche DANS l'application (Internet Explorer / WebBrowser).
REM Ne pas utiliser les scripts .sh / Chrome : c'est uniquement pour Linux+Wine.
cd /d "%~dp0..\..\windows-apps\AstroHoroscope"
if not exist "Astrologie & Horoscope.exe" (
  echo Dossier AstroHoroscope introuvable.
  echo Place ce .bat a cote du pack ou lance "Astrologie & Horoscope.exe" directement.
  pause
  exit /b 1
)
start "" "Astrologie & Horoscope.exe"
