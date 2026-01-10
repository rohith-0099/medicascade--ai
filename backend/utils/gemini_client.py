
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            # Using transport='rest' to avoid gRPC SSL certificate issues in restricted networks
            genai.configure(api_key=api_key, transport='rest')
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Stable production model
            print("✅ Gemini API configured")
        else:
            self.model = None
            print("⚠️ Gemini API key not found")
    
    def generate_medical_explanation(self, prompt: str, max_tokens: int = 800) -> str:
        
        if not self.model:
            return None
        
        try:
            # Disable safety filters for medical analysis in hackathon context
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                ),
                safety_settings=safety_settings
            )
            
            if response and response.text:
                return response.text
            else:
                print(f"⚠️ Gemini returned empty response or was blocked: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No feedback'}")
        except Exception as e:
            print(f"❌ Gemini API CRITICAL error: {str(e)}")
            if "quota" in str(e).lower():
                print("⚠️ Gemini Quota Exceeded")
            elif "400" in str(e):
                print("⚠️ Gemini Bad Request - Check model name or parameters")
        
        return None

gemini_client = GeminiClient()
