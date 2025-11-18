"""
Extract text from PDF files using pdfplumber.
"""

import pdfplumber
from pathlib import Path
from typing import List, Dict


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    
    return text.strip()


def extract_texts_from_directory(directory: Path) -> List[Dict[str, str]]:
    """Extract text from all PDF files in a directory."""
    results = []
    
    pdf_files = list(directory.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {directory}")
    
    for pdf_file in pdf_files:
        print(f"Extracting: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)
        results.append({
            "file_name": pdf_file.name,
            "file_path": str(pdf_file),
            "text": text
        })
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <directory_path>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Directory not found: {directory}")
        sys.exit(1)
    
    results = extract_texts_from_directory(directory)
    print(f"\nExtracted text from {len(results)} PDF files")

