
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')  # Updated to latest stable model
            print("✅ Gemini API configured")
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
    
    def generate_medical_explanation(self, prompt: str, max_tokens: int = 800) -> str:
        
        if not self.model:
            return None
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                )
            )
            
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return None

gemini_client = GeminiClient()
