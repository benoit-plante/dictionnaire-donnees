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


def test_installer_needs_no_administrator_and_asks_before_any_model():
    text = (ROOT / "windows" / "installer.ps1").read_text(encoding="utf-8-sig")
    assert "RunAs" not in text and "Administrator" not in text
    assert 'tool install --reinstall ("{0}[ia,revision]" -f $Root)' in text
    # The model is pulled only after a yes; -NoPrompt answers no.
    pull = text.index("pull $Model")
    assert text.rfind('Ask "Le télécharger maintenant ?"', 0, pull) != -1
    assert "if ($NoPrompt) { return $false }" in text


def test_uninstaller_keeps_the_projects():
    text = (ROOT / "windows" / "desinstaller.ps1").read_text(encoding="utf-8-sig")
    assert "tool uninstall ddict" in text
    assert ".dd.json" not in text  # never deletes project files


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
