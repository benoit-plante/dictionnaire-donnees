@echo off
rem Uninstalls the tool for this user; project files and data are not touched.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows\desinstaller.ps1"
