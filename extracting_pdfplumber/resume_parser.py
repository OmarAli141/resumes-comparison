"""
Parse resume text and extract structured information.
Extracts: ID, title, summary/profile, work experience, education, skills
"""

import json
import re
from typing import Dict, Any, List


def extract_sections(text: str) -> Dict[str, str]:
    """Extract common resume sections with improved patterns."""
    sections = {
        "summary": "",
        "education": "",
        "work_experience": "",
        "skills": ""
    }
    
    text_lower = text.lower()
    
    # Extract summary/profile (usually at the beginning, before major sections)
    summary_patterns = [
        r"(?:summary|objective|profile|about|overview|professional summary)[\s:]*\n(.*?)(?=\n(?:education|experience|work|skills|employment|qualifications|projects|$))",
        r"^(.{0,800})(?=\n(?:education|experience|work|skills|employment|qualifications))",
        r"(?:summary|objective|profile)[\s\S]{0,1000}(?=\n(?:education|experience|work|skills))"
    ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            summary_text = match.group(1).strip()
            # Limit summary length
            if len(summary_text) > 1000:
                summary_text = summary_text[:1000] + "..."
            sections["summary"] = summary_text
            break
    
    # Extract education
    edu_patterns = [
        r"(?:education|academic|qualifications|educational background)[\s:]*\n(.*?)(?=\n(?:experience|work|skills|employment|projects|certifications|$))",
        r"(?:bachelor|master|phd|degree|diploma|certification|university|college|school)[\s\S]{0,1500}(?=\n(?:experience|work|skills|employment|projects|$))"
    ]
    
    for pattern in edu_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            edu_text = match.group(1).strip() if match.groups() else match.group(0).strip()
            # Limit education length
            if len(edu_text) > 2000:
                edu_text = edu_text[:2000] + "..."
            sections["education"] = edu_text
            break
    
    # Extract work experience
    exp_patterns = [
        r"(?:work experience|employment|professional experience|experience|work history|career history)[\s:]*\n(.*?)(?=\n(?:education|skills|projects|certifications|$))",
        r"(?:experience|work history|employment)[\s\S]{0,3000}(?=\n(?:education|skills|projects|certifications|$))"
    ]
    
    for pattern in exp_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            exp_text = match.group(1).strip() if match.groups() else match.group(0).strip()
            # Limit experience length but keep more than other sections
            if len(exp_text) > 5000:
                exp_text = exp_text[:5000] + "..."
            sections["work_experience"] = exp_text
            break
    
    # Extract skills
    skills_patterns = [
        r"(?:skills|technical skills|competencies|expertise|proficiencies|core competencies)[\s:]*\n(.*?)(?=\n(?:education|experience|projects|certifications|languages|$))",
        r"(?:proficient|skilled|expert|knowledge|experience with|familiar with)[\s\S]{0,2000}(?=\n(?:education|experience|projects|certifications|$))"
    ]
    
    for pattern in skills_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            skills_text = match.group(1).strip() if match.groups() else match.group(0).strip()
            # Limit skills length
            if len(skills_text) > 2000:
                skills_text = skills_text[:2000] + "..."
            sections["skills"] = skills_text
            break
    
    return sections


def extract_job_title(text: str) -> str:
    """Extract job title from resume text."""
    # Look for common patterns
    patterns = [
        r"(?:current|present|most recent|current position|present position)[\s]*(?:position|title|role|job)[\s:]*\n?([^\n]+)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:at|@|in|for)\s+",
        r"([A-Z][a-z]+\s+(?:Engineer|Developer|Analyst|Manager|Specialist|Consultant|Designer|Architect|Administrator|Coordinator|Director|Executive|Officer|Representative|Assistant))",
        r"job title[\s:]*\n?([^\n]+)",
        r"position[\s:]*\n?([^\n]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Clean up title
            title = re.sub(r'\s+', ' ', title)
            if len(title) > 100:
                title = title[:100]
            return title
    
    return ""


def parse_resume(text: str, resume_id: str = None, category: str = None) -> Dict[str, Any]:
    """
    Parse a resume text into structured format.
    
    Returns:
        Dictionary with fields: id, category, job_title, summary, education, work_experience, skills
    """
    sections = extract_sections(text)
    job_title = extract_job_title(text)
    
    # Clean up extracted text
    def clean_field(field_text: str) -> str:
        if not field_text:
            return ""
        # Remove excessive whitespace
        field_text = re.sub(r'\s+', ' ', field_text)
        # Remove leading/trailing whitespace
        return field_text.strip()
    
    resume_data = {
        "id": resume_id or "unknown",
        "category": category or "unknown",
        "job_title": clean_field(job_title),
        "summary": clean_field(sections["summary"]),
        "education": clean_field(sections["education"]),
        "work_experience": clean_field(sections["work_experience"]),
        "skills": clean_field(sections["skills"])
    }
    
    return resume_data