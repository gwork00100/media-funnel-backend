import subprocess

class OllamaAgent:
    def __init__(self, config):
        self.config = config

    def run(self, prompt: str):
        try:
            cmd = [
                "ollama",
                "run",
                self.config.get("model", "llama2"),
                "--prompt",
                prompt
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error running Ollama: {e.stderr}"

# AGENT_CONFIG should be in a separate file (agent_config.py),
# but okay for testing here
AGENT_CONFIG = {
    "model": "llama2",
    "temperature": 0.7,
    "max_tokens": 500,
}
