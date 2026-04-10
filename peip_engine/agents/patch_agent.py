import os
import json
from peip_ollama_service import stream_ollama
from shell_tool import ShellExecutionTool

def run_patch_agent(repo_name: str, local_repo_path: str, complexity_data: dict) -> dict:
    """
    Ollama Orchestration (Beyond Summaries):
    If ComplexityAgent finds complex functions, OllamaAgent reads the source code 
    and streams a refactored, highly optimized patch immediately.
    Then, it verifies the code via the ShellExecutionTool.
    """
    print(f"\n[PatchAgent] Analyzing complexity data for {repo_name}...")
    
    patches_generated = []
    
    # Extract the worst files identified by the ComplexityAgent
    files = complexity_data.get("files", {})
    if not files:
        print("  [PatchAgent] No complex files identified for patching.")
        return {"patches": patches_generated}
    
    shell = ShellExecutionTool(local_repo_path)
    
    # We only patch files with Grade C, D, E, or F.
    for rel_path, metrics in files.items():
        grade = metrics.get("cc_grade", "A")
        if grade in ["A", "B"]:
            continue
            
        print(f"  [PatchAgent] Generating patch for {rel_path} (Grade {grade})...")
        full_path = os.path.join(local_repo_path, rel_path)
        
        if not os.path.exists(full_path):
            print(f"  [PatchAgent] x File not found: {full_path}")
            continue
            
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except:
            continue
            
        prompt = f"""
You are an Expert AI Code Refactoring Agent.
The following `{rel_path}` file from the `{repo_name}` repository has a Cyclomatic Complexity grade of {grade}. 

Please rewrite the code to significantly lower its complexity and improve maintainability.
Output ONLY valid code in a single code block. Do not provide explanations.

```python
{code_content}
```
"""
        
        print("  [PatchAgent] ⚡ Requesting Refactoring Patch via LLaMa3...")
        response = ""
        for chunk in stream_ollama("llama3", prompt, temperature=0.2):
            response += chunk
            
        # Extract code block
        patched_code = response.split("```")[1] if "```" in response else response
        if patched_code.startswith("python\n"): patched_code = patched_code[7:]
        
        # Save patched code to file
        patch_file_path = full_path + ".patched"
        with open(patch_file_path, "w", encoding="utf-8") as pf:
            pf.write(patched_code.strip())
            
        # Validate patch syntax (Real-Time Shell Execution Tool)
        print("  [PatchAgent] Validating syntax of generated patch...")
        validation = shell.execute_command(f"python -m py_compile {patch_file_path}")
        
        patch_status = "VERIFIED_SUCCESS" if validation["success"] else "VERIFIED_FAIL"
        if not validation["success"]:
            print(f"  [PatchAgent] ❌ Patch validation failed: {validation['stderr']}")
        else:
            print("  [PatchAgent] ✅ Patch compiled perfectly!")
            
        patches_generated.append({
            "file": rel_path,
            "original_grade": grade,
            "patch_path": patch_file_path,
            "validation_status": patch_status
        })

    return {"patches": patches_generated}
