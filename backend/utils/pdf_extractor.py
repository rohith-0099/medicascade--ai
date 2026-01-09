"""
PDF extraction utilities for Layer 0
Extracts text, tables, and images from PDF documents
"""
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
    """Handles all PDF extraction operations"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_text(self) -> str:
        """
        Extract all text from PDF using multiple methods
        
        Returns:
            Extracted text as string
        """
        text = ""
        
        # Method 1: Try PyPDF2 first (faster)
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
        
        # Method 2: If PyPDF2 fails or returns little text, try pdfplumber
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
        """
        Extract text using OCR for scanned PDFs
        
        Returns:
            OCR extracted text
        """
        text = ""
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(self.pdf_path, dpi=300)
            
            # Apply OCR to each page
            for i, image in enumerate(images):
                ocr_text = pytesseract.image_to_string(image)
                text += f"\n--- Page {i+1} ---\n{ocr_text}\n"
                
        except Exception as e:
            print(f"OCR extraction failed: {e}")
        
        return text.strip()
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF
        
        Returns:
            List of table dictionaries
        """
        tables = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            # Convert table to dict format
                            headers = table[0] if table[0] else [f"Column {i}" for i in range(len(table[0]))]
                            rows = table[1:]
                            
                            table_dict = {
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "headers": headers,
                                "rows": rows,
                                "data": []
                            }
                            
                            # Convert to list of dicts
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
        """
        Extract images from PDF and convert to base64
        
        Returns:
            List of base64 encoded images
        """
        images_base64 = []
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(self.pdf_path, dpi=200)
            
            for i, image in enumerate(images):
                # Convert PIL Image to base64
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                images_base64.append(img_str)
                
        except Exception as e:
            print(f"Image extraction failed: {e}")
        
        return images_base64
    
    def extract_embedded_images(self) -> List[str]:
        """
        Extract embedded images from PDF (X-rays, scans, etc.)
        
        Returns:
            List of base64 encoded embedded images
        """
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
                                # Extract image data
                                if '/Filter' in xobj:
                                    if xobj['/Filter'] == '/DCTDecode':
                                        # JPEG image
                                        data = xobj.get_data()
                                        img_str = base64.b64encode(data).decode()
                                        images_base64.append(img_str)
                                    elif xobj['/Filter'] == '/FlateDecode':
                                        # PNG-like image
                                        data = xobj.get_data()
                                        img_str = base64.b64encode(data).decode()
                                        images_base64.append(img_str)
                                        
        except Exception as e:
            print(f"Embedded image extraction failed: {e}")
        
        return images_base64
    
    def smart_extract(self) -> Tuple[str, List[str]]:
        """
        Intelligently extract text (try regular extraction first, fall back to OCR)
        
        Returns:
            Tuple of (extracted_text, list_of_image_base64)
        """
        # Try regular text extraction
        text = self.extract_text()
        
        # If very little text extracted, it might be a scanned PDF
        if len(text.strip()) < 50:
            print("Low text content detected, attempting OCR...")
            ocr_text = self.extract_text_with_ocr()
            if len(ocr_text) > len(text):
                text = ocr_text
        
        # Extract images
        images = self.extract_images()
        embedded_images = self.extract_embedded_images()
        
        # Combine all images
        all_images = images + embedded_images
        
        return text, all_images
