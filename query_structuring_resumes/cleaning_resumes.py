"""
Clean and restructure resume data from pdfplumber extraction.
Fixes polluted job_title fields and properly structures all sections.
"""

import json
from pathlib import Path
import re

input_file = Path("extracted_data/resumes_data_pdfplumber.json")
output_file = Path("extracted_data/resumes_cleaned.json")  # New cleaned file

with open(input_file, "r", encoding="utf-8") as f:
    raw_resumes = json.load(f)

cleaned_resumes = []

# Common job title keywords to identify real titles
JOB_TITLE_KEYWORDS = [
    "ACCOUNTANT", "ANALYST", "ENGINEER", "MANAGER", "DEVELOPER", "DIRECTOR",
    "SPECIALIST", "CONSULTANT", "DESIGNER", "ARCHITECT", "ADMINISTRATOR",
    "COORDINATOR", "EXECUTIVE", "OFFICER", "REPRESENTATIVE", "ASSISTANT",
    "LEAD", "SENIOR", "JUNIOR", "ASSOCIATE", "SUPERVISOR", "TECHNICIAN"
]

def extract_clean_job_title(raw_title: str, summary: str) -> str:
    """Extract clean job title from polluted field."""
    if not raw_title:
        return "N/A"
    
    raw_title = str(raw_title).strip()
    
    # Split on common delimiters that indicate summary/other content
    delimiters = [
        " Professional Summary ", " Summary ", " Experience ", " Highlights ",
        "PROFESSIONAL SUMMARY", "SUMMARY", "EXPERIENCE", "HIGHLIGHTS",
        "Objective", "OBJECTIVE", "Profile", "PROFILE"
    ]
    
    for delimiter in delimiters:
        if delimiter in raw_title:
            raw_title = raw_title.split(delimiter)[0].strip()
    
    # Split into lines and find the best title candidate
    lines = [l.strip() for l in raw_title.split("\n") if l.strip()]
    
    # Look for short lines that contain job title keywords
    for line in lines[:5]:  # Check first 5 lines
        line_upper = line.upper()
        # Check if line is short (likely a title) and contains job keywords
        if len(line) < 100:
            # Check for job title keywords
            has_keyword = any(keyword in line_upper for keyword in JOB_TITLE_KEYWORDS)
            # Check if it doesn't look like a sentence (no periods, short)
            is_title_like = len(line.split()) < 8 and "." not in line[:20]
            
            if has_keyword or is_title_like:
                # Clean up the title
                clean = line.strip()
                # Remove extra whitespace
                clean = re.sub(r'\s+', ' ', clean)
                # Limit length
                if len(clean) > 80:
                    clean = clean[:80].strip()
                return clean
    
    # Fallback: take first line if it's reasonably short
    if lines:
        first_line = lines[0].strip()
        if len(first_line) < 100:
            return re.sub(r'\s+', ' ', first_line[:80])
    
    # Last resort: try to extract from summary if available
    if summary:
        summary_upper = summary.upper()
        for keyword in JOB_TITLE_KEYWORDS:
            if keyword in summary_upper:
                # Find the phrase containing the keyword
                words = summary.split()
                for i, word in enumerate(words):
                    if keyword.lower() in word.lower():
                        # Get surrounding words (up to 5 words total)
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        title_phrase = " ".join(words[start:end])
                        if len(title_phrase) < 80:
                            return title_phrase.title()
    
    return "N/A"

def clean_skills_field(skills: str, experience: str, summary: str) -> str:
    """Clean and extract skills from polluted skills field."""
    if not skills:
        return ""
    
    skills = str(skills).strip()
    
    # If skills field is too long (likely polluted with experience), extract keywords
    if len(skills) > 500:
        # Extract common skill keywords
        all_text = f"{summary} {experience} {skills}".lower()
        
        # Common skills across different domains
        skill_patterns = [
            r'\b(excel|sql|python|java|javascript|react|node\.js|html|css)\b',
            r'\b(gaap|ifrs|quickbooks|sap|oracle|tableau|power\s*bi)\b',
            r'\b(accounting|audit|tax|reconciliation|bookkeeping)\b',
            r'\b(project\s*management|agile|scrum|devops|ci/cd)\b',
            r'\b(aws|azure|gcp|docker|kubernetes)\b'
        ]
        
        found_skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            found_skills.update([m.lower() for m in matches])
        
        if found_skills:
            return ", ".join(sorted(list(found_skills))[:20])
    
    # If skills field is reasonable length, clean it up
    # Remove "Work History" or similar prefixes
    skills = re.sub(r'^(Work History|Experience|Summary)[\s:]*', '', skills, flags=re.IGNORECASE)
    skills = re.sub(r'\s+', ' ', skills)
    
    # Limit length
    if len(skills) > 1000:
        skills = skills[:1000] + "..."
    
    return skills.strip()

def clean_text_field(text: str, max_length: int = None) -> str:
    """Clean and normalize text field."""
    if not text:
        return ""
    
    text = str(text).strip()
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()

for i, r in enumerate(raw_resumes):
    raw_title = str(r.get("job_title", "")).strip()
    summary = str(r.get("summary", "")).strip()
    experience = str(r.get("work_experience", "")).strip()
    education = str(r.get("education", "")).strip()
    skills = str(r.get("skills", "")).strip()
    
    # Fix 1: Extract clean job title
    clean_title = extract_clean_job_title(raw_title, summary)
    
    # Fix 2: If summary is empty but job_title contains summary text, extract it
    if not summary and ("Professional Summary" in raw_title or "Summary" in raw_title):
        # Try to extract summary from polluted job_title
        summary_match = re.search(r'(?:Professional\s+Summary|Summary)[\s:]*\s*(.+?)(?:\n|$)', raw_title, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
    
    # Fix 3: Clean skills field
    clean_skills = clean_skills_field(skills, experience, summary)
    
    # Fix 4: Clean all text fields
    clean_summary = clean_text_field(summary, max_length=1000)
    clean_education = clean_text_field(education, max_length=2000)
    clean_experience = clean_text_field(experience, max_length=5000)
    
    # Final cleaned resume structure - exact fields as requested (no job_title)
    cleaned_resume = {
        "ID": str(r.get("id", f"resume_{i}")),
        "category": str(r.get("category", "UNKNOWN")).strip().upper(),
        "summary": clean_summary or "No summary available",
        "work_experience": clean_experience or "No experience listed",
        "education": clean_education or "Not specified",
        "skills": clean_skills or "Not specified"
    }
    
    cleaned_resumes.append(cleaned_resume)

# Save cleaned version to new file
output_file.parent.mkdir(parents=True, exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cleaned_resumes, f, ensure_ascii=False, indent=2)

print(f"✅ Cleaned and restructured {len(cleaned_resumes)} resumes!")
print(f"💾 Saved to: {output_file}")
print(f"\n📊 Sample cleaned resume:")
if cleaned_resumes:
    sample = cleaned_resumes[0]
    print(f"  ID: {sample['ID']}")
    print(f"  Category: {sample['category']}")
    print(f"  Summary: {sample['summary'][:100]}...")
    print(f"  Work Experience: {sample['work_experience'][:100]}...")
    print(f"  Education: {sample['education'][:100]}...")
    print(f"  Skills: {sample['skills'][:100]}...")