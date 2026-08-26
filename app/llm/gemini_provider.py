import os
from google import genai
from google.genai import types
from app.llm.interface import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.client = genai.Client()
        self.model = 'gemini-3.6-flash'
    
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
            )
        )
        return response.text