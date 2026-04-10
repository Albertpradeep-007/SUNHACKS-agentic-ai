import os
import shutil
import tempfile
import subprocess
from contextlib import contextmanager

class WorkspaceManager:
    """
    Local Workspace Manager (Power Layer)
    Clones GitHub repositories into a temporary local workspace to allow
    PyDriller to perform deep AST and full commit history mining at high speed and high confidence.
    """

    def __init__(self, base_workspace_dir: str = None):
        if base_workspace_dir is None:
            self.base_workspace = os.path.join(os.getcwd(), 'peip_workspace')
        else:
            self.base_workspace = base_workspace_dir
            
        os.makedirs(self.base_workspace, exist_ok=True)

    @contextmanager
    def clone_repo(self, repo_url: str, repo_name: str, token: str = None):
        """
        Context manager that securely clones the repo to a local path, yields it, 
        and optionally cleans it up.
        """
        local_path = os.path.join(self.base_workspace, repo_name)
        
        # If it already exists, just return it (caching)
        if os.path.exists(local_path):
            print(f"  [WorkspaceManager] Using cached local clone: {local_path}")
            yield local_path
            return
            
        print(f"  [WorkspaceManager] Deep cloning {repo_url} into {local_path} for PyDriller...")
        
        # Inject token into URL if provided
        clone_url = repo_url
        if token and "https://" in repo_url:
            clone_url = repo_url.replace("https://", f"https://{token}@")
            
        try:
            # Clone with full history for PyDriller
            subprocess.run(
                ["git", "clone", clone_url, local_path], 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            yield local_path
        except subprocess.CalledProcessError as e:
            print(f"  [WorkspaceManager] x Failed to clone {repo_name}: {e}")
            yield None
        finally:
            # We don't automatically delete the repo here so subsequent agents (like Complexity/Radon)
            # can use the exact same local clone.
            pass

    def cleanup(self):
        """Wipes the entire workspace to save disk space."""
        if os.path.exists(self.base_workspace):
            print(f"  [WorkspaceManager] Cleaning up temporary workspace {self.base_workspace}")
            try:
                # To handle Windows permission issues securely:
                def on_rm_error(func, path, exc_info):
                    os.chmod(path, 0o777)
                    os.remove(path)
                shutil.rmtree(self.base_workspace, onerror=on_rm_error)
            except Exception as e:
                print(f"  [WorkspaceManager] Warning: cleanup failed: {e}")
