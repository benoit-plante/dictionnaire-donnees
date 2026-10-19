"""v0.3, step 7: the Windows installer, and starting the tool again from its icon."""

from pathlib import Path

from ddict import cli

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ["installer", "desinstaller"]


def test_batch_files_start_their_script():
    for name in SCRIPTS:
        raw = (ROOT / f"{name}.bat").read_bytes()
        assert raw.isascii() and b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
        text = raw.decode("ascii")
        assert f'-ExecutionPolicy Bypass -File "%~dp0windows\\{name}.ps1"' in text


def test_powershell_scripts_can_be_read_by_windows_powershell():
    """PowerShell 5.1 reads accents right only with a UTF-8 signature (BOM)."""
    for name in SCRIPTS:
        raw = (ROOT / "windows" / f"{name}.ps1").read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        assert b"\n" not in raw.replace(b"\r\n", b"")
        assert "Dictionnaire de données.lnk" in raw.decode("utf-8")


def test_installer_needs_no_administrator_and_no_model():
    text = (ROOT / "windows" / "installer.ps1").read_text(encoding="utf-8-sig")
    assert "RunAs" not in text and "Administrator" not in text
    assert 'tool install --reinstall ("{0}[ia,revision]" -f $Root)' in text
    # v0.18 (D-135): no local model to install; the key is typed on the AI page.
    assert "pull" not in text and "4/4" not in text and 'Step "3/3' in text
    assert "page « IA »" in text


def test_uninstaller_keeps_the_projects():
    text = (ROOT / "windows" / "desinstaller.ps1").read_text(encoding="utf-8-sig")
    assert "tool uninstall ddict" in text
    assert ".dd.json" not in text  # never deletes project files


def test_uninstaller_asks_before_erasing_the_key():
    """v0.18 (D-137): the entries "ddict:<address>" of the credential manager, after a yes;
    -NoPrompt answers no."""
    text = (ROOT / "windows" / "desinstaller.ps1").read_text(encoding="utf-8-sig")
    delete = text.index('cmdkey "/delete:$target"')
    assert text.rfind('Ask "Effacer aussi la clé d', 0, delete) != -1
    assert r'Select-String -Pattern "target=(\S*ddict:\S+)"' in text
    assert "if ($NoPrompt) { return $false }" in text


# The local model of v0.2 to v0.17 (D-023), gone in v0.18 (D-135); archives aside.
GONE = ("ollama", "qwen", "11434", "modèle local", "ia locale", "local model")
ARCHIVES = {"scripts/essai_contexte_modele.py"}  # the trial of D-080, kept as it was


def test_no_local_model_left_in_the_code():
    files = [ROOT / "installer.bat", ROOT / "desinstaller.bat"]
    for folder in ("src", "windows", "scripts"):
        files += [
            f for f in (ROOT / folder).rglob("*") if f.suffix in (".py", ".ps1", ".txt", ".po")
        ]
    found = []
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        if name in ARCHIVES or "__pycache__" in name:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace").casefold()
        found += [f"{name}: {word}" for word in GONE if word in text]
    assert not found


def test_icon_on_an_open_tool_shows_it(monkeypatch):
    opened = []
    monkeypatch.setattr(cli, "_port_open", lambda host, port: True)
    monkeypatch.setattr(cli.webbrowser, "open", opened.append)
    assert cli.main([]) == 0
    assert opened == ["http://127.0.0.1:8501"]


def test_busy_port_for_a_project_is_explained(monkeypatch, tmp_path, fictional_files, capsys):
    from ddict.workflow import profile_database

    _project, path = profile_database(fictional_files["etude-sommeil.sav"], tmp_path / "p.dd.json")
    monkeypatch.setattr(cli, "_port_open", lambda host, port: True)
    assert cli.main(["reviser", str(path)]) == 2
    assert "--port 8502" in capsys.readouterr().err


def test_no_redirected_native_output_under_stop():
    """Windows PowerShell 5.1 turns a redirected stderr line of a program into a fatal error
    when $ErrorActionPreference is "Stop": uv's notes stopped the installer (0.3.0 trial)."""
    for name in SCRIPTS:
        lines = (ROOT / "windows" / f"{name}.ps1").read_text(encoding="utf-8-sig").splitlines()
        stop = True
        for line in lines:
            if '$ErrorActionPreference = "Continue"' in line:
                stop = False
            elif '$ErrorActionPreference = "Stop"' in line:
                stop = True
            elif "& $" in line and ("2>" in line or "*>" in line):
                assert not stop, f"{name}.ps1: {line.strip()}"


def test_an_open_tool_is_closed_only_when_asked():
    """An open tool locked its files and the update failed half-way (0.4.0 trial)."""
    text = (ROOT / "windows" / "installer.ps1").read_text(encoding="utf-8-sig")
    check = text.index("Get-OpenTool")
    asked = text.index('Ask "Fermer l\'outil maintenant ?"')
    assert check < asked < text.index("Stop-Process") < text.index("uv tool install")


def test_the_icon_opens_the_window_without_console():
    """v0.7.1 (D-055): the icon starts the GUI script; the console exe only as a fallback."""
    text = (ROOT / "windows" / "installer.ps1").read_text(encoding="utf-8-sig")
    assert '$launcher = Join-Path $bin "ddict-fenetre.exe"' in text
    assert "$link.TargetPath = $launcher" in text
    for name in SCRIPTS:
        script = (ROOT / "windows" / f"{name}.ps1").read_text(encoding="utf-8-sig")
        assert "$_.Path -eq $toolWindow" in script  # an open window is closed too


def test_no_local_model_left_in_the_guides():
    """v0.18, C3: the guides and the rules. The design (one section per version), the
    roadmap, the trials, the plans, the journal and the changelog keep their history."""
    guides = ["README.md", "CLAUDE.md", "docs/installation-windows.md",
              "docs/en/installation-windows.md", "docs/scenario-revision.md",
              "docs/dependances.md", "docs/glossaire-traduction.md"]  # fmt: skip
    found = []
    for name in guides:
        text = (ROOT / name).read_text(encoding="utf-8").casefold()
        found += [f"{name}: {word}" for word in GONE if word in text]
    assert not found
