import json
from pathlib import Path


def test_tauri_window_uses_project_local_webview_data_directory() -> None:
    config_path = Path("src-tauri/tauri.conf.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    windows = config["app"]["windows"]
    assert windows, "Tauri app must define at least one startup window"
    window = windows[0]

    assert window.get("label") == "main"
    assert window.get("dataDirectory") == "auditx-dev-webview-data"


def test_tauri_dev_url_matches_frontend_dev_port() -> None:
    tauri_config = json.loads(Path("src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    frontend_package = json.loads(Path("frontend/package.json").read_text(encoding="utf-8-sig"))

    dev_url = tauri_config["build"]["devUrl"]
    dev_script = frontend_package["scripts"]["dev"]
    vite_config = Path("frontend/vite.config.mjs").read_text(encoding="utf-8")

    assert dev_url == "http://127.0.0.1:1420"
    assert dev_script == "vite"
    assert "port: 1420" in vite_config
    assert "strictPort: true" in vite_config
