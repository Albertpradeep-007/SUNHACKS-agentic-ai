import os
import subprocess

class ShellExecutionTool:
    """
    Real-Time Shell Execution Tool
    Allows the AI agent to execute validation commands (e.g., pytest, npm test, python -m py_compile)
    to confirm correctness of AI-generated patches.
    """
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        
    def execute_command(self, command: str, timeout_seconds: int = 15) -> dict:
        """
        Executes a shell command inside the workspace directory.
        """
        print(f"  [ShellExecution] Running: `{command}`")
        try:
            result = subprocess.run(
                command,
                cwd=self.workspace_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": f"Command timed out after {timeout_seconds}s", "exit_code": -1}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}
