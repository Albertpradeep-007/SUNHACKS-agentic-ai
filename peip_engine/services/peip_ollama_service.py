import requests
import json

class OllamaAgentService:
    """
    Python bridge to the local Ollama instance.
    Connects your PEIP Python agents to the LLaMa3 model for advanced reasoning.
    """
    def __init__(self, model="llama3", base_url="http://localhost:11434/api"):
        self.model = model
        self.base_url = base_url

    def is_online(self) -> bool:
        try:
            r = requests.get("http://localhost:11434/")
            return r.status_code == 200
        except:
            return False

    def ask(self, system_prompt: str, user_data: dict) -> str:
        """Single-turn query to Ollama with transient crash retry logic."""
        import time
        full_prompt = f"{system_prompt}\n\nHere is the data context:\n{json.dumps(user_data, indent=2)}\n\nResponse:"
        
        for attempt in range(3):
            try:
                response = requests.post(f"{self.base_url}/generate", json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                }, timeout=120)
                
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
                
                # If Ollama runner crashes (500), it's a known VRAM glitch. We retry.
                if response.status_code == 500 and attempt < 2:
                    print(f"  [WARN] Ollama runner crashed (500). Retrying... ({attempt+1}/3)")
                    time.sleep(2)
                    continue
                    
                return f"[Error: Ollama returned {response.status_code} - {response.text}]"
            except Exception as e:
                return f"[Ollama Connection Failed: {e}]"

def stream_ollama(model: str, prompt: str, temperature: float = 0.2):
    """
    Generator that streams the response from Ollama.
    """
    import requests
    import json
    try:
        response = requests.post(f"http://localhost:11434/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature}
        }, stream=True, timeout=120)
        
        if response.status_code != 200:
            yield f"[Ollama Error: {response.status_code} - {response.text}]"
            return
            
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                yield chunk.get("response", "")
                if chunk.get("done"):
                    break
    except Exception as e:
        yield f"\n[Ollama Connection Failed: {e}]"
