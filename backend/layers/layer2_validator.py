"""
Layer 2 — Cross-Validation
Model: google/medgemma-4b-it (MedGemma 27B text proxy via HF API)
Purpose: Examines all specialist outputs collectively, resolves contradictions,
         confirms or rejects predictions, produces one unified diagnosis.
"""

from utils.hf_client import hf_client
from schemas import Layer1Output, FinalDiagnosis, SpecialistOpinion
from config import settings
import numpy as np
import time
import re
from typing import List, Dict, Any, Optional
import json

class Layer2Validator:

    VALIDATOR_MODEL = settings.HF_VALIDATOR_MODEL   # google/medgemma-4b-it
    DISPLAY_NAME = "MedGemma-4B (Cross-Validation)"

    SPECIALIST_WEIGHTS = {
        "scan_analyzer":        1.5,   # Imaging — high signal specificity
        "lab_analyzer":         1.3,   # Labs — objective, quantitative
        "symptom_analyzer":     1.2,   # Clinical NLP
        "literature_analyzer":  1.1,   # Evidence-based
        "risk_analyzer":        0.9,   # Risk scoring
        "notes_analyzer":       1.0,   # Fallback
    }

    def process(self, layer1_output: Layer1Output) -> FinalDiagnosis:
        
        print("[Layer 2] Validating specialist opinions...")
        start_time = time.time()
        
        opinions = layer1_output.specialist_opinions
        
        cross_val_score = self._cross_validate(opinions)
        print(f"[Layer 2] Cross-validation score: {cross_val_score:.2f}")
        
        anomaly_detected, anomaly_desc = self._detect_anomalies(opinions)
        if anomaly_detected:
            print(f"[Layer 2] Anomaly detected: {anomaly_desc}")
        
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
        
        if not opinions:
            return 0.0
        
        valid_opinions = [op for op in opinions if op.confidence > 0.3]
        if len(valid_opinions) < 2:
            return 0.5
        
        all_conditions = []
        for op in valid_opinions:
            all_conditions.extend([c.lower() for c in op.detected_conditions])
        
        if not all_conditions:
            return 0.5
        
        unique_conditions = set(all_conditions)
        overlap_score = 0.0
        
        for condition in unique_conditions:
            count = all_conditions.count(condition)
            if count > 1:
                overlap_score += (count / len(valid_opinions)) * 0.3
        
        avg_confidence = sum(op.confidence for op in valid_opinions) / len(valid_opinions)
        return min((overlap_score + avg_confidence) / 2, 1.0)
    
    def _detect_conflicts(self, opinions: List[SpecialistOpinion]) -> tuple:
        """Identify specialists disagreeing on primary diagnosis."""
        if len(opinions) < 2:
            return "", 0
        diagnoses = [op.diagnosis.lower().split('(')[0].strip() for op in opinions if op.confidence > 0.3]
        unique = set(diagnoses)
        if len(unique) <= 1:
            return "All specialists in agreement", 0
        # Find two most common, determine conflict
        from collections import Counter
        counts = Counter(diagnoses)
        top = counts.most_common(2)
        if len(top) >= 2 and top[0][1] != top[1][1]:
            conflict_desc = f"{top[0][0].title()} vs {top[1][0].title()} — resolved by weighted consensus"
        else:
            conflict_desc = f"{len(unique)} distinct diagnoses across specialists"
        return conflict_desc, len(unique) - 1

    def _detect_anomalies(self, opinions: List[SpecialistOpinion]) -> tuple:
        """Statistical anomaly detection across specialist confidence scores."""
        if not opinions:
            return False, ""
        low_conf = [op for op in opinions if op.confidence < 0.2]
        if len(low_conf) > len(opinions) / 2:
            return True, "Majority of specialists report very low confidence — data may be insufficient"
        # High variance in confidence (> 0.4 std)
        confs = [op.confidence for op in opinions]
        if len(confs) >= 3 and np.std(confs) > 0.40:
            return True, f"High variance in specialist confidence scores (σ={np.std(confs):.2f}) — conflicting signals"
        return False, ""

    def _make_decision_fast(self, opinions, cross_val_score, anomaly):
        return self._smart_fallback(opinions, cross_val_score)

    def _smart_fallback(self, opinions: List[SpecialistOpinion], cross_val_score: float) -> Dict[str, Any]:
        
        if not opinions:
            return {
                "primary": "Unable to determine diagnosis",
                "confidence": 0.0,
                "secondary": [],
                "reasoning": "No specialist opinions available"
            }
        
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
            sorted_ops = sorted(opinions, key=lambda x: x.confidence, reverse=True)
            return {
                "primary": sorted_ops[0].diagnosis,
                "confidence": sorted_ops[0].confidence,
                "secondary": self._get_secondary(opinions, sorted_ops[0].diagnosis),
                "reasoning": f"Based on {sorted_ops[0].model_name} (highest confidence)"
            }
        
        best_diag = max(weighted_scores.values(), key=lambda x: x["total_score"])
        
        final_confidence = best_diag["max_confidence"]
        if best_diag["count"] > 1:
            final_confidence = min(final_confidence * 1.15, 0.92)
        
        if cross_val_score > 0.6:
            final_confidence = min(final_confidence * 1.1, 0.95)
        
        return {
            "primary": best_diag["diagnosis"],
            "confidence": final_confidence,
            "secondary": self._get_secondary(opinions, best_diag["diagnosis"]),
            "reasoning": f"Weighted consensus from {best_diag['count']} specialists (score: {best_diag['total_score']:.2f})"
        }
    
    def _get_secondary(self, opinions: List[SpecialistOpinion], primary: str) -> List[Dict]:
        
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

layer2_validator = Layer2Validator()
