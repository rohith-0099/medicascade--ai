
from utils.pdf_extractor import PDFExtractor
from utils.data_classifier import DataClassifier
from schemas import PatientData
from typing import Dict, Any
import time

class Layer0Processor:

    def __init__(self):
        self.classifier = DataClassifier()
    
    def process(self, pdf_path: str, scan_path: str = None) -> PatientData:
        
        print(f"[Layer 0] Processing PDF: {pdf_path}")
        if scan_path:
            print(f"[Layer 0] Processing Dedicated Scan: {scan_path}")
            
        start_time = time.time()
        
        extractor = PDFExtractor(pdf_path)
        
        print("[Layer 0] Extracting text...")
        text, pdf_images = extractor.smart_extract()
        
        images = []
        
        if scan_path:
            import base64
            try:
                with open(scan_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    images = [encoded_string]
                    print("[Layer 0] Using dedicated scan image for analysis")
            except Exception as e:
                print(f"[Layer 0] Error reading scan image: {e}")
                images = pdf_images
        else:
            images = pdf_images
        
        print("[Layer 0] Extracting tables...")
        tables = extractor.extract_tables()
        
        print("[Layer 0] Classifying text sections...")
        classified_sections = self.classifier.classify_sections(text)
        
        print("[Layer 0] Extracting structured data...")
        
        patient_info = {}
        if classified_sections.get("patient_demographics"):
            patient_info = self.classifier.extract_patient_info(
                classified_sections["patient_demographics"]
            )
        
        lab_results = {}
        if classified_sections.get("lab_results"):
            lab_results = self.classifier.extract_lab_values(
                classified_sections["lab_results"]
            )
        
        for table in tables:
            lab_results.update(self._extract_lab_from_table(table))
        
        patient_data = PatientData(
            patient_info=patient_info,
            symptoms=classified_sections.get("symptoms", ""),
            lab_results=lab_results,
            clinical_notes=classified_sections.get("clinical_notes", ""),
            images=images,
            raw_text=text
        )
        
        elapsed = time.time() - start_time
        print(f"[Layer 0] Processing complete in {elapsed:.2f}s")
        
        return patient_data
    
    def _extract_lab_from_table(self, table: Dict[str, Any]) -> Dict[str, Any]:
        
        lab_data = {}
        
        try:
            headers = table.get("headers", [])
            rows = table.get("data", [])
            
            test_col = None
            value_col = None
            
            for i, header in enumerate(headers):
                header_lower = str(header).lower()
                if any(k in header_lower for k in ['test', 'parameter', 'name']):
                    test_col = header
                if any(k in header_lower for k in ['value', 'result', 'level']):
                    value_col = header
            
            if test_col and value_col:
                for row in rows:
                    if test_col in row and value_col in row:
                        test_name = str(row[test_col]).strip()
                        test_value = str(row[value_col]).strip()
                        if test_name and test_value:
                            lab_data[test_name] = test_value
        
        except Exception as e:
            print(f"Lab table extraction error: {e}")
        
        return lab_data

layer0_processor = Layer0Processor()
