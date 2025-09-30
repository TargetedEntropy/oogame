import json
import requests
from typing import Optional, Dict, List, Generator
from dataclasses import dataclass, asdict
import time


@dataclass
class Message:
    role: str
    content: str


class OllamaService:
    def __init__(self, host_url: str = "http://localhost:11434"):
        self.host_url = host_url.rstrip("/")
        self.timeout = 600  # 10 minutes
        self.keep_alive = "60m"  # 60 minutes

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.host_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> Optional[List[str]]:
        """List available models."""
        try:
            response = requests.get(f"{self.host_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except requests.RequestException as e:
            print(f"Error listing models: {e}")
        return None

    def chat(
        self,
        model: str,
        messages: List[Message],
        response_format: Optional[Dict] = None,
        stream: bool = True,
    ) -> Generator[str, None, None]:
        """
        Send chat request to Ollama and yield response chunks.

        Args:
            model: Model name (e.g., "gemma3n:e4b")
            messages: List of conversation messages
            response_format: Optional JSON schema for structured output
            stream: Whether to stream the response

        Yields:
            Response chunks as strings
        """
        endpoint = f"{self.host_url}/api/chat"

        payload = {
            "model": model,
            "messages": [asdict(msg) for msg in messages],
            "stream": stream,
            "keep_alive": self.keep_alive,
            "options": {"temperature": 0.7, "top_p": 0.9, "seed": 42},
        }

        if response_format:
            payload["format"] = response_format

        try:
            response = requests.post(
                endpoint, json=payload, stream=stream, timeout=self.timeout
            )

            if response.status_code != 200:
                yield f"Error: {response.status_code} - {response.text}"
                return

            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk:
                                content = chunk["message"].get("content", "")
                                if content:
                                    yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                if "message" in data:
                    yield data["message"].get("content", "")

        except requests.Timeout:
            yield "Error: Request timed out. Please check your Ollama service."
        except requests.RequestException as e:
            yield f"Error: {str(e)}"

    def chat_sync(
        self,
        model: str,
        messages: List[Message],
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Send chat request and return complete response.

        Args:
            model: Model name
            messages: List of conversation messages
            response_format: Optional JSON schema for structured output

        Returns:
            Complete response as string
        """
        response_parts = []
        for chunk in self.chat(model, messages, response_format, stream=True):
            response_parts.append(chunk)
        return "".join(response_parts)

    def generate_with_retry(
        self,
        model: str,
        messages: List[Message],
        response_format: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Optional[str]:
        """
        Generate response with retry logic for better reliability.

        Args:
            model: Model name
            messages: List of conversation messages
            response_format: Optional JSON schema
            max_retries: Maximum number of retry attempts

        Returns:
            Response string or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                response = self.chat_sync(model, messages, response_format)
                if not response.startswith("Error:"):
                    return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff

        return None

    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.host_url}/api/pull"
        payload = {"name": model_name, "stream": False}

        try:
            response = requests.post(endpoint, json=payload, timeout=3600)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error pulling model: {e}")
            return False
