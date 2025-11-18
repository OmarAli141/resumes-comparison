"""
Main script to extract and parse resumes from PDF files.
Processes all PDFs in the data directory structure.
"""

import json
from pathlib import Path
from extract_text import extract_text_from_pdf
from resume_parser import parse_resume
from tqdm import tqdm


def process_resume_directory(directory: Path, category: str = None) -> list:
    """Process all PDFs in a directory."""
    pdf_files = list(directory.glob("*.pdf"))
    resumes = []
    
    for pdf_file in tqdm(pdf_files, desc=f"Processing {category or directory.name}"):
        # Extract text
        text = extract_text_from_pdf(pdf_file)
        
        if not text.strip():
            continue
        
        # Extract resume ID from filename (assuming format like "12345678.pdf")
        resume_id = pdf_file.stem
        
        # Parse resume
        resume_data = parse_resume(text, resume_id=resume_id, category=category or directory.name)
        resumes.append(resume_data)
    
    return resumes


def extract_all_resumes(data_root: Path = Path("data/data")) -> list:
    """Extract all resumes from the data directory structure."""
    all_resumes = []
    
    if not data_root.exists():
        print(f"Data directory not found: {data_root}")
        return []
    
    # Find all category directories
    category_dirs = [d for d in data_root.iterdir() if d.is_dir()]
    
    print(f"Found {len(category_dirs)} category directories")
    
    for category_dir in category_dirs:
        category = category_dir.name
        print(f"\nProcessing category: {category}")
        
        resumes = process_resume_directory(category_dir, category=category)
        all_resumes.extend(resumes)
        print(f"  Extracted {len(resumes)} resumes from {category}")
    
    return all_resumes


def main():
    """Main extraction function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract and parse resumes from PDFs")
    parser.add_argument("--data-dir", type=str, default="data/data", help="Root directory containing resume PDFs")
    parser.add_argument("--output", type=str, default="extracted_data/resumes_data_pdfplumber.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    data_root = Path(args.data_dir)
    output_file = Path(args.output)
    
    print("="*70)
    print("Resume Extraction and Parsing")
    print("="*70)
    
    # Extract all resumes
    all_resumes = extract_all_resumes(data_root)
    
    if not all_resumes:
        print("❌ No resumes extracted!")
        return
    
    # Save to JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"Saving {len(all_resumes)} resumes to {output_file}")
    print(f"{'='*70}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_resumes, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully saved {len(all_resumes)} resumes to {output_file}")
    
    # Print summary
    categories = {}
    for resume in all_resumes:
        cat = resume.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n📊 Summary by Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} resumes")


if __name__ == "__main__":
    main()

