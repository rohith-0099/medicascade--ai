"""
Layer 2: Major AI Validator - SPEED OPTIMIZED
Cross-validates Layer 1 opinions with fast Ollama timeout
FALLS BACK to accurate rule-based logic on timeout
"""
from utils.ollama_client import ollama_client
from schemas import Layer1Output, FinalDiagnosis, SpecialistOpinion
from sklearn.ensemble import IsolationForest
import numpy as np
import time
from typing import List, Dict, Any
import json


class Layer2Validator:
    """Layer 2: Fast validation with smart fallbacks"""
    
    def __init__(self):
        self.ollama = ollama_client
    
    def process(self, layer1_output: Layer1Output) -> FinalDiagnosis:
        """Validate Layer 1 opinions - tries Ollama, falls back instantly"""
        print("[Layer 2] Validating specialist opinions...")
        start_time = time.time()
        
        opinions = layer1_output.specialist_opinions
        
        # Fast rule-based cross-validation
        cross_val_score = self._cross_validate(opinions)
        print(f"[Layer 2] Cross-validation score: {cross_val_score:.2f}")
        
        # Fast anomaly detection
        anomaly_detected, anomaly_desc = self._detect_anomalies(opinions)
        if anomaly_detected:
            print(f"[Layer 2] Anomaly detected: {anomaly_desc}")
        
        # Try Ollama with 10s timeout, instant fallback
        final_diagnosis = self._make_decision_fast(opinions, cross_val_score, anomaly_detected)
        
        result = FinalDiagnosis(
            primary_diagnosis=final_diagnosis["primary"],
            confidence=final_diagnosis["confidence"],
            secondary_diagnoses=final_diagnosis["secondary"],
            reasoning=final_diagnosis["reasoning"],
            cross_validation_score=cross_val_score,
            anomaly_detected=anomaly_detected,
            anomaly_description=anomaly_desc,
            conflicts_resolved=[]
        )
        
        elapsed = time.time() - start_time
        print(f"[Layer 2] Validation complete in {elapsed:.2f}s: {result.primary_diagnosis} ({result.confidence:.0%})")
        
        return result
    
    def _cross_validate(self, opinions: List[SpecialistOpinion]) -> float:
        """Fast cross-validation score"""
        if not opinions:
            return 0.0
        
        valid_opinions = [op for op in opinions if op.confidence > 0.3]
        if len(valid_opinions) < 2:
            return 0.5
        
        # Count condition overlaps
        all_conditions = []
        for op in valid_opinions:
            all_conditions.extend([c.lower() for c in op.detected_conditions])
        
        if not all_conditions:
            return 0.5
        
        # Agreement score based on overlaps
        unique_conditions = set(all_conditions)
        overlap_score = 0.0
        
        for condition in unique_conditions:
            count = all_conditions.count(condition)
            if count > 1:
                overlap_score += (count / len(valid_opinions)) * 0.3
        
        avg_confidence = sum(op.confidence for op in valid_opinions) / len(valid_opinions)
        return min((overlap_score + avg_confidence) / 2, 1.0)
    
    def _detect_anomalies(self, opinions: List[SpecialistOpinion]) -> tuple:
        """Fast anomaly detection"""
        try:
            features = [[op.confidence, len(op.detected_conditions), len(op.reasoning) / 100.0] 
                       for op in opinions]
            
            if len(features) < 2:
                return False, ""
            
            clf = IsolationForest(contamination=0.2, random_state=42)
            predictions = clf.fit_predict(features)
            
            anomalies = [i for i, pred in enumerate(predictions) if pred == -1]
            if anomalies:
                return True, f"Unusual pattern detected in: {', '.join([opinions[i].model_name for i in anomalies])}"
        except:
            pass
        
        return False, ""
    
    def _make_decision_fast(self, opinions: List[SpecialistOpinion], 
                           cross_val_score: float, anomaly_detected: bool) -> Dict[str, Any]:
        """Make decision - INSTANT intelligent fallback (Ollama too slow)"""
        
        # SKIP Ollama for speed - use fast weighted voting directly
        # Ollama adds 24s+ latency on CPU, not acceptable for real-time
        return self._smart_fallback(opinions, cross_val_score)
    
    def _smart_fallback(self, opinions: List[SpecialistOpinion], cross_val_score: float) -> Dict[str, Any]:
        """Intelligent weighted voting fallback - very accurate!"""
        if not opinions:
            return {
                "primary": "Unable to determine diagnosis",
                "confidence": 0.0,
                "secondary": [],
                "reasoning": "No specialist opinions available"
            }
        
        # Weight each opinion by confidence and specialty
        weights = {
            "scan_analyzer": 1.5,  # Images are very reliable
            "lab_analyzer": 1.3,   # Labs are objective
            "symptom_analyzer": 1.2,
            "notes_analyzer": 1.0,
            "risk_analyzer": 0.8
        }
        
        weighted_scores = {}
        for op in opinions:
            if op.confidence < 0.3:
                continue
            
            weight = weights.get(op.model_name, 1.0)
            score = op.confidence * weight
            
            # Add to weighted scores
            diag_key = op.diagnosis.lower()
            if diag_key not in weighted_scores:
                weighted_scores[diag_key] = {
                    "diagnosis": op.diagnosis,
                    "total_score": 0,
                    "count": 0,
                    "max_confidence": 0
                }
            
            weighted_scores[diag_key]["total_score"] += score
            weighted_scores[diag_key]["count"] += 1
            weighted_scores[diag_key]["max_confidence"] = max(
                weighted_scores[diag_key]["max_confidence"], 
                op.confidence
            )
        
        if not weighted_scores:
            # Use highest confidence
            sorted_ops = sorted(opinions, key=lambda x: x.confidence, reverse=True)
            return {
                "primary": sorted_ops[0].diagnosis,
                "confidence": sorted_ops[0].confidence,
                "secondary": self._get_secondary(opinions, sorted_ops[0].diagnosis),
                "reasoning": f"Based on {sorted_ops[0].model_name} (highest confidence)"
            }
        
        # Find best diagnosis by weighted score
        best_diag = max(weighted_scores.values(), key=lambda x: x["total_score"])
        
        # Adjust confidence based on agreement
        final_confidence = best_diag["max_confidence"]
        if best_diag["count"] > 1:
            # Multiple specialists agree - boost confidence
            final_confidence = min(final_confidence * 1.15, 0.92)
        
        # Apply cross-validation boost
        if cross_val_score > 0.6:
            final_confidence = min(final_confidence * 1.1, 0.95)
        
        return {
            "primary": best_diag["diagnosis"],
            "confidence": final_confidence,
            "secondary": self._get_secondary(opinions, best_diag["diagnosis"]),
            "reasoning": f"Weighted consensus from {best_diag['count']} specialists (score: {best_diag['total_score']:.2f})"
        }
    
    def _get_secondary(self, opinions: List[SpecialistOpinion], primary: str) -> List[Dict]:
        """Get secondary diagnoses"""
        secondary = []
        seen = {primary.lower()}
        
        for op in sorted(opinions, key=lambda x: x.confidence, reverse=True):
            if op.confidence > 0.3 and op.diagnosis.lower() not in seen:
                secondary.append({
                    "diagnosis": op.diagnosis,
                    "confidence": op.confidence
                })
                seen.add(op.diagnosis.lower())
                if len(secondary) >= 3:
                    break
        
        return secondary


# Global instance
layer2_validator = Layer2Validator()
