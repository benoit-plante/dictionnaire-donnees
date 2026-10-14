@echo off
rem Installs or updates the tool for this user, without administrator rights.
rem The work is done by windows\installer.ps1 (see docs/installation-windows.md).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\installer.ps1"
