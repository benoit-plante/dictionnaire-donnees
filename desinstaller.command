#!/bin/bash
# Uninstalls the tool for the current user on macOS (v0.5; as desinstaller.bat, D-021).
#
# Removes the tool and its icons. Project files, codebooks and data are not touched. uv and
# Ollama stay installed: other software may use them.
#
# For trials: DDICT_APP_DIR and DDICT_NO_PROMPT=1, as for installer.command.

set -u
NAME="Dictionnaire de données"
APP_DIR="${DDICT_APP_DIR:-}"
NO_PROMPT="${DDICT_NO_PROMPT:-}"

say() { printf '%s\n' "$1"; }
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

say "Désinstallation de l'outil $NAME"
say "Vos fichiers projet, codebooks et données ne sont pas touchés."
if [ -z "$NO_PROMPT" ] && ! ask "Continuer ?"; then finish 0; fi

UV="$(command -v uv || true)"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -n "$UV" ]; then
    TOOL_DIR="$("$UV" tool dir)/ddict"
    TOOL_EXE="$("$UV" tool dir --bin)/ddict"
    # An open tool is closed first: its files are in use (found by the trial of 0.4.0).
    pkill -f "$TOOL_DIR/" 2>/dev/null && sleep 2
    pkill -f "^$TOOL_EXE( |$)" 2>/dev/null
    if "$UV" tool uninstall ddict; then say "Outil retiré."; else say "L'outil n'était pas installé."; fi
else
    say "uv est introuvable : l'outil n'était probablement pas installé."
fi

if [ -n "$APP_DIR" ]; then
    FOLDERS=("$APP_DIR")
else
    FOLDERS=("$HOME/Applications" "$HOME/Desktop")
fi
for folder in "${FOLDERS[@]}"; do
    launcher="$folder/$NAME.command"
    if [ -e "$launcher" ]; then rm -f "$launcher" && say "Icône retirée : $launcher"; fi
done

RECENTS="$HOME/Library/Application Support/ddict"
if [ -d "$RECENTS" ]; then
    if ask "Effacer aussi la liste des projets récents et la langue choisie (les chemins de vos fichiers projet) ?"; then
        rm -rf "$RECENTS"
        say "Liste effacée."
    fi
fi

printf '\n\033[32mDésinstallation terminée.\033[0m\n'
finish 0
