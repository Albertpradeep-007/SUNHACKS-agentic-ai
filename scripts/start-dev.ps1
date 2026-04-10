$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path "backend/.env")) {
  Write-Host "backend/.env not found. Creating from backend/.env.example ..."
  Copy-Item "backend/.env.example" "backend/.env"
  Write-Host "Fill GROQ_API_KEY and GITHUB_TOKEN in backend/.env, then re-run this script."
  exit 1
}

try {
  docker info | Out-Null
}
catch {
  Write-Host "Current Docker context is unavailable. Trying context 'default'..."
  docker context use default | Out-Null
  docker info | Out-Null
}

docker compose -f docker-compose.dev.yml up --build
