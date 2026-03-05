"""
Layer 1 Specialists — 5 Parallel Models
Wires all 5 architecture-defined specialists and runs them in parallel with ThreadPoolExecutor.

ARCHITECTURE:
  Specialist 1: scan_analyzer       → google/medgemma-4b-it       (Medical Imaging)
  Specialist 2: symptom_analyzer    → UFNLP/gatortron-medium       (Symptoms & Clinical Notes)
  Specialist 3: lab_analyzer        → google/medgemma-4b-it        (Lab Results)
  Specialist 4: literature_analyzer → microsoft/BioGPT-Large       (Biomedical Literature)
  Specialist 5: risk_analyzer       → LightGBM + OpenMed-434M      (Patient Risk Scoring)
"""

from specialists.symptom_analyzer import symptom_analyzer, notes_analyzer
from specialists.lab_analyzer import lab_analyzer
from specialists.scan_analyzer import scan_analyzer
from specialists.literature_analyzer import literature_analyzer
from specialists.risk_analyzer import risk_analyzer
from schemas import PatientData, Layer1Output, SpecialistOpinion
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class Layer1Specialists:

    def __init__(self):
        self.specialists = {
            "scan": scan_analyzer,          # Specialist 1: MedGemma-4B (imaging)
            "symptom": symptom_analyzer,    # Specialist 2: GatorTron-medium (NER)
            "lab": lab_analyzer,            # Specialist 3: MedGemma-4B (lab)
            "literature": literature_analyzer,  # Specialist 4: BioGPT-Large
            "risk": risk_analyzer,          # Specialist 5: LightGBM + OpenMed-434M
        }
        print("[Layer 1] Initialized with 5 specialists:")
        for k, v in self.specialists.items():
            print(f"   • {k}: {getattr(v, 'model_name', k)}")

    def process(self, patient_data: PatientData) -> Layer1Output:
        print(f"\n[Layer 1] Launching {len(self.specialists)} specialist models in parallel...")
        start_time = time.time()

        opinions = []
        task_map = {
            "scan":       self._run_scan_analyzer,
            "symptom":    self._run_symptom_analyzer,
            "lab":        self._run_lab_analyzer,
            "literature": self._run_literature_analyzer,
            "risk":       self._run_risk_analyzer,
        }

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {
                executor.submit(fn, patient_data): name
                for name, fn in task_map.items()
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    opinion = future.result(timeout=90)
                    opinions.append(opinion)
                    print(f"[Layer 1] ✅ {name}: {opinion.diagnosis[:60]} ({opinion.confidence:.0%})")
                except Exception as e:
                    print(f"[Layer 1] ❌ {name} error: {e}")
                    opinions.append(SpecialistOpinion(
                        model_name=f"{name}_analyzer",
                        diagnosis=f"{name} analysis unavailable",
                        confidence=0.0,
                        reasoning=f"Error during specialist execution: {str(e)}"
                    ))

        elapsed = time.time() - start_time
        print(f"[Layer 1] All {len(opinions)} specialists completed in {elapsed:.2f}s")

        return Layer1Output(
            specialist_opinions=opinions,
            processing_time=elapsed
        )

    # ── Specialist runners ────────────────────────────────────────────────────

    def _run_scan_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Specialist 1 — Medical Imaging (MedGemma-4B vision)"""
        return scan_analyzer.analyze(data.images or [])

    def _run_symptom_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Specialist 2 — Symptoms & Clinical Notes (GatorTron NER)"""
        text = data.symptoms or ""
        if data.clinical_notes:
            text = text + "\n" + data.clinical_notes
        if data.raw_text and len(text) < 200:
            text += "\n" + data.raw_text[:1500]
        return symptom_analyzer.analyze(text)

    def _run_lab_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Specialist 3 — Lab Results (MedGemma-4B)"""
        # Pass both structured lab_results dict and raw_text for regex extraction
        lab_input = data.lab_results or {}
        if data.raw_text:
            lab_input = str(lab_input) + "\n" + data.raw_text[:1000]
        return lab_analyzer.analyze(lab_input)

    def _run_literature_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Specialist 4 — Biomedical Literature Matching (BioGPT-Large)"""
        # Combine symptoms + notes + raw text for comprehensive literature match
        combined = " ".join(filter(None, [
            data.symptoms or "",
            data.clinical_notes or "",
            str(data.lab_results or ""),
            (data.raw_text or "")[:1500]
        ]))
        return literature_analyzer.analyze(combined)

    def _run_risk_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Specialist 5 — Patient Risk Scoring (LightGBM + OpenMed-434M)"""
        patient_info = dict(data.patient_info or {})
        # Augment with full text for feature extraction
        if data.raw_text:
            patient_info["medical_history"] = patient_info.get("medical_history", "") + "\n" + data.raw_text[:1200]
        if data.symptoms:
            patient_info["symptoms"] = data.symptoms
        return risk_analyzer.analyze(patient_info)


layer1_specialists = Layer1Specialists()
