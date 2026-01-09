"""
HuggingFace Inference API Client
"""
import requests
from typing import Dict, Any, Optional, List
from config import settings
import time


class HuggingFaceClient:
    """Client for HuggingFace Inference API"""
    
    def __init__(self):
        self.api_token = settings.HUGGINGFACE_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        self.base_url = "https://api-inference.huggingface.co/models"
    
    def query_text_generation(self, model: str, prompt: str, max_length: int = 500,
                            temperature: float = 0.7) -> str:
        """
        Query text generation model
        
        Args:
            model: Model identifier on HuggingFace
            prompt: Input prompt
            max_length: Maximum response length
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        url = f"{self.base_url}/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_length,
                "temperature": temperature,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict):
                return result.get("generated_text", "")
            
            return ""
            
        except requests.exceptions.RequestException as e:
            print(f"HuggingFace API error for {model}: {e}")
            # If rate limited, wait and retry once
            if "503" in str(e) or "rate" in str(e).lower():
                print("Model loading or rate limited, waiting 10s and retrying...")
                time.sleep(10)
                try:
                    response = requests.post(url, headers=self.headers, json=payload, timeout=30)
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "")
                except:
                    pass
            return ""
    
    def query_classification(self, model: str, text: str) -> List[Dict[str, Any]]:
        """
        Query classification model
        
        Args:
            model: Model identifier
            text: Text to classify
            
        Returns:
            List of classification results
        """
        url = f"{self.base_url}/{model}"
        
        payload = {"inputs": text}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list):
                return result
            
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"HuggingFace classification error: {e}")
            return []
    
    def query_vision(self, model: str, image_data: bytes) -> str:
        """
        Query vision model with image
        
        Args:
            model: Vision model identifier
            image_data: Image bytes
            
        Returns:
            Model output/classification
        """
        url = f"{self.base_url}/{model}"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=image_data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    return result[0].get("label", str(result[0]))
                return str(result[0])
            elif isinstance(result, dict):
                return result.get("label", str(result))
            
            return str(result)
            
        except requests.exceptions.RequestException as e:
            print(f"HuggingFace vision error: {e}")
            return ""


# Global instance
hf_client = HuggingFaceClient()
