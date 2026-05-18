from pathlib import Path


def test_desktop_start_script_starts_backend_before_tauri() -> None:
    script = Path("scripts/start_desktop.ps1").read_text(encoding="utf-8")

    assert "auditx.main:app" in script
    assert '"--port", "8765"' in script
    assert "Start-Process" in script
    assert "Stop-Process" in script
