"""
Risk Factor Analyzer - Layer 1 Specialist
Assesses patient risk based on demographics, history, and lifestyle factors
"""
from schemas import SpecialistOpinion
from typing import Dict, Any


class RiskAnalyzer:
    """Analyzes patient risk factors"""
    
    def __init__(self):
        pass
    
    def analyze(self, patient_info: Dict[str, Any], medical_history: str = "") -> SpecialistOpinion:
        """
        Analyze risk factors
        
        Args:
            patient_info: Patient demographics
            medical_history: Medical history text
            
        Returns:
            SpecialistOpinion with risk assessment
        """
        if not patient_info:
            return SpecialistOpinion(
                model_name="risk_analyzer",
                diagnosis="Insufficient patient data",
                confidence=0.0,
                reasoning="No patient information available"
            )
        
        risk_factors = []
        risk_score = 0.0
        max_risk = 0.0
        
        # Age-based risks
        try:
            age = patient_info.get("age")
            if age:
                age_num = int(str(age).split()[0]) if isinstance(age, str) else int(age)
                
                if age_num > 65:
                    risk_factors.append(f"Advanced age ({age_num}) - increased risk for cardiovascular disease, cancer")
                    risk_score += 0.3
                elif age_num > 50:
                    risk_factors.append(f"Age {age_num} - moderate age-related risks")
                    risk_score += 0.15
                
                max_risk += 0.3
        except (ValueError, TypeError):
            pass
        
        # Gender-based risks
        gender = str(patient_info.get("gender", "")).lower()
        if "male" in gender and "fe" not in gender:
            risk_factors.append("Male gender - higher cardiovascular risk")
            risk_score += 0.1
        elif "female" in gender:
            risk_factors.append("Female gender - specific screening recommendations")
            risk_score += 0.05
        max_risk += 0.1
        
        # Medical history
        if medical_history:
            history_lower = medical_history.lower()
            
            if any(word in history_lower for word in ["diabetes", "diabetic"]):
                risk_factors.append("History of diabetes - increased complications risk")
                risk_score += 0.25
                max_risk += 0.25
            
            if any(word in history_lower for word in ["hypertension", "high blood pressure"]):
                risk_factors.append("History of hypertension - cardiovascular risk")
                risk_score += 0.20
                max_risk += 0.20
            
            if any(word in history_lower for word in ["smoking", "smoker", "tobacco"]):
                risk_factors.append("Smoking history - major risk factor")
                risk_score += 0.30
                max_risk += 0.30
            
            if any(word in history_lower for word in ["family history", "genetic"]):
                risk_factors.append("Family history present - genetic predisposition")
                risk_score += 0.15
                max_risk += 0.15
            
            if any(word in history_lower for word in ["cancer", "tumor"]):
                risk_factors.append("Cancer history - requires monitoring")
                risk_score += 0.25
                max_risk += 0.25
        
        # Calculate overall risk
        if max_risk > 0:
            normalized_risk = min(risk_score / max_risk, 1.0)
        else:
            normalized_risk = 0.3  # Default moderate risk
        
        # Determine risk level
        if normalized_risk > 0.7:
            risk_level = "HIGH RISK"
            confidence = 0.85
        elif normalized_risk > 0.4:
            risk_level = "MODERATE RISK"
            confidence = 0.75
        else:
            risk_level = "LOW RISK"
            confidence = 0.70
        
        # Build reasoning
        if risk_factors:
            reasoning = "Risk factors identified:\n" + "\n".join(f"• {rf}" for rf in risk_factors)
        else:
            reasoning = "No significant risk factors identified in available data"
        
        return SpecialistOpinion(
            model_name="risk_analyzer",
            diagnosis=f"Patient Risk Assessment: {risk_level}",
            confidence=confidence,
            reasoning=reasoning,
            detected_conditions=risk_factors,
            key_findings={
                "risk_score": normalized_risk,
                "risk_level": risk_level,
                "num_factors": len(risk_factors)
            }
        )


# Global instance
risk_analyzer = RiskAnalyzer()
