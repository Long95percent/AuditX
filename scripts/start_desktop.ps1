param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$env:Path = "C:\Users\22641\.local\bin;C:\Users\22641\.cargo\bin;$env:Path"
$env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"

Write-Host "[AuditX] Repository: $repoRoot"
Write-Host "[AuditX] Using UV_CACHE_DIR=$env:UV_CACHE_DIR"

if (-not (Test-Path "frontend/package.json")) {
    throw "frontend/package.json was not found. Please run this script from the AuditX repository root or check the frontend directory."
}

if (-not (Test-Path "src-tauri/tauri.conf.json")) {
    throw "src-tauri/tauri.conf.json was not found. Please run this script from the AuditX repository root."
}

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo was not found. Restart PowerShell or install Rust/Cargo first."
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm.cmd was not found. Install Node.js first."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found. Restart PowerShell or install uv first."
}

if (-not $SkipInstall) {
    if (-not (Test-Path ".venv")) {
        Write-Host "[AuditX] Creating Python virtual environment with uv..."
        uv venv
    }

    if (-not (Test-Path "frontend/node_modules")) {
        Write-Host "[AuditX] Installing frontend dependencies..."
        npm.cmd --prefix frontend install
    }
}

if (-not (Test-Path "frontend/node_modules/@tauri-apps/cli")) {
    Write-Host "[AuditX] Installing local Tauri CLI package..."
    npm.cmd --prefix frontend install
}

$frontendPortInUse = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 1420 -State Listen -ErrorAction SilentlyContinue
if ($frontendPortInUse) {
    $owningProcess = Get-Process -Id $frontendPortInUse.OwningProcess -ErrorAction SilentlyContinue
    $processName = if ($owningProcess) { $owningProcess.ProcessName } else { "unknown" }
    throw "Frontend dev port 127.0.0.1:1420 is already in use by process $($frontendPortInUse.OwningProcess) ($processName). Close existing AuditX/Tauri/Vite windows and rerun this script."
}
$backendStartedByScript = $false
$backendProcess = $null

try {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2 | Out-Null
        Write-Host "[AuditX] Backend API already running on http://127.0.0.1:8765"
    } catch {
        Write-Host "[AuditX] Starting backend API on http://127.0.0.1:8765..."
        $backendProcess = Start-Process `
            -FilePath "python" `
            -ArgumentList @("-m", "uvicorn", "auditx.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8765") `
            -WorkingDirectory $repoRoot `
            -PassThru
        $backendStartedByScript = $true

        $backendReady = $false
        for ($attempt = 1; $attempt -le 20; $attempt++) {
            Start-Sleep -Milliseconds 500
            try {
                Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2 | Out-Null
                $backendReady = $true
                break
            } catch {
                if ($backendProcess.HasExited) {
                    throw "Backend API exited before becoming ready."
                }
            }
        }

        if (-not $backendReady) {
            throw "Backend API did not become ready on http://127.0.0.1:8765."
        }
        Write-Host "[AuditX] Backend API is ready."
    }

    Write-Host "[AuditX] Starting desktop app with local Tauri CLI..."
    & ".\frontend\node_modules\.bin\tauri.cmd" dev
} finally {
    if ($backendStartedByScript -and $backendProcess -and -not $backendProcess.HasExited) {
        Write-Host "[AuditX] Stopping backend API started by this script..."
        Stop-Process -Id $backendProcess.Id -Force
    }
}






