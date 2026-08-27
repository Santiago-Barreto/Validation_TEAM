$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "== Validation TEAM: dev setup ==" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python not found. Install Python 3.13+ or activate conda env 'validation-team'."
}

Write-Host "`n[1/4] Python dependencies..." -ForegroundColor Yellow
python -m pip install -r backend\requirements.txt -q

Write-Host "`n[2/4] Frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
if (-not (Test-Path node_modules)) {
    npm install
} else {
    Write-Host "  node_modules already present — skipping npm install" -ForegroundColor DarkGray
}
Pop-Location

Write-Host "`n[3/4] Local config checks..." -ForegroundColor Yellow
$checks = @(
    @{ Path = "backend\credentials.json"; Required = $true; Hint = "Earth Engine service account JSON" },
    @{ Path = "backend\.env"; Required = $false; Hint = "Copy from backend\.env.example" },
    @{ Path = "data\mapbiomas.db"; Required = $false; Hint = "Copy from Statistics project — see data\README.md" },
    @{ Path = "backend\data\comentarios_team.json"; Required = $false; Hint = "Only if PUNTOS_BACKEND=json; copy from comentarios_team.example.json" }
)

foreach ($c in $checks) {
    if (Test-Path $c.Path) {
        Write-Host "  OK  $($c.Path)" -ForegroundColor Green
    } elseif ($c.Required) {
        Write-Host "  MISSING (required): $($c.Path) — $($c.Hint)" -ForegroundColor Red
    } else {
        Write-Host "  optional: $($c.Path) — $($c.Hint)" -ForegroundColor DarkYellow
    }
}

Write-Host "`n[4/4] Quick health check..." -ForegroundColor Yellow
python -c "import backend.main; print('  backend imports OK')"

Write-Host "`nSetup complete." -ForegroundColor Green
Write-Host "  API:  uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --app-dir ." -ForegroundColor White
Write-Host "  UI:   cd frontend && npm run dev" -ForegroundColor White
