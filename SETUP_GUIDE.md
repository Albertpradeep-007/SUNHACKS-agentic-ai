# Predictive Engineering Intelligence Platform (PEIP)
**Setup & Execution Guide**

Welcome to PEIP! This platform uses an autonomous multi-agent architecture powered by **LLaMa3** to statically analyze codebases, predict future software crashes, calculate Executive Tech-Debt ROI, and autonomously generate code patches.

Follow these simple steps to run the pipeline on your machine.

---

## 🛠️ Step 1: Install Dependencies
Ensure you have **Python 3.10+** installed. Check your version by opening a terminal and running `python --version`.

Open a terminal inside the unzipped `SUNHACKS_FINAL` folder and install the required Python libraries:

```bash
pip install -r requirements.txt
```
*(Note: If `requirements.txt` does not exist, run: `pip install requests radon pygments`)*

## 🦙 Step 2: Install & Start Ollama
Since PEIP requires 100% data privacy, all AI processing happens locally on your machine.

1. Download and install Ollama from [https://ollama.com/](https://ollama.com/)
2. Open a new terminal window and download the LLaMa3 model:
   ```bash
   ollama run llama3
   ```
3. Ensure that the Ollama service is running in the background. It must be active on `http://localhost:11434` for the agents to connect!

## 🚀 Step 3: Run the Pipeline!
With your dependencies installed and Ollama running seamlessly in the background, you're ready to run the orchestration engine.

Open your terminal in the `SUNHACKS_FINAL` folder and run:

```bash
python main.py --live
```

**During execution, the Orchestrator will:**
1. Dynamically mock or clone the target engineering repository.
2. Spin up the `ComplexityAgent` to run deep AST (Abstract Syntax Tree) analysis.
3. Spin up the `BugPredictionAgent` to generate exact crash forecasts using LLaMa3.
4. Spin up the `PatchAgent` to suggest and validate fixes.
5. Compile all calculations (Financial ROI) into an interactive dashboard.

## 📊 Step 4: View the War Room Dashboard
Once you see the terminal output say `[OK] Interactive HTML Report saved to: reports\peip_interactive_report.html`, PEIP has finished!

Open the following file in Google Chrome, Firefox, or Safari to view the executive dashboard:
**`reports/peip_interactive_report.html`**

Enjoy predictive engineering!
