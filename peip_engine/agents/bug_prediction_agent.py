"""
BugPredictionAgent — Deep Source-code Analysis for Vulnerabilities and Crashes

Uses Ollama LLaMa3 to analyze the exact source code of the most complex files
in the local workspace, predicting future crashes and vulnerabilities in
simple natural language.
"""

import os
from peip_engine.services.peip_ollama_service import OllamaAgentService

def run_bug_prediction(repo_name: str, local_path: str, complexity_output: dict) -> dict:
    highest_cc_file = None
    highest_cc = -1
    
    # 1. Identify the absolute worst file in the local workspace based on Complexity
    if complexity_output and "files" in complexity_output:
        for file_path, cmplx in complexity_output["files"].items():
            if cmplx.get("cc_max", 0) > highest_cc:
                highest_cc = cmplx.get("cc_max", 0)
                highest_cc_file = file_path
                
    if not highest_cc_file or highest_cc < 10: # Only predict if it's somewhat risky
        return {"predictions": "Code is secure and well structured. No immediate crashes predicted."}

    # 2. Extract exact source code block
    target_disk_path = os.path.join(local_path, highest_cc_file.replace("/", os.sep))
    if not os.path.exists(target_disk_path):
        return {"error": "File not found locally."}
        
    try:
        with open(target_disk_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    # Truncate if massive
    if len(code) > 8000:
        code = code[:8000] + "\n... (truncated)"

    # 3. Stream to LLaMa3
    ollama = OllamaAgentService('llama3')
    if not ollama.is_online():
        return {"error": "Ollama is completely offline."}

    prompt = (
        "You are a Senior Security and Systems Engineer. I am providing you the EXACT source code "
        f"for `{highest_cc_file}`, which currently has a huge cyclomatic complexity of {highest_cc}.\n\n"
        "Your job:\n"
        "1. Predict EXACT CRASHES or BUGS that are vulnerable to happen in the future under load.\n"
        "2. Explain your prediction in SIMPLE NATURAL LANGUAGE.\n"
        "3. Provide EXACT updates and recommendations on how to fix the specific lines of code.\n\n"
        "FORMAT YOUR RESPONSE IN CLEAN MARKDOWN.\n\n"
        "SOURCE CODE:\n```python\n"
        f"{code}\n```"
    )

    result = {"target_file": highest_cc_file, "cc": highest_cc}
    
    try:
        ai_response = ollama.ask(prompt, {"repo": repo_name})
        result["predictions"] = ai_response
    except Exception as e:
        result["error"] = str(e)
        
    return result
