"""
Ollama Client - Local LLM Integration
Provides AI capabilities using locally running Ollama
"""
import requests
import json
import os
from typing import Optional, Dict, Any


class OllamaClient:
    """Client for interacting with Ollama LLM"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self._test_connection()
    
    def _test_connection(self):
        """Test if Ollama is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.ok:
                print(f"✅ Ollama connected ({self.model})")
            else:
                print(f"⚠️  Ollama service not responding")
        except Exception as e:
            print(f"⚠️  Ollama not accessible: {e}")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Generate text using Ollama
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text or None if error
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"Ollama error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Ollama generation error: {e}")
            return None
    
    def chat(self, messages: list, temperature: float = 0.7) -> Optional[str]:
        """
        Chat with Ollama using message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
        
        Returns:
            Response text or None
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                message = result.get('message', {})
                return message.get('content', '')
            else:
                return None
                
        except Exception as e:
            print(f"Ollama chat error: {e}")
            return None
    
    def classify_text(self, text: str, categories: list = None) -> dict:
        """
        Classify medical text into categories (for Layer 0)
        Fast classification with timeout
        """
        if categories is None:
            categories = ["symptoms", "lab_results", "clinical_notes", "patient_info"]
        
        prompt = f"""Classify this medical text into ONE category: {', '.join(categories)}

Text: {text[:500]}

Return only the category name."""
        
        try:
            response = self.generate(prompt, temperature=0.1, max_tokens=10)
            if response:
                category = response.strip().lower()
                # Match to closest category
                for cat in categories:
                    if cat in category or category in cat:
                        return {"category": cat, "confidence": 0.85}
                return {"category": categories[0], "confidence": 0.50}
        except:
            pass
        
        return {"category": "unknown", "confidence": 0.30}
    
    def extract_structured_data(self, text: str, data_type: str = "patient") -> dict:
        """
        Extract structured data from medical text (for Layer 0)
        Returns dict with extracted fields
        """
        prompt = f"""Extract {data_type} information from this text:

{text[:1000]}

Return key facts as brief JSON."""
        
        try:
            response = self.generate(prompt, temperature=0.2, max_tokens=100)
            if response:
                # Try to parse as JSON
                import json
                try:
                    return json.loads(response)
                except:
                    # Return as raw text
                    return {"extracted_text": response[:200], "raw": True}
        except:
            pass
        
        return {"error": "extraction_failed", "raw_text": text[:200]}


# Global instance
ollama_client = OllamaClient()
