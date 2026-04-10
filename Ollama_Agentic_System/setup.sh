#!/bin/bash
# setup.sh - Shell script for environments supporting bash

echo "Initializing Agentic AI System Architecture..."

# 1. Modular Folders
mkdir -p frontend backend agents/{coder,debugger,reporter} shared/{types,constants,utils}

# 2. Setup Shared Files
echo "Scaffolding Agent templates..."
touch shared/utils/encryption.ts
touch shared/types/index.ts

for agent in coder debugger reporter; do
  touch agents/$agent/prompt.ts
  touch agents/$agent/logic.ts
  touch agents/$agent/tools.ts
done

# 3. Initialize Backend
echo "Setting up Node.js Backend..."
cd backend
npm init -y > /dev/null
npm install express cors dotenv axios @langchain/core @langchain/community
npm install -D typescript @types/node @types/express @types/cors ts-node
npx tsc --init
mkdir -p src/routes src/controllers src/services
cd ..

# 4. Initialize Frontend
echo "Setting up Next.js Frontend (Mission Control)..."
# Using npx to bootstrap Next.js silently
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes

echo "Setup script finished successfully!"
echo "Next steps:"
echo "1. Verify Ollama is running (localhost:11434)"
echo "2. cd frontend && npm run dev"
echo "3. cd backend && npx ts-node src/services/OllamaService.ts"
