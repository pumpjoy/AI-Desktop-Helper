import ollama
import sys 
from typing import Optional, Dict, Any

class LocalLLMConnector:
    """
    Handles connection and model management for the local Ollama API.
    It checks model availability at startup and attempts to pull the model 
    if it is not found locally.
    """
    
    def __init__(self, model_name: str = "ibm/granite3.2:8b"):
        self.model: str = model_name
        self.client: ollama.Client = ollama.Client() 
        # is_model_ready will be set by is_available_and_pull_if_needed
        self.is_model_ready: bool = False 
        
        # The subsequent call to is_available_and_pull_if_needed() handles 
        # the initial availability check and pull.
        
        print(f"LocalLLMConnector initialized for model: {self.model}")

    def is_available_and_pull_if_needed(self) -> bool:
        """
        Checks if the model is locally available. 
        If not, it attempts to pull the model.
        Returns True if the model is ready, False otherwise.
        """
        print(f"Checking for local model: {self.model}...")
        
        try:
            # Check for model existence using client.show()
            self.client.show(self.model)
            print(f"✅ Model '{self.model}' is available locally.")
            self.is_model_ready = True
            return True
            
        except ollama.ResponseError as e:
            # Check for model not found (typically 404 or specific text)
            if "not found" in str(e).lower() or e.status_code == 404:
                print(f"⚠️ Model '{self.model}' not found locally. Starting pull...")
                return self._pull_model()
            else:
                print(f"🛑 CRITICAL ERROR: Ollama service issue. Is the service running? Details: {e}")
                self.is_model_ready = False
                return False
                
        except Exception as e:
            # Catch general connection/network errors
            print(f"🛑 CRITICAL ERROR: Cannot connect to Ollama service. Ensure service is running. Details: {e}")
            self.is_model_ready = False
            return False

    def _pull_model(self) -> bool:
        """
        Pulls the model from the Ollama registry and prints streamed progress.
        Returns True on successful pull, False on failure.
        """
        try:
            # We use typing.Dict here for safety, though Dict[str, Any] is better 
            # for the runtime type of the chunk.
            chunk: Dict[str, Any]
            for chunk in self.client.pull(self.model, stream=True):
                
                # If a chunk contains an error, raise it immediately
                if chunk.get('error'):
                    raise Exception(chunk['error'])

                if 'status' in chunk:
                    status = chunk['status']

                    # NOTE: These values might be None for certain status messages, 
                    # but casting them to int(0) handles the NoneType error robustly.
                    total = int(chunk.get('total', 0) or 0)
                    completed = int(chunk.get('completed', 0) or 0)

                    # Only show progress bar if total size is known, completed is tracked, 
                    # and the status is not a verification step ('digest').
                    if total > 0 and completed >= 0 and 'digest' not in status.lower():
                        # Calculate progress bar and percentage
                        progress_len = 20
                        fill_count = int(completed * progress_len / total)
                        percentage = (completed / total) * 100
                        
                        # Use rjust to ensure the '=' characters don't exceed the length
                        progress_bar = f"[{'='*fill_count:<{progress_len}}] {percentage:.2f}%"
                        sys.stdout.write(f"\r{status} {progress_bar}")
                        
                    elif 'digest' not in status.lower():
                        # Display status for non-download steps (e.g., verifying)
                        sys.stdout.write(f"\r{status}...")
                        
                    sys.stdout.flush()

            sys.stdout.write("\n")
            print(f"✅ Model '{self.model}' successfully pulled and ready.")
            self.is_model_ready = True
            return True

        except Exception as e:
            # Catch pull failures, including the internal chunk errors
            sys.stdout.write("\n")
            print(f"🛑 Error during model pull: {e}")
            self.is_model_ready = False
            return False
