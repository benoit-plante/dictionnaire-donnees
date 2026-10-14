#!/bin/bash
# Installs or updates the tool for the current user on macOS, without administrator rights
# (v0.5, D-031; the same steps as installer.bat on Windows, D-021). Double-click it in the
# Finder: it opens in the Terminal.
#
# It:
#   1. installs uv (Python manager, astral.sh) when missing, in the user's folder;
#   2. installs the tool with its options (local AI, interface), or updates it, after
#      closing an open tool if the person agrees;
#   3. creates the "Dictionnaire de données" icon in Applications and on the desktop;
#   4. checks Ollama and, only when the person asks, downloads the model.
# Internet is needed during the installation only; the tool itself never uses it.
#
# For trials: DDICT_APP_DIR (one folder for the icon instead of Applications and the
# desktop; PATH is then left alone) and DDICT_NO_PROMPT=1 (ask nothing, download nothing
# but the tool).

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
NAME="Dictionnaire de données"
MODEL="qwen2.5:7b-instruct-q4_K_M"
APP_DIR="${DDICT_APP_DIR:-}"
NO_PROMPT="${DDICT_NO_PROMPT:-}"

say() { printf '%s\n' "$1"; }
step() { printf '\n\033[36m%s\033[0m\n' "$1"; }
ask() {
    [ -n "$NO_PROMPT" ] && return 1
    local answer
    read -r -p "$1 (o/n) " answer
    [[ "$answer" =~ ^[[:space:]]*[oOyY] ]]
}
finish() {
    if [ -z "$NO_PROMPT" ]; then
        echo
        read -r -p "Appuyez sur Entrée pour fermer cette fenêtre." _
    fi
    exit "$1"
}
fail() {
    printf '\n\033[31m%s\033[0m\n' "$1"
    say "Notez ce message et transmettez-le à la personne qui vous a fourni l'outil."
    finish 1
}

say "Installation de l'outil $NAME"
say "Dossier de l'outil : $ROOT"
if [ ! -f "$ROOT/pyproject.toml" ]; then
    fail "Ce dossier ne contient pas l'outil (pyproject.toml manque). Lancez installer.command depuis le dossier de l'outil décompressé."
fi

# --- 1. uv ---------------------------------------------------------------------------
step "1/4 - uv, le gestionnaire de Python"
UV="$(command -v uv || true)"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -n "$UV" ]; then
    say "Déjà installé : $UV"
else
    say "Installation de uv depuis astral.sh (dans votre dossier d'utilisateur)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "uv n'a pas pu être installé. Vérifiez la connexion Internet, puis relancez installer.command."
    UV="$HOME/.local/bin/uv"
    [ -x "$UV" ] || fail "uv n'a pas pu être installé. Vérifiez la connexion Internet, puis relancez installer.command."
fi

# --- 2. L'outil ------------------------------------------------------------------------
step "2/4 - L'outil (une ou deux minutes la première fois)"
# An open tool may be using its own files: close it first (found by the trial of 0.4.0).
TOOL_DIR="$("$UV" tool dir)/ddict"
TOOL_EXE="$("$UV" tool dir --bin)/ddict"
open_tool() { pgrep -f "$TOOL_DIR/" >/dev/null 2>&1 || pgrep -f "^$TOOL_EXE( |$)" >/dev/null 2>&1; }
if open_tool; then
    say "L'outil est ouvert : il faut le fermer pour le mettre à jour. Vos décisions sont déjà enregistrées."
    if ask "Fermer l'outil maintenant ?"; then
        pkill -f "$TOOL_DIR/" 2>/dev/null
        pkill -f "^$TOOL_EXE( |$)" 2>/dev/null
        sleep 2
    fi
    if open_tool; then
        fail "L'outil est encore ouvert. Fermez sa fenêtre de Terminal, puis relancez installer.command."
    fi
    say "Outil fermé."
fi
"$UV" tool install --reinstall "$ROOT[ia,revision]" || fail "L'installation de l'outil a échoué. Vérifiez la connexion Internet et que l'outil est fermé, puis relancez installer.command."
if [ -z "$APP_DIR" ]; then  # a trial leaves PATH alone
    "$UV" tool update-shell >/dev/null 2>&1 || true
fi
DDICT="$("$UV" tool dir --bin)/ddict"
[ -x "$DDICT" ] || fail "L'outil est installé, mais ddict est introuvable dans $("$UV" tool dir --bin)."
say "Installé : $("$DDICT" --version)"

# --- 3. Les icônes --------------------------------------------------------------------
# A .command file: a double-click opens a Terminal window that runs the tool, and closing
# that window stops it, like the small console window on Windows.
step "3/4 - Les icônes"
if [ -n "$APP_DIR" ]; then
    FOLDERS=("$APP_DIR")
else
    FOLDERS=("$HOME/Applications" "$HOME/Desktop")
fi
for folder in "${FOLDERS[@]}"; do
    mkdir -p "$folder" || fail "Impossible de créer le dossier $folder."
    launcher="$folder/$NAME.command"
    {
        printf '#!/bin/bash\n'
        printf '# Opens the tool in the browser (this computer only). Close this window to stop it.\n'
        printf 'cd "$HOME/Documents" 2>/dev/null || cd "$HOME"\n'
        printf 'exec "%s"\n' "$DDICT"
    } > "$launcher"
    chmod +x "$launcher"
    say "Icône créée : $launcher"
done

# --- 4. Ollama (facultatif) -----------------------------------------------------------
step "4/4 - IA locale (facultative)"
MODELS="$(curl -s --max-time 3 http://127.0.0.1:11434/api/tags || true)"
if [ -z "$MODELS" ]; then
    say "Ollama ne répond pas sur cet ordinateur. L'outil fonctionne sans IA ; pour l'utiliser,"
    say "installez Ollama depuis https://ollama.com, puis relancez installer.command."
    if ask "Ouvrir la page de téléchargement d'Ollama dans le navigateur ?"; then
        open "https://ollama.com/download"
    fi
elif printf '%s' "$MODELS" | grep -q "\"$MODEL\""; then
    say "Ollama répond, et le modèle recommandé est installé ($MODEL)."
else
    say "Ollama répond, mais le modèle recommandé n'est pas installé ($MODEL, environ 4,7 Go)."
    if ask "Le télécharger maintenant ?"; then
        OLLAMA="$(command -v ollama || echo /Applications/Ollama.app/Contents/Resources/ollama)"
        "$OLLAMA" pull "$MODEL"
    else
        say "Plus tard, dans le Terminal : ollama pull $MODEL"
    fi
fi

printf '\n\033[32mInstallation terminée.\033[0m\n'
say "Double-cliquez sur l'icône « $NAME » (bureau ou dossier Applications) : l'outil"
say "s'ouvre dans votre navigateur."
finish 0
