# Installs or updates the tool for the current user, without administrator rights (D-021).
# Started by installer.bat, at the root of the tool's archive.
#
# It:
#   1. installs uv (Python manager, astral.sh) when missing, in the user's folder;
#   2. installs the tool with its options (AI, interface), or updates it;
#   3. creates the "Dictionnaire de données" icon in the Start menu and on the desktop.
# The AI needs no installation: an API key, typed on the tool's "IA" page (v0.18, D-135).
# Internet is needed during the installation; afterwards the tool uses it only for the AI,
# for a project that allows it, and never sends a participant's data (D-134).
#
# For trials: -ShortcutDir (one folder instead of the Start menu and the desktop; PATH is
# then left alone) and -NoPrompt (ask nothing).

param(
    [string]$ShortcutDir = "",
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ShortcutName = "Dictionnaire de données.lnk"

function Say([string]$Text) { Write-Host $Text }

function Step([string]$Text) { Write-Host ""; Write-Host $Text -ForegroundColor Cyan }

function Ask([string]$Question) {
    if ($NoPrompt) { return $false }
    $answer = Read-Host "$Question (o/n)"
    return $answer -match "^\s*[oOyY]"
}

function Finish([int]$Code) {
    if (-not $NoPrompt) { Write-Host ""; Read-Host "Appuyez sur Entrée pour fermer cette fenêtre" | Out-Null }
    exit $Code
}

function Fail([string]$Text) {
    Write-Host ""
    Write-Host $Text -ForegroundColor Red
    Say "Notez ce message et transmettez-le à la personne qui vous a fourni l'outil."
    Finish 1
}

Say "Installation de l'outil Dictionnaire de données"
Say "Dossier de l'outil : $Root"
if (-not (Test-Path (Join-Path $Root "pyproject.toml"))) {
    Fail "Ce dossier ne contient pas l'outil (pyproject.toml manque). Lancez installer.bat depuis le dossier de l'outil décompressé."
}

# --- 1. uv ---------------------------------------------------------------------------
Step "1/3 - uv, le gestionnaire de Python"
$uv = $null
$found = Get-Command uv -ErrorAction SilentlyContinue
if ($found) { $uv = $found.Source }
$local = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
if (-not $uv -and (Test-Path $local)) { $uv = $local }
if ($uv) {
    Say "Déjà installé : $uv"
} else {
    Say "Installation de uv depuis astral.sh (dans votre dossier d'utilisateur)..."
    try {
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    } catch {
        Fail "uv n'a pas pu être installé : $($_.Exception.Message). Vérifiez la connexion Internet, puis relancez installer.bat."
    }
    if (-not (Test-Path $local)) {
        Fail "uv n'a pas pu être installé. Vérifiez la connexion Internet, puis relancez installer.bat."
    }
    $uv = $local
}

# --- 2. L'outil ------------------------------------------------------------------------
Step "2/3 - L'outil (une ou deux minutes la première fois)"
# An open tool locks its own files: updating it then fails half-way and leaves it broken
# (found by the trial of 0.4.0). Ask to close it first.
$toolDir = Join-Path (& $uv tool dir).Trim() "ddict"
$toolExe = Join-Path (& $uv tool dir --bin).Trim() "ddict.exe"
$toolWindow = Join-Path (& $uv tool dir --bin).Trim() "ddict-fenetre.exe"
function Get-OpenTool {
    @(Get-Process | Where-Object {
        $_.Path -and ($_.Path -like "$toolDir\*" -or $_.Path -eq $toolExe -or $_.Path -eq $toolWindow)
    })
}
$open = Get-OpenTool
if ($open.Count -gt 0) {
    Say "L'outil est ouvert : il faut le fermer pour le mettre à jour. Vos décisions sont déjà enregistrées."
    if (Ask "Fermer l'outil maintenant ?") {
        $open | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    if ((Get-OpenTool).Count -gt 0) {
        Fail "L'outil est encore ouvert. Fermez sa fenêtre (ou cliquez « Quitter l'outil »), puis relancez installer.bat."
    }
    Say "Outil fermé."
}
& $uv tool install --reinstall ("{0}[ia,revision]" -f $Root)
if ($LASTEXITCODE -ne 0) {
    Fail "L'installation de l'outil a échoué (code $LASTEXITCODE). Vérifiez la connexion Internet et que l'outil est fermé, puis relancez installer.bat."
}
if (-not $ShortcutDir) {  # a trial leaves PATH alone
    # uv writes its notes to stderr; under "Stop", Windows PowerShell 5.1 would take a
    # redirected one for a fatal error (found by the trial of 0.3.0).
    $ErrorActionPreference = "Continue"
    & $uv tool update-shell 2>&1 | Out-Null
    $ErrorActionPreference = "Stop"
}
$bin = (& $uv tool dir --bin).Trim()
$ddict = Join-Path $bin "ddict.exe"
if (-not (Test-Path $ddict)) { Fail "L'outil est installé, mais ddict.exe est introuvable dans $bin." }
# The icon starts the tool in its own window, without a console (D-055).
$launcher = Join-Path $bin "ddict-fenetre.exe"
if (-not (Test-Path $launcher)) { $launcher = $ddict }
$version = (& $ddict --version).Trim()
Say "Installé : $version"

# --- 3. Les icônes --------------------------------------------------------------------
Step "3/3 - Les icônes"
if ($ShortcutDir) {
    $folders = @($ShortcutDir)
} else {
    $folders = @([Environment]::GetFolderPath("Programs"), [Environment]::GetFolderPath("Desktop"))
}
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force $folder | Out-Null
    $link = $shell.CreateShortcut((Join-Path $folder $ShortcutName))
    $link.TargetPath = $launcher
    $link.WorkingDirectory = [Environment]::GetFolderPath("MyDocuments")
    if ($launcher -eq $ddict) { $link.WindowStyle = 7 }  # a console: it starts minimized
    $link.Description = "Ouvre l'outil dans sa fenêtre (cet ordinateur seulement)."
    $link.Save()
    Say "Icône créée : $(Join-Path $folder $ShortcutName)"
}

Write-Host ""
Write-Host "Installation terminée." -ForegroundColor Green
Say "Double-cliquez sur l'icône « Dictionnaire de données » (bureau ou menu Démarrer) : l'outil"
Say "s'ouvre dans votre navigateur. Une petite fenêtre réduite le fait tourner ; fermez-la pour"
Say "arrêter l'outil."
Say ""
Say "L'IA est facultative. Pour l'utiliser : une clé d'API, à saisir sur la page « IA » de"
Say "l'outil (voir docs/installation-windows.md). Elle n'envoie jamais les réponses des"
Say "participants, et seulement pour un projet qui le permet."
Finish 0
