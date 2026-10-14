# Uninstalls the tool for the current user (D-021). Started by desinstaller.bat.
#
# Removes the tool and its icons. Project files, codebooks and data are not touched. uv and
# Ollama stay installed: other software may use them.
#
# For trials: -ShortcutDir and -NoPrompt, as for installer.ps1.

param(
    [string]$ShortcutDir = "",
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
$ShortcutName = "Dictionnaire de données.lnk"

function Say([string]$Text) { Write-Host $Text }

function Ask([string]$Question) {
    if ($NoPrompt) { return $false }
    $answer = Read-Host "$Question (o/n)"
    return $answer -match "^\s*[oOyY]"
}

function Finish([int]$Code) {
    if (-not $NoPrompt) { Write-Host ""; Read-Host "Appuyez sur Entrée pour fermer cette fenêtre" | Out-Null }
    exit $Code
}

Say "Désinstallation de l'outil Dictionnaire de données"
Say "Vos fichiers projet, codebooks et données ne sont pas touchés."
if (-not $NoPrompt -and -not (Ask "Continuer ?")) { Finish 0 }

$uv = $null
$found = Get-Command uv -ErrorAction SilentlyContinue
if ($found) { $uv = $found.Source }
$local = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
if (-not $uv -and (Test-Path $local)) { $uv = $local }
if ($uv) {
    & $uv tool uninstall ddict
    if ($LASTEXITCODE -eq 0) { Say "Outil retiré." } else { Say "L'outil n'était pas installé." }
} else {
    Say "uv est introuvable : l'outil n'était probablement pas installé."
}

if ($ShortcutDir) {
    $folders = @($ShortcutDir)
} else {
    $folders = @([Environment]::GetFolderPath("Programs"), [Environment]::GetFolderPath("Desktop"))
}
foreach ($folder in $folders) {
    $path = Join-Path $folder $ShortcutName
    if (Test-Path $path) { Remove-Item $path; Say "Icône retirée : $path" }
}

$recents = Join-Path $env:APPDATA "ddict"
if (Test-Path $recents) {
    if (Ask "Effacer aussi la liste des projets récents (les chemins de vos fichiers projet) ?") {
        Remove-Item -Recurse $recents
        Say "Liste effacée."
    }
}

Write-Host ""
Write-Host "Désinstallation terminée." -ForegroundColor Green
Finish 0
