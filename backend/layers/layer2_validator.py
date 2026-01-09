"""
Layer 2: Major AI Validator
Cross-validates Layer 1 opinions and makes final diagnosis decision
"""
from utils.ollama_client import ollama_client
from schemas import Layer1Output, FinalDiagnosis, SpecialistOpinion
from sklearn.ensemble import IsolationForest
import numpy as np
import time
from typing import List, Dict, Any
import json


class Layer2Validator:
    """Layer 2: Validates and consolidates Layer 1 outputs"""
    
    def __init__(self):
        self.ollama = ollama_client
    
    def process(self, layer1_output: Layer1Output) -> FinalDiagnosis:
        """
        Validate Layer 1 opinions and make final diagnosis
        
        Args:
            layer1_output: All specialist opinions from Layer 1
            
        Returns:
            FinalDiagnosis with validated conclusion
        """
        print("[Layer 2] Validating specialist opinions...")
        start_time = time.time()
        
        opinions = layer1_output.specialist_opinions
        
        # Step 1: Cross-validate opinions
        cross_val_score = self._cross_validate(opinions)
        print(f"[Layer 2] Cross-validation score: {cross_val_score:.2f}")
        
        # Step 2: Detect and resolve conflicts
        conflicts = self._detect_conflicts(opinions)
        resolved_conflicts = []
        
        if conflicts:
            print(f"[Layer 2] Resolving {len(conflicts)} conflicts...")
            resolved_conflicts = self._resolve_conflicts(conflicts, opinions)
        
        # Step 3: Anomaly detection
        anomaly_detected, anomaly_desc = self._detect_anomalies(opinions)
        
        if anomaly_detected:
            print(f"[Layer 2] Anomaly detected: {anomaly_desc}")
        
        # Step 4: Make final decision using Ollama
        final_diagnosis = self._make_decision(opinions, cross_val_score, resolved_conflicts, anomaly_detected)
        
        # Step 5: Build FinalDiagnosis object
        result = FinalDiagnosis(
            primary_diagnosis=final_diagnosis["primary"],
            confidence=final_diagnosis["confidence"],
            secondary_diagnoses=final_diagnosis["secondary"],
            reasoning=final_diagnosis["reasoning"],
            cross_validation_score=cross_val_score,
            anomaly_detected=anomaly_detected,
            anomaly_description=anomaly_desc,
            conflicts_resolved=resolved_conflicts
        )
        
        elapsed = time.time() - start_time
        print(f"[Layer 2] Validation complete in {elapsed:.2f}s: {result.primary_diagnosis} ({result.confidence:.0%})")
        
        return result
    
    def _cross_validate(self, opinions: List[SpecialistOpinion]) -> float:
        """Calculate cross-validation score based on opinion agreement"""
        if not opinions:
            return 0.0
        
        # Filter out low-confidence opinions
        valid_opinions = [op for op in opinions if op.confidence > 0.3]
        
        if len(valid_opinions) < 2:
            return 0.5  # Not enough data for cross-validation
        
        # Check for diagnosis agreement
        diagnoses = [op.diagnosis.lower() for op in valid_opinions]
        conditions = []
        for op in valid_opinions:
            conditions.extend([c.lower() for c in op.detected_conditions])
        
        # Count overlapping conditions
        if not conditions:
            return 0.5
        
        unique_conditions = list(set(conditions))
        overlap_score = 0.0
        
        for condition in unique_conditions:
            count = conditions.count(condition)
            if count > 1:
                # More specialists agreeing increases score
                overlap_score += (count / len(valid_opinions)) * 0.3
        
        # Average confidence from all specialists
        avg_confidence = sum(op.confidence for op in valid_opinions) / len(valid_opinions)
        
        # Combined score
        cross_val_score = min((overlap_score + avg_confidence) / 2, 1.0)
        
        return cross_val_score
    
    def _detect_conflicts(self, opinions: List[SpecialistOpinion]) -> List[Dict[str, Any]]:
        """Detect conflicting diagnoses"""
        conflicts = []
        
        # Compare pairs of opinions
        for i in range(len(opinions)):
            for j in range(i + 1, len(opinions)):
                op1 = opinions[i]
                op2 = opinions[j]
                
                # Skip low-confidence opinions
                if op1.confidence < 0.4 or op2.confidence < 0.4:
                    continue
                
                # Check if diagnoses contradict
                diag1_words = set(op1.diagnosis.lower().split())
                diag2_words = set(op2.diagnosis.lower().split())
                
                # If no common words and both confident, potential conflict
                if len(diag1_words & diag2_words) == 0 and op1.confidence > 0.6 and op2.confidence > 0.6:
                    conflicts.append({
                        "model1": op1.model_name,
                        "diagnosis1": op1.diagnosis,
                        "model2": op2.model_name,
                        "diagnosis2": op2.diagnosis
                    })
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict], opinions: List[SpecialistOpinion]) -> List[str]:
        """Resolve conflicts using Ollama"""
        resolutions = []
        
        for conflict in conflicts[:3]:  # Resolve up to 3 conflicts
            prompt = f"""Two medical AI models have conflicting diagnoses:

Model 1 ({conflict['model1']}): {conflict['diagnosis1']}
Model 2 ({conflict['model2']}): {conflict['diagnosis2']}

Are these diagnoses actually conflicting, or could they both be true (e.g., comorbid conditions)?
Provide a brief resolution in one sentence."""
            
            resolution = self.ollama.generate(prompt, temperature=0.5)
            resolutions.append(resolution.strip())
        
        return resolutions
    
    def _detect_anomalies(self, opinions: List[SpecialistOpinion]) -> tuple:
        """Detect anomalous patterns using Isolation Forest"""
        try:
            # Extract numerical features
            features = []
            for op in opinions:
                features.append([
                    op.confidence,
                    len(op.detected_conditions),
                    len(op.reasoning) / 100.0,  # Normalized text length
                ])
            
            if len(features) < 2:
                return False, ""
            
            # Fit Isolation Forest
            clf = IsolationForest(contamination=0.2, random_state=42)
            predictions = clf.fit_predict(features)
            
            # Check if any opinions are outliers
            anomalies = [i for i, pred in enumerate(predictions) if pred == -1]
            
            if anomalies:
                anomalous_models = [opinions[i].model_name for i in anomalies]
                return True, f"Unusual pattern detected in: {', '.join(anomalous_models)}"
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
        
        return False, ""
    
    def _make_decision(self, opinions: List[SpecialistOpinion], cross_val_score: float,
                      conflicts: List[str], anomaly_detected: bool) -> Dict[str, Any]:
        """Make final diagnosis decision using Ollama"""
        
        # Build comprehensive prompt
        opinions_text = "\n\n".join([
            f"**{op.model_name}**\n"
            f"Diagnosis: {op.diagnosis}\n"
            f"Confidence: {op.confidence:.0%}\n"
            f"Reasoning: {op.reasoning}\n"
            f"Conditions: {', '.join(op.detected_conditions) if op.detected_conditions else 'None'}"
            for op in opinions
        ])
        
        prompt = f"""You are a senior medical AI reviewing opinions from 5 specialist AI models. Your job is to make a final diagnosis.

SPECIALIST OPINIONS:
{opinions_text}

CROSS-VALIDATION SCORE: {cross_val_score:.0%}
ANOMALY DETECTED: {'Yes' if anomaly_detected else 'No'}

Analyze all opinions and provide:
1. PRIMARY DIAGNOSIS (most likely condition)
2. CONFIDENCE (0-100%)
3. SECONDARY DIAGNOSES (alternative possibilities, max 3)
4. REASONING (why you chose this diagnosis, which specialists agreed, how you resolved conflicts)

Format as JSON:
{{
  "primary": "diagnosis name",
  "confidence": 0.85,
  "secondary": [
    {{"diagnosis": "alternative 1", "confidence": 0.60}},
    {{"diagnosis": "alternative 2", "confidence": 0.45}}
  ],
  "reasoning": "explanation"
}}

Respond with ONLY the JSON object."""
        
        response = self.ollama.generate(prompt, temperature=0.6)
        
        # Parse JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group(0))
                
                # Ensure confidence is float between 0 and 1
                if "confidence" in decision:
                    conf = decision["confidence"]
                    if conf > 1:
                        decision["confidence"] = conf / 100.0
                
                return decision
        
        except Exception as e:
            print(f"Decision parsing error: {e}")
        
        # Fallback: use highest confidence opinion
        return self._fallback_decision(opinions)
    
    def _fallback_decision(self, opinions: List[SpecialistOpinion]) -> Dict[str, Any]:
        """Fallback decision logic"""
        # Sort by confidence
        sorted_ops = sorted(opinions, key=lambda x: x.confidence, reverse=True)
        
        if sorted_ops:
            primary_op = sorted_ops[0]
            
            secondary = []
            for op in sorted_ops[1:4]:
                if op.confidence > 0.3:
                    secondary.append({
                        "diagnosis": op.diagnosis,
                        "confidence": op.confidence
                    })
            
            return {
                "primary": primary_op.diagnosis,
                "confidence": primary_op.confidence,
                "secondary": secondary,
                "reasoning": f"Primary diagnosis from {primary_op.model_name} with highest confidence. " + primary_op.reasoning
            }
        
        return {
            "primary": "Unable to determine diagnosis",
            "confidence": 0.0,
            "secondary": [],
            "reasoning": "Insufficient data from specialist models"
        }


# Global instance
layer2_validator = Layer2Validator()
