$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== Validation TEAM: clean artifacts ==" -ForegroundColor Cyan

$targets = @(
    "build",
    "dist",
    "release",
    "frontend\dist",
    ".pytest_cache"
)

foreach ($rel in $targets) {
    if (Test-Path $rel) {
        Remove-Item $rel -Recurse -Force
        Write-Host "  removed $rel" -ForegroundColor Green
    }
}

$skipRoots = @(
    (Join-Path $PWD ".venv"),
    (Join-Path $PWD "frontend\node_modules")
)

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Where-Object {
        $full = $_.FullName
        -not ($skipRoots | Where-Object { $full.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) })
    } |
    ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "  removed $($_.FullName)" -ForegroundColor DarkGray
    }

foreach ($wal in @("data\mapbiomas.db-shm", "data\mapbiomas.db-wal")) {
    if (Test-Path $wal) {
        Remove-Item $wal -Force
        Write-Host "  removed $wal" -ForegroundColor Green
    }
}

Write-Host "`nDone. Kept: .venv, node_modules, data\mapbiomas.db, backend\.env" -ForegroundColor Green
