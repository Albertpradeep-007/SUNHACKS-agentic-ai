# setup.ps1 - PowerShell script for Windows environments

Write-Host "Initializing Agentic AI System Architecture..." -ForegroundColor Cyan

# 1. Modular Folders
$folders = @(
    "frontend", 
    "backend\src\routes", "backend\src\controllers", "backend\src\services",
    "agents\coder", "agents\debugger", "agents\reporter",
    "shared\types", "shared\constants", "shared\utils"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

# 2. Setup Shared & Agent Files
Write-Host "Scaffolding Agent templates..." -ForegroundColor Cyan
New-Item -ItemType File -Force -Path "shared\utils\encryption.ts" | Out-Null
New-Item -ItemType File -Force -Path "shared\types\index.ts" | Out-Null

$agents = @("coder", "debugger", "reporter")
foreach ($agent in $agents) {
    New-Item -ItemType File -Force -Path "agents\$agent\prompt.ts" | Out-Null
    New-Item -ItemType File -Force -Path "agents\$agent\logic.ts" | Out-Null
    New-Item -ItemType File -Force -Path "agents\$agent\tools.ts" | Out-Null
}

# 3. Initialize Backend
Write-Host "Setting up Node.js Backend..." -ForegroundColor Cyan
Set-Location backend
npm init -y | Out-Null
npm install express cors dotenv axios @langchain/core @langchain/community --legacy-peer-deps
npm install -D typescript @types/node @types/express @types/cors ts-node --legacy-peer-deps
npx tsc --init
Set-Location ..

# 4. Initialize Frontend
Write-Host "Setting up Next.js Frontend (Mission Control)..." -ForegroundColor Cyan
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes

Write-Host "Setup script finished successfully!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "1. Verify Ollama is running (localhost:11434)"
Write-Host "2. cd frontend; npm run dev"
Write-Host "3. cd backend; npx ts-node src/services/OllamaService.ts"
