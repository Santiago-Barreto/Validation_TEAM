$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== Validation TEAM: build .exe ==" -ForegroundColor Cyan

Write-Host "`n[1/4] Building frontend..." -ForegroundColor Yellow
Push-Location frontend
if (-not (Test-Path node_modules)) {
    npm install
}
npm run build
if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
Pop-Location

if (-not (Test-Path "frontend\dist\index.html")) {
    throw "frontend\dist\index.html was not generated"
}

Write-Host "`n[2/4] Installing PyInstaller..." -ForegroundColor Yellow
python -m pip install -r backend\requirements-packaging.txt -q

Write-Host "`n[3/4] Packaging with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller --noconfirm Validation_TEAM.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$releaseRoot = Join-Path $PWD "release\Validation_TEAM"
Write-Host "`n[4/4] Preparing release at $releaseRoot ..." -ForegroundColor Yellow

if (Test-Path $releaseRoot) {
    Remove-Item $releaseRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
Copy-Item -Path "dist\Validation_TEAM\*" -Destination $releaseRoot -Recurse -Force

New-Item -ItemType Directory -Path (Join-Path $releaseRoot "backend\data") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $releaseRoot "data") -Force | Out-Null

if (Test-Path "data\COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx") {
    Copy-Item "data\COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx" `
        (Join-Path $releaseRoot "data\COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx") -Force
}

if (Test-Path "data\README.md") {
    Copy-Item "data\README.md" (Join-Path $releaseRoot "data\README.md") -Force
}

Copy-Item "packaging\README_EXE.md" (Join-Path $releaseRoot "README.txt") -Force

if (Test-Path "backend\credentials.json") {
    Copy-Item "backend\credentials.json" (Join-Path $releaseRoot "backend\credentials.json") -Force
} else {
    Write-Host "  Warning: copy backend\credentials.json into the release folder." -ForegroundColor DarkYellow
}

if (Test-Path "backend\.env") {
    Copy-Item "backend\.env" (Join-Path $releaseRoot "backend\.env") -Force
} elseif (Test-Path "backend\.env.example") {
    Copy-Item "backend\.env.example" (Join-Path $releaseRoot "backend\.env") -Force
}

if (Test-Path "data\mapbiomas.db") {
    Copy-Item "data\mapbiomas.db" (Join-Path $releaseRoot "data\mapbiomas.db") -Force
} else {
    Write-Host "  Warning: copy data\mapbiomas.db for the statistics panel." -ForegroundColor DarkYellow
}

Write-Host "`nDone: $releaseRoot" -ForegroundColor Green
Write-Host "Run: $releaseRoot\Validation_TEAM.exe" -ForegroundColor Green
