from pathlib import Path


def test_tauri_dialog_plugin_is_registered_and_allowed() -> None:
    cargo = Path("src-tauri/Cargo.toml").read_text(encoding="utf-8")
    main_rs = Path("src-tauri/src/main.rs").read_text(encoding="utf-8")
    capability = Path("src-tauri/capabilities/default.json").read_text(encoding="utf-8")
    package = Path("frontend/package.json").read_text(encoding="utf-8-sig")

    assert "tauri-plugin-dialog" in cargo
    assert "tauri_plugin_dialog::init()" in main_rs
    assert "dialog:allow-open" in capability
    assert "@tauri-apps/plugin-dialog" in package
