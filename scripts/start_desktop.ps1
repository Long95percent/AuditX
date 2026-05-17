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

Write-Host "[AuditX] Starting desktop app with local Tauri CLI..."
& ".\frontend\node_modules\.bin\tauri.cmd" dev




