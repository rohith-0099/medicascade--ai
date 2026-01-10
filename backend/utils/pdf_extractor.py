
import io
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import base64
from typing import List, Dict, Any, Tuple
import re

class PDFExtractor:

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_text(self) -> str:
        
        text = ""
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
        
        if len(text.strip()) < 100:
            try:
                with pdfplumber.open(self.pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"pdfplumber extraction failed: {e}")
        
        return text.strip()
    
    def extract_text_with_ocr(self) -> str:
        
        text = ""
        
        try:
            images = convert_from_path(self.pdf_path, dpi=300)
            
            for i, image in enumerate(images):
                ocr_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n{ocr_text}\n"
                
        except Exception as e:
            print(f"OCR extraction failed: {e}")
        
        return text.strip()
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            headers = table[0] if table[0] else [f"Column {i}" for i in range(len(table[0]))]
                            rows = table[1:]
                            
                            table_dict = {
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "headers": headers,
                                "rows": rows,
                                "data": []
                            }
                            
                            for row in rows:
                                row_dict = {}
                                for i, header in enumerate(headers):
                                    if i < len(row):
                                        row_dict[header] = row[i]
                                table_dict["data"].append(row_dict)
                            
                            tables.append(table_dict)
                            
        except Exception as e:
            print(f"Table extraction failed: {e}")
        
        return tables
    
    def extract_images(self) -> List[str]:
        
        images_base64 = []
        
        try:
            images = convert_from_path(self.pdf_path, dpi=200)
            
            for i, image in enumerate(images):
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                images_base64.append(img_str)
                
        except Exception as e:
            print(f"Image extraction failed: {e}")
        
        return images_base64
    
    def extract_embedded_images(self) -> List[str]:
        
        images_base64 = []
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    if '/XObject' in page['/Resources']:
                        xobjects = page['/Resources']['/XObject'].get_object()
                        
                        for obj in xobjects:
                            xobj = xobjects[obj]
                            
                            if xobj['/Subtype'] == '/Image':
                                if '/Filter' in xobj:
                                    if xobj['/Filter'] == '/DCTDecode':
                                        data = xobj.get_data()
                                        img_str = base64.b64encode(data).decode()
                                        images_base64.append(img_str)
                                    elif xobj['/Filter'] == '/FlateDecode':
                                        data = xobj.get_data()
                                        img_str = base64.b64encode(data).decode()
                                        images_base64.append(img_str)
                                        
        except Exception as e:
            print(f"Embedded image extraction failed: {e}")
        
        return images_base64
    
    def smart_extract(self) -> Tuple[str, List[str]]:
        
        text = self.extract_text()
        text_len = len(text.strip())
        
        all_images = []
        
        if text_len >= 200:
            print(f"[PDF Extractor] Text-heavy document ({text_len} chars). Extracting embedded images only.")
            embedded_images = self.extract_embedded_images()
            all_images = embedded_images
            
        else:
            print(f"[PDF Extractor] Low text content ({text_len} chars). Treating as scanned document.")
            print("Attempting OCR...")
            ocr_text = self.extract_text_with_ocr()
            if len(ocr_text) > text_len:
                text = ocr_text
            
            print("Extracting full page renders...")
            page_images = self.extract_images()
            all_images = page_images
        
        return text, all_images
