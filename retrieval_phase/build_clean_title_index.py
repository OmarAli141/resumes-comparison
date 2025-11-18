"""
Rebuild job_titles_index with clean, professional job titles only.
Extracts titles from category field and work_experience with proper cleaning.
"""

import json
import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

ROOT = Path(__file__).parent.parent
CHROMA_PATH = ROOT / "chroma_db"

# Setup
client = chromadb.PersistentClient(path=str(CHROMA_PATH))
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get or create collection
title_collection = client.get_or_create_collection(
    name="job_titles_index",
    embedding_function=embed_fn
)

# Job title keywords
JOB_TITLE_KEYWORDS = [
    "ACCOUNTANT", "ANALYST", "ENGINEER", "MANAGER", "DEVELOPER", "DIRECTOR",
    "SPECIALIST", "CONSULTANT", "DESIGNER", "ARCHITECT", "ADMINISTRATOR",
    "COORDINATOR", "EXECUTIVE", "OFFICER", "REPRESENTATIVE", "ASSISTANT",
    "LEAD", "SENIOR", "JUNIOR", "ASSOCIATE", "SUPERVISOR", "TECHNICIAN",
    "FINANCIAL", "BUSINESS", "DATA", "SOFTWARE", "SYSTEMS", "PROJECT"
]

SENIORITY_KEYWORDS = {
    "senior": ["senior", "sr", "lead", "principal", "head", "chief", "director", "vp", "vice president"],
    "mid": ["mid", "mid-level", "intermediate", "experienced", "professional"],
    "junior": ["junior", "jr", "entry", "associate", "assistant", "trainee", "intern", "internship"],
    "intern": ["intern", "internship", "trainee", "student"]
}


def extract_clean_title(text: str, category: str = "") -> str:
    """Extract a clean, professional job title from text."""
    if not text:
        return ""
    
    text = str(text).strip()
    
    # Remove common prefixes/suffixes that indicate it's not a title
    text = re.sub(r'^(years|year|domain|experience|with|having|skilled|focused|working|hard-working|dedicated)\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+(years|year|experience|skilled|at|in|with|focused|on|working).*$', '', text, flags=re.IGNORECASE)
    
    # Remove incomplete sentences (ending with "At", "On", "In", "With")
    text = re.sub(r'\s+(At|On|In|With|Skilled|Focused|Working|Hard-Working|Dedicated)$', '', text)
    
    # Split into words and check if it looks like a title
    words = text.split()
    
    # If too long, it's probably not a title
    if len(words) > 8:
        return ""
    
    # Check if it contains job title keywords
    text_upper = text.upper()
    has_keyword = any(keyword in text_upper for keyword in JOB_TITLE_KEYWORDS)
    
    if not has_keyword:
        return ""
    
    # Clean up: remove extra spaces, capitalize properly
    title = " ".join(words)
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Title case (but preserve acronyms)
    title_parts = []
    for word in title.split():
        if word.isupper() and len(word) > 1:
            title_parts.append(word)
        else:
            title_parts.append(word.capitalize())
    
    title = " ".join(title_parts)
    
    # Limit length
    if len(title) > 60:
        return ""
    
    return title


def detect_seniority(title: str) -> str:
    """Detect seniority level from job title."""
    title_lower = title.lower()
    
    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return level
    
    return "mid"  # Default to mid-level if not specified


def build_title_index():
    """Build clean job titles index from resumes."""
    # Try cleaned file first
    path = ROOT / "extracted_data_cleaned" / "resumes_cleaned.json"
    if not path.exists():
        path = ROOT / "extracted_data" / "resumes_data_pdfplumber.json"
    
    if not path.exists():
        print("❌ Resumes file not found!")
        return
    
    print(f"Loading resumes from: {path}")
    with open(path, "r", encoding="utf-8") as f:
        resumes = json.load(f)
    
    print(f"Processing {len(resumes)} resumes...")
    
    # Clear existing collection
    try:
        existing_ids = title_collection.get(include=[])["ids"]
        if existing_ids:
            print(f"Clearing {len(existing_ids)} existing titles...")
            title_collection.delete(ids=existing_ids)
    except:
        pass
    
    titles_seen = set()
    new_docs, new_ids, new_metas = [], [], []
    
    for i, r in enumerate(resumes):
        resume_id = r.get("ID") or r.get("id", f"resume_{i}")
        category = r.get("category", "").strip()
        work_exp = r.get("work_experience", "")
        summary = r.get("summary", "")
        
        # Priority 1: Use category as base title
        title = ""
        if category and category.upper() not in ["UNKNOWN", "N/A", ""]:
            # Category is usually the job type (e.g., "ACCOUNTANT", "FINANCIAL ANALYST")
            title = category.title()
        
        # Priority 2: Extract from work experience (first job title mentioned)
        if not title and work_exp:
            # Look for patterns like "Job Title at Company" or "Job Title, Company"
            patterns = [
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:at|@|in|for|,)\s+',
                r'^([A-Z][a-z]+(?:\s+(?:Senior|Junior|Lead|Principal|Associate|Assistant|Manager|Director|Analyst|Engineer|Developer|Specialist|Consultant|Coordinator))+)',
            ]
            
            first_lines = work_exp.split('\n')[:3]
            for line in first_lines:
                line = line.strip()
                if len(line) > 100:
                    continue
                
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        candidate = match.group(1).strip()
                        if len(candidate.split()) <= 5:
                            title = extract_clean_title(candidate, category)
                            if title:
                                break
                if title:
                    break
        
        # Priority 3: Extract from summary
        if not title and summary:
            words = summary.split()[:15]
            candidate = " ".join(words)
            title = extract_clean_title(candidate, category)
        
        # Clean the title
        if title:
            title = extract_clean_title(title, category)
        
        if not title or len(title) < 3:
            continue
        
        # Skip duplicates
        title_normalized = title.upper().strip()
        if title_normalized in titles_seen:
            continue
        
        titles_seen.add(title_normalized)
        
        # Detect seniority
        seniority = detect_seniority(title)
        
        # Store
        doc_id = f"title_{resume_id}_{i}"
        new_ids.append(doc_id)
        new_docs.append(title)
        new_metas.append({
            "resume_id": str(resume_id),
            "category": category,
            "seniority": seniority
        })
    
    # Add to collection
    if new_docs:
        print(f"\nAdding {len(new_docs)} clean job titles to index...")
        title_collection.add(ids=new_ids, documents=new_docs, metadatas=new_metas)
        print(f"✅ Successfully indexed {len(new_docs)} job titles")
        
        # Show statistics
        seniority_counts = {}
        for meta in new_metas:
            level = meta.get("seniority", "mid")
            seniority_counts[level] = seniority_counts.get(level, 0) + 1
        
        print(f"\n📊 Seniority breakdown:")
        for level, count in sorted(seniority_counts.items()):
            print(f"   {level}: {count}")
    else:
        print("No titles to add")


if __name__ == "__main__":
    print("=" * 70)
    print("Building Clean Job Titles Index")
    print("=" * 70)
    build_title_index()
