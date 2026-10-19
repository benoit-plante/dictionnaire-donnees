# Uninstalls the tool for the current user (D-021). Started by desinstaller.bat.
#
# Removes the tool and its icons. Project files, codebooks and data are not touched. uv
# stays installed: other software may use it. The AI settings and the API key are erased
# only when the person asks (v0.18).
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
    # An open tool locks its files (found by the trial of 0.4.0): close it first.
    $toolDir = Join-Path (& $uv tool dir).Trim() "ddict"
    $toolExe = Join-Path (& $uv tool dir --bin).Trim() "ddict.exe"
    $toolWindow = Join-Path (& $uv tool dir --bin).Trim() "ddict-fenetre.exe"
    $open = @(Get-Process | Where-Object {
        $_.Path -and ($_.Path -like "$toolDir\*" -or $_.Path -eq $toolExe -or $_.Path -eq $toolWindow)
    })
    if ($open.Count -gt 0) {
        if ($NoPrompt -or (Ask "L'outil est ouvert. Le fermer maintenant ? Vos décisions sont déjà enregistrées.")) {
            $open | Stop-Process -Force
            Start-Sleep -Seconds 2
        } else {
            Say "Fermez la fenêtre de l'outil (ou cliquez « Quitter l'outil »), puis relancez desinstaller.bat."
            Finish 1
        }
    }
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
    if (Ask "Effacer aussi les listes des projets récents et des projets suivis (les chemins de vos fichiers projet) et les réglages de l'IA ?") {
        Remove-Item -Recurse $recents
        Say "Listes et réglages effacés."
    }
}

# The API key (v0.18, D-137): entries "ddict:<address>" of Windows' Credential Manager. The
# label before "target=" depends on the language of Windows; "target=" does not.
$keys = @(cmdkey /list | Select-String -Pattern "target=(\S*ddict:\S+)" | ForEach-Object { $_.Matches[0].Groups[1].Value })
if ($keys.Count -gt 0) {
    if (Ask "Effacer aussi la clé d'API de l'IA, gardée dans le gestionnaire d'identifiants de Windows ?") {
        foreach ($target in $keys) { cmdkey "/delete:$target" | Out-Null }
        Say "Clé d'API effacée."
    }
}

Write-Host ""
Write-Host "Désinstallation terminée." -ForegroundColor Green
Finish 0
