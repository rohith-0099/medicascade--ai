"""
Ollama API Client for local LLM inference (Layer 2 & 3)
"""
import requests
import json
from typing import Dict, Any, Optional
from config import settings


class OllamaClient:
    """Client for interacting with Ollama local LLM"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Ollama API error: {e}")
            return ""
    
    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Assistant's response
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            print(f"Ollama chat error: {e}")
            return ""
    
    def classify_text(self, text: str, categories: list) -> str:
        """
        Classify text into one of the given categories
        
        Args:
            text: Text to classify
            categories: List of category names
            
        Returns:
            Category name
        """
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following medical text into ONE of these categories: {categories_str}

Text: {text}

Return ONLY the category name, nothing else."""
        
        result = self.generate(prompt, temperature=0.1)
        return result.strip()
    
    def extract_structured_data(self, text: str, fields: list) -> Dict[str, Any]:
        """
        Extract structured data from unstructured text
        
        Args:
            text: Unstructured text
            fields: List of field names to extract
            
        Returns:
            Dictionary with extracted data
        """
        fields_str = ", ".join(fields)
        prompt = f"""Extract the following fields from this medical text: {fields_str}

Text: {text}

Return as JSON object with field names as keys. If a field is not found, use null."""
        
        result = self.generate(prompt, temperature=0.1)
        
        try:
            # Try to parse JSON from response
            return json.loads(result)
        except json.JSONDecodeError:
            # If not valid JSON, return empty dict
            return {}


# Global instance
ollama_client = OllamaClient()
