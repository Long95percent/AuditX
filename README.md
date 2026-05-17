# AuditX / VeriDoc

AuditX / VeriDoc is a high-certainty, industrial-grade desktop audit application for enterprise document review.

## Architecture

- Backend: Python + FastAPI + Pydantic + pytest
- Frontend UI: React + Vite + TypeScript
- Desktop Shell: Tauri + Python Sidecar
- Package management: uv only, Conda is not used
- Audit principle: every finding must include traceable evidence and precise bbox coordinates

## Acceptance Target

The final product is a **desktop application**. Browser preview and standalone backend API are development tools only. For acceptance, use the Tauri desktop app.

```text
Tauri desktop shell
  -> loads React/Vite UI
  -> will later orchestrate Python sidecar backend
```

## What To Open

### Recommended: double-click startup

For acceptance, use the desktop startup script in the project root:

```text
启动AuditX桌面应用.bat
```

How to run it:

1. Open Windows File Explorer.
2. Go to `D:\github_desktop\AuditX`.
3. Double-click `启动AuditX桌面应用.bat`.
4. Wait for the terminal logs.
5. A native Tauri desktop window should open.

Expected result:

- A native Tauri desktop window opens.
- The window shows the AuditX / VeriDoc glassmorphism desktop UI skeleton.
- This is the acceptance surface for the app.

If dependencies have already been installed and you want a faster startup, double-click:

```text
快速启动AuditX桌面应用.bat
```

### Alternative: PowerShell startup

If double-click startup fails, use **Windows PowerShell** or **PowerShell 7**:

1. Open **Windows PowerShell**.
2. Go to the project root directory:

```powershell
cd D:\github_desktop\AuditX
```

3. Start the desktop app with the provided PowerShell script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_desktop.ps1
```

Fast startup after dependencies are already installed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_desktop.ps1 -SkipInstall
```

## What The Startup Script Does

Script file: `scripts/start_desktop.ps1`

It does the following:

1. Switches to the repository root.
2. Adds these user tool paths for the current PowerShell session:
   - `C:\Users\22641\.local\bin`
   - `C:\Users\22641\.cargo\bin`
3. Sets uv cache to the project-local `.uv-cache` directory.
4. Checks that `uv`, `npm`, and `cargo` are available.
5. Creates `.venv` with `uv venv` if missing.
6. Runs `npm.cmd --prefix frontend install` if `frontend/node_modules` is missing.
7. Installs Tauri CLI with Cargo if missing.
8. Starts the desktop app with `.\frontend\node_modules\.bin\tauri.cmd dev`.

## Current Scope

The repository currently contains the foundational desktop/backend/frontend structure and a Phase 1A fake audit backend loop. OCR, LLM inference, external APIs, real file upload, real PDF rendering, and real Python sidecar packaging are intentionally not implemented yet.

## Manual Desktop Startup

Use this only if you do not want to use the startup script.

Open **Windows PowerShell**, then run:

```powershell
cd D:\github_desktop\AuditX
$env:Path = "C:\Users\22641\.local\bin;C:\Users\22641\.cargo\bin;$env:Path"
$env:UV_CACHE_DIR = ".uv-cache"
.\frontend\node_modules\.bin\tauri.cmd dev
```

If `.\frontend\node_modules\.bin\tauri.cmd dev` says `no such command: tauri`, install the Tauri CLI in the same PowerShell window:

```powershell
npm.cmd --prefix frontend install
.\frontend\node_modules\.bin\tauri.cmd dev
```

## Backend API Development Startup

This is not the final acceptance surface. Use it only when checking the Phase 1A backend fake audit loop.

Open **Windows PowerShell**, then run:

```powershell
cd D:\github_desktop\AuditX
$env:Path = "C:\Users\22641\.local\bin;C:\Users\22641\.cargo\bin;$env:Path"
$env:UV_CACHE_DIR = ".uv-cache"
python -m uvicorn auditx.main:app --app-dir backend --reload --host 127.0.0.1 --port 8765
```

Then open this URL in a browser:

```text
http://127.0.0.1:8765/docs
```

Useful endpoints:

```text
GET  /health
POST /api/audit-jobs
GET  /api/audit-jobs/{job_id}
GET  /api/audit-jobs/{job_id}/findings
```

Example body for `POST /api/audit-jobs`:

```json
{
  "file_path": "demo_resume.pdf"
}
```

## Frontend Browser Preview

This is only for UI development. It is not the final acceptance target.

Open **Windows PowerShell**, then run:

```powershell
cd D:\github_desktop\AuditX
npm.cmd --prefix frontend run dev
```

Then open this URL in a browser:

```text
http://127.0.0.1:5173
```

## Test Commands

Open **Windows PowerShell**, then run:

```powershell
cd D:\github_desktop\AuditX
python -m pytest backend/tests/unit backend/tests/integration -q -p no:cacheprovider
```

Latest verified result:

```text
6 passed
```

`-p no:cacheprovider` avoids pytest cache write warnings in the current Windows workspace.

## Important Notes

- Do not use Conda for this project.
- Use `uv` for Python environment management.
- Treat `frontend/` as the UI source, not as the final standalone app.
- Treat `src-tauri/` as the desktop shell and final app entry.
- Python sidecar packaging is planned but not enabled in Tauri config yet; the current desktop build starts the Tauri shell and React UI only.





