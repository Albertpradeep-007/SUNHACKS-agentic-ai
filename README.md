<div align="center">

# 🧠 PEIP — Predictive Engineering Intelligence Platform

### **Autonomous Multi-Agent AI System for Software Risk Prediction & Code Health Analysis**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-LLaMa3-orange?logo=llama)](https://ollama.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)](https://nodejs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

<br/>

> **Built for SUNHACKS** — A fully local, privacy-first AI platform that predicts software crashes before they happen, calculates executive tech-debt ROI, and autonomously generates code patches using a multi-agent orchestration engine powered by LLaMa3.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Usage](#-usage)
- [Dashboard & Reports](#-dashboard--reports)
- [Agents Deep Dive](#-agents-deep-dive)
- [Ollama Agentic System](#-ollama-agentic-system)
- [Contributing](#-contributing)
- [Research References](#-research-references)

---

## 🌟 Overview

**PEIP** is a **Predictive Engineering Intelligence Platform** that uses an autonomous multi-agent architecture to:

1. **Statically analyze** codebases for complexity, maintainability, and risk signals
2. **Predict future software crashes** using research-backed engineering metrics
3. **Calculate Executive Tech-Debt ROI** — translating code quality into business cost
4. **Generate interactive CEO-level reports** with actionable recommendations
5. **Autonomously suggest code patches** to resolve identified risks

All AI inference happens **100% locally** via [Ollama](https://ollama.com) + LLaMa3 — **zero data leaves your machine**.

---

## ✨ Key Features

| Feature | Description |
|:---|:---|
| 🤖 **Multi-Agent Orchestration** | 4-layer agent pipeline with autonomous handoffs, retry logic, and state management |
| 📊 **Interactive War Room Dashboard** | Rich HTML report with health scores, risk heatmaps, and financial impact analysis |
| 🔒 **100% Local & Private** | All AI processing runs on your machine via Ollama — no API keys, no cloud |
| 🧮 **Research-Backed Metrics** | McCabe Cyclomatic Complexity, DORA metrics, Bus Factor, Code Churn, Hotspot Detection |
| 💰 **Financial ROI Calculation** | IBM's 100x multiplier for fix-now vs. fix-after-failure cost comparison |
| 📝 **CEO Executive Reports** | Auto-generated Markdown reports with board-ready language |
| 🩹 **Autonomous Patch Generation** | AI-suggested code fixes for identified risk areas |
| 🎛️ **Mission Control UI** | Next.js dashboard for real-time agent monitoring and orchestration |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PEIP — System Architecture                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   LAYER 1: INPUT AGENT                                              │
│   ┌─────────────────────────────────────────────┐                   │
│   │  Validates GitHub URL/Token → Session Config │                   │
│   └──────────────────┬──────────────────────────┘                   │
│                      ▼                                              │
│   LAYER 2: MASTER AGENT (Orchestrator)                              │
│   ┌─────────────────────────────────────────────┐                   │
│   │  ┌──────────────┐  ┌───────────────────┐    │                   │
│   │  │ GitHistory    │  │ Complexity Agent  │    │                   │
│   │  │ Agent         │  │ (Radon AST)       │    │                   │
│   │  └──────┬───────┘  └────────┬──────────┘    │                   │
│   │         ▼                   ▼                │                   │
│   │  ┌──────────────┐  ┌───────────────────┐    │                   │
│   │  │ Risk Agent   │  │ CEO Report Agent  │    │                   │
│   │  │ (Classifier) │  │ (LLaMa3 Summary)  │    │                   │
│   │  └──────────────┘  └───────────────────┘    │                   │
│   └──────────────────┬──────────────────────────┘                   │
│                      ▼                                              │
│   LAYER 3: DASHBOARD AGENT                                          │
│   ┌─────────────────────────────────────────────┐                   │
│   │  Renders Interactive HTML War Room Report    │                   │
│   └─────────────────────────────────────────────┘                   │
│                                                                     │
│   SUPPORT LAYER: Ollama Agentic System                              │
│   ┌──────────┐  ┌────────────┐  ┌──────────────┐                   │
│   │ Coder    │  │ Debugger   │  │ Reporter     │                   │
│   │ Agent    │  │ Agent      │  │ Agent        │                   │
│   └──────────┘  └────────────┘  └──────────────┘                   │
│        ↕              ↕               ↕                             │
│   ┌─────────────────────────────────────────────┐                   │
│   │  Next.js Mission Control + Node.js Backend  │                   │
│   └─────────────────────────────────────────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Multi-Agent Pipeline

The PEIP pipeline operates in **3 execution layers** with **4 specialized sub-agents**:

```
python main.py --live
       │
       ▼
  InputAgent ──────► Validates GitHub repo URL & auth token
       │
       ▼
  MasterAgent ─────► Orchestrates 4 sub-agents in sequence:
       │
       ├──► GitHistoryAgent ───── Analyzes commit patterns, churn rate,
       │                          bus factor, hotspot files
       │
       ├──► ComplexityAgent ───── Runs Radon AST analysis for cyclomatic
       │                          complexity & maintainability index
       │
       ├──► RiskAgent ─────────── Classifies repos (HEALTHY / WATCH / AT RISK)
       │                          using research-backed signal thresholds
       │
       └──► CEOReportAgent ────── Generates executive summary via LLaMa3
                                   with financial ROI calculations
       │
       ▼
  DashboardAgent ──► Renders interactive HTML War Room dashboard
                      with health scores, risk heatmaps, and recommendations
```

---

## 📁 Project Structure

```
SUNHACKS_FINAL/
│
├── main.py                         # 🚀 Main entrypoint (CLI: --demo / --live)
├── SETUP_GUIDE.md                  # Quick setup instructions
├── README.md                       # This file
│
├── peip_engine/                    # 🧠 Core Intelligence Engine
│   ├── agents/                     # Agent implementations
│   │   ├── input_agent.py          #   → Layer 1: GitHub validation
│   │   ├── master_agent.py         #   → Layer 2: Pipeline orchestrator
│   │   ├── git_history_agent.py    #   → Commit/churn/bus-factor analysis
│   │   ├── complexity_agent.py     #   → Radon-based AST complexity
│   │   ├── risk_agent.py           #   → Multi-signal risk classifier
│   │   ├── ceo_report_agent.py     #   → LLaMa3 executive report generator
│   │   ├── dashboard_agent.py      #   → Layer 3: HTML dashboard renderer
│   │   ├── health_score_agent.py   #   → Health scoring engine
│   │   ├── dora_agent.py           #   → DORA metrics evaluator
│   │   ├── bug_prediction_agent.py #   → Crash/bug forecaster
│   │   ├── bug_pattern_agent.py    #   → Pattern-based bug detection
│   │   ├── patch_agent.py          #   → Autonomous patch generator
│   │   └── dashboard_generator.py  #   → Dashboard template engine
│   │
│   ├── core/                       # Orchestration & state management
│   │   ├── orchestrator.py         #   → State-machine pipeline runner
│   │   ├── pipeline_state.py       #   → Pipeline state tracking
│   │   ├── agent_handoffs.py       #   → Inter-agent communication
│   │   ├── failure_handler.py      #   → Retry & fallback logic
│   │   ├── peip_analytics.py       #   → Demo signal profiles
│   │   ├── workspace_manager.py    #   → Workspace/clone management
│   │   └── shell_tool.py           #   → Shell command execution
│   │
│   └── services/                   # External service integrations
│       └── peip_ollama_service.py  #   → Ollama LLM API client
│
├── Ollama_Agentic_System/          # 🤖 Modular Agent UI + Backend
│   ├── frontend/                   #   → Next.js 15 Mission Control Dashboard
│   ├── backend/                    #   → Node.js/Express orchestration server
│   ├── agents/                     #   → Coder / Debugger / Reporter agents
│   │   ├── coder/                  #   → Auto code generation & editing
│   │   ├── debugger/               #   → Failure log analysis
│   │   └── reporter/               #   → Executive report synthesis
│   ├── shared/                     #   → Shared types, constants, utilities
│   ├── setup.ps1                   #   → Windows setup script
│   └── setup.sh                    #   → Linux/Mac setup script
│
├── reports/                        # 📊 Generated Reports
│   ├── PEIP_EXECUTIVE_REPORT.md    #   → CEO-level risk report
│   └── peip_interactive_report.html#   → Interactive War Room dashboard
│
├── peip_health_scores.json         # Health score output (demo mode)
├── peip_pipeline_output.json       # Full pipeline output (live mode)
├── peip_analytics_raw.json         # Raw analytics data
└── peip_analytics_v2.json          # Processed analytics data
```

---

## ⚙️ Prerequisites

Before running PEIP, ensure you have the following installed:

| Requirement | Version | Purpose |
|:---|:---|:---|
| **Python** | 3.10+ | Core pipeline engine |
| **Ollama** | Latest | Local LLM inference (LLaMa3) |
| **Node.js** | 18+ | Ollama Agentic System frontend/backend |
| **npm** | 9+ | Package management |
| **Git** | Latest | Repository cloning & analysis (live mode) |

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Albertpradeep-007/SUNHACKS-agentic-ai.git
cd SUNHACKS-agentic-ai
```

### 2. Install Python Dependencies

```bash
pip install requests radon pygments
```

### 3. Install & Start Ollama

```bash
# Download from https://ollama.com
# Then pull the LLaMa3 model:
ollama run llama3
```

> **Note:** Ollama must be running on `http://localhost:11434` for the agents to connect.

### 4. Setup the Ollama Agentic System (Optional)

**Windows (PowerShell):**
```powershell
cd Ollama_Agentic_System
./setup.ps1
```

**Linux/Mac:**
```bash
cd Ollama_Agentic_System
bash setup.sh
```

---

## 🎮 Usage

### Demo Mode (Quick Validation — No GitHub Token Needed)

```bash
python main.py --demo
```

Runs the pipeline with **pre-validated signal profiles** for 6 sample repositories. Great for quickly seeing the platform in action without any setup.

### Live Mode (Full Pipeline — Real GitHub Analysis)

```bash
python main.py --live
```

Prompts you for a **GitHub repository URL** and **personal access token**, then runs the full 4-agent intelligence pipeline:

1. **InputAgent** validates your GitHub credentials  
2. **MasterAgent** orchestrates all sub-agents  
3. **Sub-agents** analyze git history, code complexity, risk signals, and generate reports  
4. **DashboardAgent** renders the interactive War Room dashboard  

### Default Mode

```bash
python main.py
```

Defaults to demo mode for quick validation.

---

## 📊 Dashboard & Reports

After running the pipeline, PEIP generates:

| Output | Location | Description |
|:---|:---|:---|
| **Interactive Dashboard** | `reports/peip_interactive_report.html` | Full War Room dashboard with health scores, risk heatmaps, and recommendations |
| **CEO Executive Report** | `reports/PEIP_EXECUTIVE_REPORT.md` | Board-ready Markdown report with financial ROI analysis |
| **Health Scores** | `peip_health_scores.json` | JSON output with per-repo health scores |
| **Pipeline Output** | `peip_pipeline_output.json` | Complete pipeline data for all agents |

> 💡 **Tip:** Open `peip_interactive_report.html` in Chrome/Firefox for the best dashboard experience.

---

## 🔍 Agents Deep Dive

### InputAgent (`input_agent.py`)
- Validates GitHub repository URL and authentication token
- Builds session configuration for downstream agents
- Handles invalid inputs with retry logic

### GitHistoryAgent (`git_history_agent.py`)
- Analyzes commit patterns and frequency
- Calculates **code churn rate** (Munson & Elbaum 1998)
- Identifies **bus factor risk** (Spadini et al. 2018)
- Detects **hotspot files** with concentrated change patterns

### ComplexityAgent (`complexity_agent.py`)
- Runs **Radon AST analysis** on Python codebases
- Calculates **Cyclomatic Complexity** (McCabe 1976, IEEE)
- Computes **Maintainability Index** (Coleman et al. 1994)
- Grades functions from A (simple) to F (unmaintainable)

### RiskAgent (`risk_agent.py`)
- Multi-signal risk classifier using research-backed thresholds
- Classifications: `HEALTHY` → `WATCH` → `AT RISK`
- Correlates complexity, churn, bus factor, and DORA metrics
- Generates per-component signal breakdowns

### CEOReportAgent (`ceo_report_agent.py`)
- Generates executive summaries via **LLaMa3** local inference
- Calculates **fix-now vs. fix-later cost** using IBM's 100x multiplier
- Produces board-ready language with actionable recommendations
- Outputs structured Markdown reports

### DashboardAgent (`dashboard_agent.py`)
- Renders interactive HTML War Room dashboard
- Visualizes health scores with color-coded risk indicators
- Displays financial impact analysis and cost comparisons
- Generates downloadable report artifacts

### DORAAgent (`dora_agent.py`)
- Evaluates **DORA 2024/2025** engineering metrics:
  - Deployment Frequency
  - Lead Time for Changes  
  - Change Failure Rate
  - Mean Time to Recovery (MTTR)

### PatchAgent (`patch_agent.py`)
- Autonomously suggests code patches for identified risks
- Validates patch correctness before recommendation
- Focuses on reducing cyclomatic complexity

---

## 🤖 Ollama Agentic System

The `Ollama_Agentic_System/` directory contains a **modular, production-grade agentic framework** with:

- **Next.js 15 Mission Control Dashboard** — Real-time agent monitoring UI  
- **Node.js/Express Backend** — LangChain integration for agent orchestration  
- **3 Specialized Agent Clusters:**

| Agent | Role | Capabilities |
|:---|:---|:---|
| **Coder** | Code Generation | Auto-generates code, edits files, implements fixes |
| **Debugger** | Failure Analysis | Analyzes error logs, traces root causes |
| **Reporter** | Report Synthesis | Synthesizes outcomes into executive reports |

Each agent follows the **ReAct (Reasoning + Acting)** pattern with:
- `prompt.ts` — System prompts and personas
- `logic.ts` — Agentic loop execution strategy
- `tools.ts` — Specialized tools (FileSystem, ShellExec, etc.)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m "feat: add your feature"`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|:---|:---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `refactor:` | Code refactoring |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance tasks |

---

## 📚 Research References

All thresholds and metrics in PEIP are traceable to published research:

| Metric | Source |
|:---|:---|
| Cyclomatic Complexity | McCabe 1976 (IEEE) |
| Maintainability Index | Coleman et al. 1994 (IEEE) |
| Code Churn | Munson & Elbaum 1998 (IEEE) |
| Bus Factor | Spadini et al. 2018 (ESEC/FSE) |
| DORA Metrics | DORA 2024/2025 (Google) |
| Hotspot Detection | arXiv 2026 |
| 100x Fix Cost Multiplier | IBM Systems Sciences Institute |
| Technical Debt | Van Deursen 2014 |
| Radon Complexity Grades | Radon Documentation |

---

<div align="center">

**Built with ❤️ for SUNHACKS**

*Predictive Engineering Intelligence — Because the best bug fix is the one you never have to make.*

</div>
