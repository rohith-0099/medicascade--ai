"""
HuggingFace API Client with Improved Response Parsing
Handles all communication with HuggingFace Inference API
"""
import requests
import os
from typing import Dict, Any
import time
import json
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class HuggingFaceClient:
    """Client for HuggingFace Inference API with robust parsing"""
    
    def __init__(self):
        self.token = os.getenv("HF_API_TOKEN", "")
        if not self.token:
            print("⚠️  WARNING: HF_API_TOKEN not found in environment!")
        else:
            print(f"✅ HuggingFace API token loaded (starts with: {self.token[:10]}...)")
        
        self.base_url = "https://router.huggingface.co/models/"
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def query(self, model_id: str, payload: Dict, max_retries: int = 2) -> Any:
        """
        Query HuggingFace model
        
        Args:
            model_id: Model identifier (e.g., "google/gemma-2-9b-it")
            payload: Request payload with "inputs" key
            max_retries: Number of retries for model loading
        
        Returns:
            API response
        """
        url = self.base_url + model_id
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                # Model loading - wait and retry
                if response.status_code == 503:
                    if attempt < max_retries:
                        wait_time = 20 * (attempt + 1)
                        print(f"⏳ Model loading, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"error": "Model unavailable", "status_code": 503}
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.Timeout:
                print(f"⚠️ Timeout (attempt {attempt + 1})")
                if attempt >= max_retries:
                    return {"error": "Request timeout"}
            
            except requests.exceptions.RequestException as e:
                print(f"❌ API Error: {str(e)}")
                if attempt >= max_retries:
                    return {"error": str(e)}
        
        return {"error": "Max retries exceeded"}
    
    def extract_json_from_text(self, text: str) -> Dict:
        """
        Robust JSON extraction from AI text responses
        Handles various formats and markdown code blocks
        """
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        patterns = [
            r'```json\s*(.*?)\s*```',  # ```json {...} ```
            r'```\s*({\s*.*?}\s*)```',  # ``` {...} ```
            r'({[\s\S]*?})',  # Any {...} including multiline
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_text = match.group(1)
                    return json.loads(json_text)
                except:
                    continue
        
        # Last resort: extract key-value pairs manually
        result = {}
        
        # Look for common patterns
        diagnosis_match = re.search(r'"?primary[_\s]diagnosis"?\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        if diagnosis_match:
            result['primary_diagnosis'] = diagnosis_match.group(1)
        
        confidence_match = re.search(r'"?confidence"?\s*:\s*(\d+)', text)
        if confidence_match:
            result['confidence'] = int(confidence_match.group(1))
        
        reasoning_match = re.search(r'"?reasoning"?\s*:\s*"([^"]+)"', text, re.IGNORECASE)
        if reasoning_match:
            result['reasoning'] = reasoning_match.group(1)
        
        return result if result else {"error": "Could not parse response"}


# Global instance
hf_client = HuggingFaceClient()
