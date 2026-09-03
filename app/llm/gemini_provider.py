from google.genai.errors import ServerError
import os
from google import genai
from google.genai import types
from app.llm.interface import LLMProvider
import time

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.client = genai.Client()
        self.model = 'gemini-3-flash-preview'
    
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0,
                    )
                )
                return response.text
            except ServerError as e:
                if attempt == 2:
                    raise e
                time.sleep(2)
        return response.text