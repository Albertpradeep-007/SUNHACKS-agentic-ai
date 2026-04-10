# Agentic AI System: Modular Ollama-Powered Orchestration

A production-grade, modular Agentic AI system that interfaces with a local Ollama instance securely to avoid API costs and protect data privacy. This system provides a Next.js mission control dashboard, a Node.js orchestration backend, and modular agent clusters adhering to the real-time "Claude Code" interaction standard.

## 🏗️ Architecture

```text
.
├── frontend/             # Next.js (App Router), Tailwind CSS, Lucide React
├── backend/              # Node.js/Express, LangChain integration
│   └── src/
│       └── services/
│           └── OllamaService.ts  # Boilerplate Ollama API integration
├── agents/               # Modular Agent Cores
│   ├── coder/            # Auto-generates code, edits files
│   ├── debugger/         # Analyzes failure logs (like MATLAB/Simulink errors)
│   └── reporter/         # Synthesizes outcomes into executive reports
│       ├── prompt.ts     # System prompts, personas, output formats
│       ├── logic.ts      # The ReAct/Agentic loop execution strategy 
│       └── tools.ts      # Specialized tools (e.g., FileSystem, ShellExec)
└── shared/               # Shared cross-boundary utilities
    ├── types/            # TypeScript interfaces
    ├── constants/        # System-wide variables
    └── utils/
        └── encryption.ts # Custom AES-128/LSB routines
```

## 🚀 Quick Start

### 1. Prerequisites
- Install and launch [Ollama](https://ollama.com/).
- Ensure the model is available by running: `ollama pull llama3` (or `mistral`).
- Node.js version 18+ and `npm`.

### 2. Initialize System Folder Structure
Since you are on Windows, you can use the provided PowerShell setup script (or the bash script if you prefer Git Bash).

**Windows (PowerShell):**
```powershell
./setup.ps1
```

**Linux/Mac/Git Bash:**
```bash
bash setup.sh
```

This will automatically scaffold the directories, initialize the `frontend` using Next.js CLI, and install `backend` packages (Express, Axios, Langchain, etc.).

### 3. The "Claude Code" Layer
By adopting a filesystem orchestration mechanism, your agents inside the `agents/` directories will utilize tools to:
- Read source code locally via `fs` integration.
- Run terminal commands through Node's `child_process.exec`.
- Record interactions in an overarching `history.log`.
- Automate commits via `git`.
