from abc import ABC, abstractmethod
class LLMProvider(ABC):
    @abstractmethod
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Takes a system instruction and user prompt, returns the LLM's text response."""
        pass